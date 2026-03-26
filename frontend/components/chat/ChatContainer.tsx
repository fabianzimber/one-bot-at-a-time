"use client";

import { useState } from "react";
import { InputBar } from "@/components/chat/InputBar";
import { MessageBubble } from "@/components/chat/MessageBubble";

type ChatMessage = {
  id: string;
  role: "bot" | "user";
  content: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: "bot-1",
    role: "bot",
    content:
      "Welcome. Ask me anything about your documents, workflows, or employee data.",
  },
  {
    id: "user-1",
    role: "user",
    content:
      "Summarize the latest uploaded company brief in five bullet points.",
  },
  {
    id: "bot-2",
    role: "bot",
    content:
      "I can do that. Upload a file or reference an existing one and I will generate a concise summary.",
  },
];

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);

  const handleSubmit = (message: string, file: File | null) => {
    const normalizedMessage = message.trim();

    if (!normalizedMessage && !file) {
      return;
    }

    const composedMessage = file
      ? `${normalizedMessage || "Uploaded file"} (${file.name})`
      : normalizedMessage;

    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: composedMessage,
      },
    ]);
  };

  return (
    <section className="flex h-[min(86vh,860px)] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-brand-slate bg-brand-midnight">
      <header className="border-b border-brand-slate px-4 py-3">
        <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
          one-bot-at-a-time
        </p>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-3">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
            />
          ))}
        </div>
      </div>

      <InputBar onSubmit={handleSubmit} />
    </section>
  );
}
