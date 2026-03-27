import { memo } from "react";

import { MessageBubble } from "@/components/chat/MessageBubble";
import type { ChatMessage } from "@/components/chat/chat-types";

type ChatMessageListProps = {
  messages: ChatMessage[];
};

export const ChatMessageList = memo(function ChatMessageList({
  messages,
}: ChatMessageListProps) {
  return (
    <div className="relative min-h-0 flex-1 overflow-hidden">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 left-8 hidden w-px bg-linear-to-b from-transparent via-brand-electric-indigo/28 to-transparent lg:block"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-12 top-10 hidden h-24 w-24 border border-brand-teal/30 animate-drift-line lg:block"
      />

      <div className="flex h-full max-h-[calc(100svh-18rem)] overflow-y-auto px-5 py-6 sm:px-6">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-5">
          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              pending={message.pending}
            />
          ))}
        </div>
      </div>
    </div>
  );
});
