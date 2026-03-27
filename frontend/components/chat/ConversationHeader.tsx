import { memo } from "react";

type ConversationHeaderProps = {
  conversationId: string | null;
  isSubmitting: boolean;
};

export const ConversationHeader = memo(function ConversationHeader({
  conversationId,
  isSubmitting,
}: ConversationHeaderProps) {
  return (
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
              Use the same session to search documents, inspect seeded HR data, and follow service
              activity while the assistant streams.
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
  );
});
