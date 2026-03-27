"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ChatMessageList } from "@/components/chat/ChatMessageList";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { ConversationHeader } from "@/components/chat/ConversationHeader";
import { InputBar } from "@/components/chat/InputBar";
import type { ChatMessage } from "@/components/chat/chat-types";

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
  const pendingStreamDeltaRef = useRef("");
  const pendingMessageIdRef = useRef<string | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const closeStream = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
  }, []);

  const appendBotMessage = useCallback((content: string, pending = false) => {
    const id = `bot-${crypto.randomUUID()}`;
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
  }, []);

  const updateMessage = useCallback((id: string, updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((currentMessages) =>
      currentMessages.map((message) => (message.id === id ? updater(message) : message)),
    );
  }, []);

  const flushPendingStreamDelta = useCallback(() => {
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    const delta = pendingStreamDeltaRef.current;
    const messageId = pendingMessageIdRef.current;
    if (!delta || !messageId) {
      return;
    }

    pendingStreamDeltaRef.current = "";
    updateMessage(messageId, (currentMessage) => ({
      ...currentMessage,
      content: currentMessage.content + delta,
    }));
  }, [updateMessage]);

  const schedulePendingStreamDeltaFlush = useCallback(() => {
    if (animationFrameRef.current !== null) {
      return;
    }

    animationFrameRef.current = requestAnimationFrame(() => {
      animationFrameRef.current = null;
      flushPendingStreamDelta();
    });
  }, [flushPendingStreamDelta]);

  const resetPendingStreamState = useCallback(() => {
    pendingStreamDeltaRef.current = "";
    pendingMessageIdRef.current = null;
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  const uploadDocument = useCallback(async (file: File) => {
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
  }, [appendBotMessage]);

  const streamResponse = useCallback(async (message: string) => {
    setStatusText("Waiting for assistant...");
    const assistantMessageId = appendBotMessage("", true);
    pendingMessageIdRef.current = assistantMessageId;
    pendingStreamDeltaRef.current = "";

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
            pendingStreamDeltaRef.current += event.data.delta;
            schedulePendingStreamDeltaFlush();
            continue;
          }

          if (event.event === "done") {
            flushPendingStreamDelta();
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
        flushPendingStreamDelta();
        throw new Error("Streaming ended unexpectedly");
      }
    } catch (error) {
      flushPendingStreamDelta();
      updateMessage(assistantMessageId, (currentMessage) => ({
        ...currentMessage,
        pending: false,
        content: currentMessage.content || "The assistant is currently unavailable.",
      }));
      setStatusText("Assistant unavailable");
      throw error;
    } finally {
      resetPendingStreamState();
      closeStream();
    }
  }, [
    appendBotMessage,
    closeStream,
    conversationId,
    flushPendingStreamDelta,
    resetPendingStreamState,
    schedulePendingStreamDeltaFlush,
    updateMessage,
  ]);

  const handleSubmit = useCallback(async (message: string, file: File | null) => {
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
            id: `user-upload-${crypto.randomUUID()}`,
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
          id: `user-${crypto.randomUUID()}`,
          role: "user",
          content: normalizedMessage,
        },
      ]);

      await streamResponse(normalizedMessage);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      const messageText = error instanceof Error ? error.message : "Request failed";
      appendBotMessage(messageText);
      setStatusText("Request failed");
    } finally {
      setIsSubmitting(false);
    }
  }, [appendBotMessage, closeStream, streamResponse, uploadDocument]);

  useEffect(() => {
    return () => {
      resetPendingStreamState();
      closeStream();
    };
  }, [closeStream, resetPendingStreamState]);

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
        <ChatSidebar statusText={statusText} />

        <div className="relative flex min-h-0 flex-col">
          <ConversationHeader conversationId={conversationId} isSubmitting={isSubmitting} />
          <ChatMessageList messages={messages} />

          <InputBar onSubmit={handleSubmit} disabled={isSubmitting} />
        </div>
      </div>
    </section>
  );
}
