"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, Bot, DatabaseZap, ShieldCheck, Workflow } from "lucide-react";

import { InputBar } from "@/components/chat/InputBar";
import { MessageBubble } from "@/components/chat/MessageBubble";

type ChatMessage = {
  id: string;
  role: "bot" | "user";
  content: string;
  pending?: boolean;
};

type UploadResponse = {
  document_id: string;
  filename: string;
  chunks_created: number;
  message: string;
};

type StreamEvent =
  | { event: "start"; data: { conversation_id: string } }
  | { event: "content"; data: { delta: string } }
  | { event: "done"; data: { conversation_id: string } }
  | { event: "tool"; data: Record<string, unknown> }
  | { event: "error"; data: { detail?: string; error?: string } };

type WorkspaceTrack = {
  title: string;
  detail: string;
  icon: typeof DatabaseZap;
  accent: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: "bot-1",
    role: "bot",
    content: "Welcome. Ask me anything about your documents, workflows, or employee data.",
  },
];

const workspaceTracks: WorkspaceTrack[] = [
  {
    title: "Document search",
    detail: "Ground answers in uploaded knowledge with branch-safe retrieval.",
    icon: DatabaseZap,
    accent: "bg-brand-electric-indigo",
  },
  {
    title: "HR records",
    detail: "Inspect seeded employee data without leaving the conversation surface.",
    icon: ShieldCheck,
    accent: "bg-brand-teal",
  },
  {
    title: "Workflow handoff",
    detail: "Keep streaming, uploads, and service hops visible in one thread.",
    icon: Workflow,
    accent: "bg-brand-amber",
  },
];

function parseSseChunk(chunk: string) {
  const lines = chunk
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0);

  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  return {
    event: eventName,
    data: dataLines.join("\n"),
  };
}

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusText, setStatusText] = useState<string>("Ready");
  const abortControllerRef = useRef<AbortController | null>(null);

  const hasMessages = useMemo(() => messages.length > 0, [messages.length]);

  const closeStream = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  };

  const appendBotMessage = (content: string, pending = false) => {
    const id = `bot-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id,
        role: "bot",
        content,
        pending,
      },
    ]);
    return id;
  };

  const updateMessage = (id: string, updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((currentMessages) =>
      currentMessages.map((message) => (message.id === id ? updater(message) : message)),
    );
  };

  const uploadDocument = async (file: File) => {
    setStatusText(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/documents", {
      method: "POST",
      body: formData,
    });

    const payload = (await response.json()) as UploadResponse | { error?: string; detail?: string };
    if (!response.ok) {
      const detail =
        "error" in payload
          ? (payload.error ?? payload.detail)
          : "Document upload failed";
      throw new Error(detail ?? "Document upload failed");
    }

    const upload = payload as UploadResponse;
    appendBotMessage(`Indexed ${upload.filename} into ${upload.chunks_created} chunks.`);
    setStatusText(`Indexed ${upload.filename}`);
  };

  const streamResponse = async (message: string) => {
    setStatusText("Waiting for assistant...");
    const assistantMessageId = appendBotMessage("", true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: {
        "content-type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
      signal: abortController.signal,
    });

    if (!response.ok || !response.body) {
      const payload = (await response.json().catch(() => null)) as
        | { error?: string; detail?: string }
        | null;
      throw new Error(payload?.error ?? payload?.detail ?? "Streaming backend unavailable");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let streamFinished = false;

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });

        // Vercel/Fetch preserves CRLF in SSE streams, so normalize before
        // splitting events; otherwise the client can miss the final `done` event.
        const normalizedBuffer = buffer.replace(/\r\n/g, "\n");
        const chunks = normalizedBuffer.split("\n\n");
        buffer = chunks.pop() ?? "";

        for (const chunk of chunks) {
          const parsed = parseSseChunk(chunk);
          if (!parsed) {
            continue;
          }

          const event = {
            event: parsed.event,
            data: JSON.parse(parsed.data),
          } as StreamEvent;

          if (event.event === "start") {
            setConversationId(event.data.conversation_id);
            setStatusText("Streaming response...");
            continue;
          }

          if (event.event === "content") {
            updateMessage(assistantMessageId, (currentMessage) => ({
              ...currentMessage,
              content: currentMessage.content + event.data.delta,
            }));
            continue;
          }

          if (event.event === "done") {
            streamFinished = true;
            setConversationId(event.data.conversation_id);
            updateMessage(assistantMessageId, (currentMessage) => ({
              ...currentMessage,
              pending: false,
              content: currentMessage.content || "No response received.",
            }));
            setStatusText("Ready");
            return;
          }

          if (event.event === "error") {
            throw new Error(event.data.error ?? event.data.detail ?? "Streaming failed");
          }
        }
      }

      if (!streamFinished) {
        throw new Error("Streaming ended unexpectedly");
      }
    } catch (error) {
      updateMessage(assistantMessageId, (currentMessage) => ({
        ...currentMessage,
        pending: false,
        content: currentMessage.content || "The assistant is currently unavailable.",
      }));
      setStatusText("Assistant unavailable");
      throw error;
    } finally {
      closeStream();
    }
  };

  const handleSubmit = async (message: string, file: File | null) => {
    const normalizedMessage = message.trim();

    if (!normalizedMessage && !file) {
      return;
    }

    closeStream();
    setIsSubmitting(true);

    try {
      if (file) {
        setMessages((currentMessages) => [
          ...currentMessages,
          {
            id: `user-upload-${Date.now()}`,
            role: "user",
            content: `Uploaded file: ${file.name}`,
          },
        ]);
        await uploadDocument(file);
      }

      if (!normalizedMessage) {
        setStatusText("Ready");
        return;
      }

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `user-${Date.now()}`,
          role: "user",
          content: normalizedMessage,
        },
      ]);

      await streamResponse(normalizedMessage);
    } catch (error) {
      const messageText = error instanceof Error ? error.message : "Request failed";
      appendBotMessage(messageText);
      setStatusText("Request failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="brand-shell brand-top-rule relative flex min-h-[calc(100svh-2rem)] w-full overflow-hidden border border-brand-silver">
      <div
        aria-hidden="true"
        className="brand-grid-light pointer-events-none absolute inset-0 opacity-70"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[24%] top-0 h-full w-px bg-linear-to-b from-transparent via-brand-electric-indigo/18 to-transparent"
      />

      <div className="relative grid w-full lg:grid-cols-[minmax(18rem,24rem)_1fr]">
        <aside className="brand-panel flex flex-col justify-between border-b border-brand-silver px-5 py-5 sm:px-6 sm:py-6 lg:border-b-0 lg:border-r">
          <div className="space-y-8">
            <header className="animate-rise-in space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-3">
                  <p className="font-mono text-[0.68rem] uppercase tracking-[0.32em] text-brand-electric-indigo">
                    one-bot-at-a-time
                  </p>
                  <div>
                    <h1 className="max-w-[14rem] text-3xl font-medium tracking-[-0.08em] text-brand-midnight sm:text-[2.6rem]">
                      Trenkwalder assistant surface
                    </h1>
                    <p className="mt-3 max-w-xs text-sm leading-6 text-brand-slate">
                      Query documents, HR data, and workflows from one precise thread.
                    </p>
                  </div>
                </div>

                <div className="inline-flex size-11 items-center justify-center border border-brand-electric-indigo text-brand-electric-indigo">
                  <Bot className="size-5" />
                </div>
              </div>
            </header>

            <div className="relative overflow-hidden border border-brand-silver bg-brand-white">
              <div className="absolute inset-5 border border-brand-silver/60" />
              <div className="absolute left-1/2 top-1/2 size-48 -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand-electric-indigo/40" />
              <div className="absolute left-1/2 top-1/2 size-60 -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand-electric-indigo/18 animate-orbit-slow" />
              <div className="absolute left-1/2 top-1/2 flex size-40 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-brand-electric-indigo text-6xl font-medium text-brand-white">
                1
              </div>
              <div className="absolute left-[18%] top-[62%] size-4 rounded-full bg-brand-amber" />
              <div className="absolute right-[18%] top-[23%] size-6 rounded-full bg-brand-scarlet" />
              <div className="absolute left-1/2 top-1/2 h-40 w-40 -translate-x-1/2 -translate-y-1/2 border border-brand-electric-indigo/10" />
              <div className="relative flex min-h-64 items-end justify-between p-5">
                <div>
                  <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
                    brand axis
                  </p>
                  <p className="mt-2 text-sm text-brand-slate">
                    White canvas, hard edges, indigo signal.
                  </p>
                </div>
                <div className="border border-brand-silver px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.22em] text-brand-electric-indigo">
                  v1
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <p className="font-mono text-[0.68rem] uppercase tracking-[0.26em] text-brand-slate-light">
                Active surfaces
              </p>
              <div className="border-y border-brand-silver">
                {workspaceTracks.map((track) => {
                  const Icon = track.icon;

                  return (
                    <div
                      key={track.title}
                      className="grid grid-cols-[auto_1fr] gap-3 border-b border-brand-silver/80 px-0 py-4 last:border-b-0"
                    >
                      <div className="mt-1 flex items-center gap-2">
                        <span className={`block h-8 w-1 ${track.accent}`} />
                        <Icon className="size-4 text-brand-midnight" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-brand-midnight">{track.title}</p>
                        <p className="mt-1 text-sm leading-6 text-brand-slate">{track.detail}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="mt-8 flex items-end justify-between gap-4 border-t border-brand-silver pt-4">
            <Link
              href="/mock-data"
              className="inline-flex items-center gap-2 border border-brand-midnight px-3 py-2 font-mono text-[0.68rem] uppercase tracking-[0.22em] text-brand-midnight transition-colors hover:border-brand-electric-indigo hover:bg-brand-electric-indigo hover:text-brand-white"
            >
              mock data
              <ArrowUpRight className="size-3.5" />
            </Link>

            <div className="text-right">
              <p className="font-mono text-[0.68rem] uppercase tracking-[0.22em] text-brand-slate-light">
                runtime
              </p>
              <p className="mt-1 text-sm text-brand-slate">{statusText}</p>
            </div>
          </div>
        </aside>

        <div className="relative flex min-h-0 flex-col">
          <header className="brand-panel border-b border-brand-silver px-5 py-5 sm:px-6">
            <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
              <div className="space-y-2">
                <p className="font-mono text-[0.68rem] uppercase tracking-[0.28em] text-brand-electric-indigo">
                  conversation surface
                </p>
                <div>
                  <h2 className="text-3xl font-medium tracking-[-0.08em] text-brand-midnight sm:text-4xl">
                    Ask, upload, inspect.
                  </h2>
                  <p className="mt-3 max-w-2xl text-sm leading-6 text-brand-slate">
                    Use the same session to search documents, inspect seeded HR data, and follow
                    service activity while the assistant streams.
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="border border-brand-silver bg-brand-ghost/70 px-4 py-3">
                  <p className="font-mono text-[0.64rem] uppercase tracking-[0.24em] text-brand-slate-light">
                    session
                  </p>
                  <p className="mt-2 text-sm font-medium text-brand-midnight">
                    {conversationId ? conversationId.slice(0, 8) : "not started"}
                  </p>
                </div>
                <div className="border border-brand-silver bg-brand-ghost/70 px-4 py-3">
                  <p className="font-mono text-[0.64rem] uppercase tracking-[0.24em] text-brand-slate-light">
                    transport
                  </p>
                  <p className="mt-2 text-sm font-medium text-brand-midnight">
                    {isSubmitting ? "streaming" : "ready"}
                  </p>
                </div>
              </div>
            </div>
          </header>

          <div className="relative min-h-0 flex-1 overflow-hidden">
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-y-0 left-8 hidden w-px bg-linear-to-b from-transparent via-brand-electric-indigo/28 to-transparent lg:block"
            />
            <div
              aria-hidden="true"
              className="pointer-events-none absolute right-12 top-10 hidden h-24 w-24 border border-brand-teal/30 animate-drift-line lg:block"
            />

            <div className="flex h-full overflow-y-auto px-5 py-6 sm:px-6">
              <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
                {hasMessages
                  ? messages.map((message) => (
                      <MessageBubble
                        key={message.id}
                        role={message.role}
                        content={message.content}
                        pending={message.pending}
                      />
                    ))
                  : null}
              </div>
            </div>
          </div>

          <InputBar onSubmit={handleSubmit} disabled={isSubmitting} />
        </div>
      </div>
    </section>
  );
}
