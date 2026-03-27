import { memo } from "react";
import { Bot, UserRound } from "lucide-react";

import { cn } from "@/lib/utils";

type MessageBubbleProps = {
  role: "bot" | "user";
  content: string;
  pending?: boolean;
};

export const MessageBubble = memo(function MessageBubble({
  role,
  content,
  pending = false,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={cn(
          "max-w-[min(44rem,88%)] border px-4 py-4 sm:px-5",
          isUser
            ? "border-brand-electric-indigo bg-brand-electric-indigo text-brand-white"
            : "brand-panel border-brand-silver text-brand-midnight",
        )}
      >
        <div
          className={cn(
            "mb-3 flex items-center gap-2 font-mono text-[0.64rem] uppercase tracking-[0.24em]",
            isUser ? "text-brand-indigo-100" : "text-brand-slate",
          )}
        >
          <span
            className={cn(
              "inline-flex size-6 items-center justify-center border",
              isUser
                ? "border-brand-indigo-light/35 bg-brand-indigo-deep/20 text-brand-white"
                : "border-brand-silver text-brand-electric-indigo",
            )}
          >
            {isUser ? <UserRound className="size-3.5" /> : <Bot className="size-3.5" />}
          </span>
          {isUser ? "Operator" : pending ? "Assistant / streaming" : "Assistant"}
        </div>

        <p
          className={cn(
            "whitespace-pre-wrap text-sm leading-7",
            isUser ? "font-medium text-brand-white" : "font-mono text-brand-midnight",
          )}
        >
          {content}
          {pending ? (
            <span className="ml-1 inline-block animate-pulse text-brand-scarlet">▍</span>
          ) : null}
        </p>
      </div>
    </div>
  );
});
