type MessageBubbleProps = {
  role: "bot" | "user";
  content: string;
};

export function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={isUser ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          isUser
            ? "max-w-[80%] rounded-xl bg-brand-electric-indigo px-4 py-3 text-sm font-sans leading-6 text-brand-white"
            : "max-w-[80%] rounded-xl border border-brand-slate bg-brand-indigo-deep px-4 py-3 text-sm font-mono leading-6 text-brand-ghost"
        }
      >
        {content}
      </div>
    </div>
  );
}
