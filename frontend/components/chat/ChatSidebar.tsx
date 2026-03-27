import Link from "next/link";
import { ArrowUpRight, Bot, DatabaseZap, ShieldCheck, Workflow } from "lucide-react";
import { memo } from "react";

type WorkspaceTrack = {
  title: string;
  detail: string;
  icon: typeof DatabaseZap;
  accent: string;
};

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

type ChatSidebarProps = {
  statusText: string;
};

export const ChatSidebar = memo(function ChatSidebar({ statusText }: ChatSidebarProps) {
  return (
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
  );
});
