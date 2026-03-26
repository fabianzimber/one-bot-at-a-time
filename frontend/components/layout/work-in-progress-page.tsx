import type { LucideIcon } from "lucide-react";
import {
  ArrowUpRight,
  Bot,
  Clock3,
  DatabaseZap,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

type Track = {
  title: string;
  description: string;
  icon: LucideIcon;
  tone: string;
  iconTone: string;
};

type Milestone = {
  label: string;
  value: string;
  detail: string;
};

const tracks: Track[] = [
  {
    title: "Brand System",
    description:
      "Tailwind v4 theme tokens und shadcn/ui-Variablen sind direkt auf die one-bot-at-a-time Palette gemappt.",
    icon: Sparkles,
    tone: "from-brand-electric-indigo/22 via-brand-electric-indigo/8 to-transparent",
    iconTone: "text-brand-indigo-light",
  },
  {
    title: "Component Foundation",
    description:
      "Die UI-Basis fuer Badges, Cards, Buttons und Separatoren ist bereit fuer den naechsten Chat-Flow.",
    icon: Workflow,
    tone: "from-brand-teal/20 via-brand-teal/6 to-transparent",
    iconTone: "text-brand-teal-light",
  },
  {
    title: "Interface Direction",
    description:
      "Dark-mode-first, praezise Typografie und ruhige Bewegung als Grundlage fuer die spaetere RAG-Oberflaeche.",
    icon: ShieldCheck,
    tone: "from-brand-amber/20 via-brand-amber/6 to-transparent",
    iconTone: "text-brand-amber-light",
  },
];

const milestones: Milestone[] = [
  {
    label: "Foundation",
    value: "Live now",
    detail: "Next.js 16.2.1, App Router, Tailwind CSS v4 und shadcn/ui laufen gemeinsam.",
  },
  {
    label: "Next pass",
    value: "Chat canvas",
    detail: "Als Naechstes folgen Streaming UI, Tool-Zustaende und Dokumenten-Interaktion.",
  },
  {
    label: "Design rule",
    value: "Every pixel intentional",
    detail: "Die Oberflaeche bleibt reduziert, lesbar und streng an die Brandfarben gebunden.",
  },
];

export function WorkInProgressPage() {
  return (
    <main className="relative isolate min-h-screen overflow-hidden">
      <div
        aria-hidden="true"
        className="brand-grid pointer-events-none absolute inset-0 opacity-60"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-16 h-72 w-72 -translate-x-1/2 rounded-full bg-brand-electric-indigo/20 blur-3xl"
      />

      <div className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 py-6 sm:px-10 lg:px-12">
        <header className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="hero-orb flex size-11 items-center justify-center rounded-2xl bg-brand-electric-indigo/12 backdrop-blur-md">
              <Bot className="size-5 text-brand-indigo-light" />
            </div>
            <div>
              <p className="font-mono text-[0.68rem] uppercase tracking-[0.32em] text-brand-slate-light">
                one-bot-at-a-time
              </p>
              <p className="text-sm text-brand-ghost/72">
                Trenkwalder AI Assistant
              </p>
            </div>
          </div>

          <Badge
            variant="outline"
            className="border-brand-indigo-light/20 bg-brand-white/6 px-3 py-1 text-brand-ghost/82 backdrop-blur-md"
          >
            Work in Progress
          </Badge>
        </header>

        <section className="flex flex-1 items-center py-14 sm:py-20">
          <div className="grid w-full gap-8 lg:grid-cols-[1.1fr_0.78fr] lg:gap-10">
            <div className="flex flex-col justify-center">
              <Badge
                variant="secondary"
                className="mb-6 w-fit border border-brand-indigo-light/10 bg-brand-indigo-50/10 px-3 py-1 text-brand-indigo-light"
              >
                Next.js 16.2.1 / Tailwind / shadcn/ui
              </Badge>

              <div className="space-y-6">
                <p className="font-mono text-xs uppercase tracking-[0.32em] text-brand-slate-light/90">
                  Interface foundation
                </p>
                <h1 className="max-w-4xl text-balance font-heading text-5xl font-medium tracking-[-0.06em] text-brand-white sm:text-6xl lg:text-7xl">
                  A restrained surface for ambitious AI systems is taking shape.
                </h1>
                <p className="max-w-2xl text-pretty text-lg leading-8 text-brand-slate-light sm:text-xl">
                  Das Frontend ist jetzt hochwertig aufgesetzt und das
                  Brand-Design sitzt tief im System: Farben, Typografie,
                  Semantik und Komponenten greifen bereits ineinander.
                </p>
              </div>

              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href="#status"
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-full border border-transparent bg-brand-electric-indigo px-5 text-sm font-medium text-brand-white shadow-[0_12px_40px_rgba(99,102,241,0.35)] transition-all hover:bg-brand-indigo-light hover:shadow-[0_18px_46px_rgba(99,102,241,0.42)] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-brand-indigo-light/40"
                >
                  Build status
                  <ArrowUpRight className="size-4" />
                </a>
                <a
                  href="#foundation"
                  className="inline-flex h-11 items-center justify-center rounded-full border border-brand-silver/15 bg-brand-white/6 px-5 text-sm font-medium text-brand-ghost transition-all hover:bg-brand-white/10 focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-brand-indigo-light/30"
                >
                  Design foundation
                </a>
              </div>

              <div
                id="foundation"
                className="mt-10 grid gap-4 sm:grid-cols-3"
              >
                {tracks.map((track) => {
                  const Icon = track.icon;

                  return (
                    <Card
                      key={track.title}
                      className="brand-panel border border-brand-silver/10 bg-card/78 backdrop-blur-xl"
                    >
                      <CardHeader className="gap-4">
                        <div
                          className={cn(
                            "flex size-11 items-center justify-center rounded-2xl border border-brand-silver/10 bg-linear-to-br",
                            track.tone
                          )}
                        >
                          <Icon className={cn("size-5", track.iconTone)} />
                        </div>
                        <div className="space-y-1">
                          <CardTitle>{track.title}</CardTitle>
                          <CardDescription>{track.description}</CardDescription>
                        </div>
                      </CardHeader>
                    </Card>
                  );
                })}
              </div>
            </div>

            <Card
              id="status"
              className="brand-panel relative overflow-hidden border border-brand-indigo-light/14 bg-card/86 backdrop-blur-xl"
            >
              <div
                aria-hidden="true"
                className="animate-drift absolute -right-12 top-6 h-36 w-36 rounded-full bg-brand-electric-indigo/16 blur-3xl"
              />
              <CardHeader className="gap-4 pb-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <Badge className="mb-4 bg-brand-electric-indigo text-brand-white">
                      Phase 01
                    </Badge>
                    <CardTitle className="text-xl">
                      Frontend status snapshot
                    </CardTitle>
                    <CardDescription>
                      Die Plattform startet mit einer ruhigen, dunklen WIP-Seite
                      und einem belastbaren Designsystem darunter.
                    </CardDescription>
                  </div>
                  <div className="rounded-full border border-brand-silver/10 bg-brand-white/6 px-3 py-1 font-mono text-[0.7rem] uppercase tracking-[0.28em] text-brand-slate-light">
                    Active
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="relative overflow-hidden rounded-[calc(var(--radius-2xl))] border border-brand-indigo-light/12 bg-linear-to-br from-brand-electric-indigo/10 via-brand-midnight to-brand-midnight p-6">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(129,140,248,0.18),transparent_58%)]" />
                  <div className="relative h-48">
                    <div className="absolute left-1/2 top-1/2 size-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand-indigo-light/18" />
                    <div className="absolute left-1/2 top-1/2 size-56 -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand-silver/10" />
                    <div className="absolute left-[calc(50%-0.5rem)] top-[calc(50%-0.5rem)] animate-pulse-soft size-4 rounded-full bg-brand-electric-indigo hero-orb" />
                    <div className="animate-float-slow absolute left-[22%] top-[30%] size-2 rounded-full bg-brand-teal" />
                    <div className="absolute right-[22%] top-[36%] size-2 rounded-full bg-brand-amber" />
                    <div className="animate-float-slow absolute bottom-[28%] left-[26%] size-2 rounded-full bg-brand-scarlet [animation-delay:1.2s]" />
                    <div className="absolute bottom-[22%] right-[30%] size-2 rounded-full bg-brand-indigo-light" />

                    <div className="absolute left-0 top-0 rounded-full border border-brand-silver/10 bg-brand-white/6 px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
                      foundation
                    </div>
                    <div className="absolute bottom-0 right-0 rounded-full border border-brand-silver/10 bg-brand-white/6 px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
                      brand locked
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {milestones.map((milestone, index) => (
                    <div key={milestone.label} className="space-y-4">
                      <div className="flex items-start gap-4">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-2xl border border-brand-silver/10 bg-brand-white/6">
                          {index === 0 ? (
                            <Clock3 className="size-4 text-brand-indigo-light" />
                          ) : index === 1 ? (
                            <DatabaseZap className="size-4 text-brand-teal-light" />
                          ) : (
                            <ShieldCheck className="size-4 text-brand-amber-light" />
                          )}
                        </div>
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                            <p className="font-mono text-[0.7rem] uppercase tracking-[0.28em] text-brand-slate-light">
                              {milestone.label}
                            </p>
                            <p className="text-sm font-medium text-brand-white">
                              {milestone.value}
                            </p>
                          </div>
                          <p className="text-sm leading-6 text-brand-slate-light">
                            {milestone.detail}
                          </p>
                        </div>
                      </div>
                      {index < milestones.length - 1 ? (
                        <Separator className="bg-brand-silver/8" />
                      ) : null}
                    </div>
                  ))}
                </div>
              </CardContent>

              <CardFooter className="flex items-center justify-between gap-4 border-brand-silver/10 bg-brand-white/5">
                <p className="text-sm text-brand-slate-light">
                  Built with intention. One bot at a time.
                </p>
                <p className="font-mono text-[0.7rem] uppercase tracking-[0.28em] text-brand-slate-light">
                  Ready for chat UI
                </p>
              </CardFooter>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}
