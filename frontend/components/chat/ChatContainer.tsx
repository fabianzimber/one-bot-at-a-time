"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";

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

const initialMessages: ChatMessage[] = [
  {
    id: "bot-1",
    role: "bot",
    content: "Welcome. Ask me anything about your documents, workflows, or employee data.",
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
    <section className="flex h-[min(86vh,860px)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-brand-slate bg-brand-midnight">
      <header className="flex items-center justify-between border-b border-brand-slate px-4 py-3">
        <div>
          <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
            one-bot-at-a-time
          </p>
          <p className="mt-1 text-xs text-brand-slate-light">{statusText}</p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/mock-data"
            className="hidden rounded-full border border-brand-slate px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-slate-light transition-colors hover:border-brand-electric-indigo hover:text-brand-ghost sm:inline-flex"
          >
            mock data
          </Link>
          {conversationId ? (
            <p className="hidden font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-slate-light sm:block">
              session {conversationId.slice(0, 8)}
            </p>
          ) : null}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-3">
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

      <InputBar onSubmit={handleSubmit} disabled={isSubmitting} />
    </section>
  );
}
