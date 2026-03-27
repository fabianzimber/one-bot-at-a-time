import Link from "next/link";
import { ArrowUpRight, DatabaseZap, ShieldCheck, Users } from "lucide-react";

import {
  buildInternalServerHeaders,
  buildServiceUrl,
  getChatOrchestratorShareToken,
  getChatOrchestratorUrl,
} from "@/lib/backend";
import { demoPrompts } from "@/lib/demo-prompts";
import type { MockDataOverview } from "@/types";

export const dynamic = "force-dynamic";

function formatCurrency(value: number | null, currency: string) {
  if (value === null) {
    return "n/a";
  }

  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

async function getMockDataOverview(): Promise<MockDataOverview> {
  const response = await fetch(
    buildServiceUrl(
      getChatOrchestratorUrl(),
      "/api/v1/mock-data/hr-overview",
      getChatOrchestratorShareToken(),
    ),
    {
      headers: buildInternalServerHeaders("mock-data-page"),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error("Mock data unavailable");
  }

  return (await response.json()) as MockDataOverview;
}

export default async function MockDataPage() {
  let overview: MockDataOverview | null = null;
  let loadError: string | null = null;

  try {
    overview = await getMockDataOverview();
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Mock data unavailable";
  }

  return (
    <main className="relative isolate min-h-screen overflow-hidden bg-background">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-4 bg-brand-electric-indigo"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 bottom-0 h-4 bg-brand-electric-indigo"
      />
      <div
        aria-hidden="true"
        className="brand-grid-light pointer-events-none absolute inset-0 opacity-90"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-[10%] top-24 h-20 w-20 border border-brand-amber/35"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[8%] top-32 h-28 w-28 rounded-full border border-brand-electric-indigo/30"
      />

      <div className="relative mx-auto flex min-h-screen w-full max-w-[92rem] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="brand-shell brand-top-rule border border-brand-silver px-5 py-5 sm:px-6">
          <div className="flex flex-col gap-5 xl:flex-row xl:items-end xl:justify-between">
            <div className="space-y-3">
              <p className="font-mono text-[0.68rem] uppercase tracking-[0.32em] text-brand-electric-indigo">
                mock data
              </p>
              <div>
                <h1 className="text-3xl font-medium tracking-[-0.08em] text-brand-midnight sm:text-5xl">
                  Seeded HR snapshot
                </h1>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-brand-slate">
                  Diese Ansicht zeigt die fiktiven HR-Daten, die der Assistent im selben Branch
                  via internen Tools abfragt.
                </p>
              </div>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              {overview ? (
                <div className="border border-brand-silver bg-brand-white px-4 py-3">
                  <p className="font-mono text-[0.64rem] uppercase tracking-[0.24em] text-brand-slate-light">
                    dataset
                  </p>
                  <p className="mt-2 text-sm font-medium text-brand-midnight">
                    {overview.employee_count} employees / {overview.departments.length} departments
                  </p>
                </div>
              ) : null}

              <Link
                href="/"
                className="inline-flex items-center gap-2 border border-brand-midnight bg-brand-white px-4 py-3 font-mono text-[0.68rem] uppercase tracking-[0.22em] text-brand-midnight transition-colors hover:border-brand-electric-indigo hover:bg-brand-electric-indigo hover:text-brand-white"
              >
                back to chat
                <ArrowUpRight className="size-3.5" />
              </Link>
            </div>
          </div>
        </header>

        <section className="grid gap-6 xl:grid-cols-[1.45fr_0.72fr]">
          <div className="brand-shell border border-brand-silver">
            <div className="flex items-center justify-between gap-4 border-b border-brand-silver px-5 py-4 sm:px-6">
              <div>
                <p className="font-mono text-[0.64rem] uppercase tracking-[0.24em] text-brand-slate-light">
                  employee register
                </p>
                <p className="mt-2 text-sm text-brand-slate">
                  Persisted preview data exposed through the HR service.
                </p>
              </div>
              <DatabaseZap className="size-5 text-brand-electric-indigo" />
            </div>

            {loadError ? (
              <div className="px-5 py-6 text-sm text-brand-scarlet sm:px-6">{loadError}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse text-left">
                  <thead className="border-b border-brand-silver bg-brand-ghost/85">
                    <tr className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-slate-light">
                      <th className="px-4 py-3 sm:px-6">Employee</th>
                      <th className="px-4 py-3">Department</th>
                      <th className="px-4 py-3">Position</th>
                      <th className="px-4 py-3">Manager</th>
                      <th className="px-4 py-3">Vacation</th>
                      <th className="px-4 py-3">Pay grade</th>
                      <th className="px-4 py-3 sm:px-6">Gross annual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview?.rows.map((row) => (
                      <tr
                        key={row.employee_id}
                        className="border-b border-brand-silver/80 text-sm text-brand-midnight last:border-b-0"
                      >
                        <td className="px-4 py-4 align-top sm:px-6">
                          <div className="space-y-1">
                            <div className="font-medium text-brand-midnight">{row.name}</div>
                            <div className="font-mono text-[0.72rem] uppercase tracking-[0.16em] text-brand-slate-light">
                              {row.employee_id}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-4 align-top text-brand-slate">{row.department}</td>
                        <td className="px-4 py-4 align-top">{row.position}</td>
                        <td className="px-4 py-4 align-top text-brand-slate">{row.manager_name}</td>
                        <td className="px-4 py-4 align-top">
                          {row.remaining_vacation_days === null ? "n/a" : `${row.remaining_vacation_days} days`}
                        </td>
                        <td className="px-4 py-4 align-top">{row.pay_grade ?? "n/a"}</td>
                        <td className="px-4 py-4 align-top text-brand-slate sm:px-6">
                          {formatCurrency(row.gross_annual, row.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <aside className="flex flex-col gap-6">
            <section className="brand-shell border border-brand-silver px-5 py-5 sm:px-6">
              <div className="space-y-4">
                <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
                  service notes
                </p>
                <div className="border-y border-brand-silver">
                  <div className="grid grid-cols-[auto_1fr] gap-3 border-b border-brand-silver/80 py-4">
                    <Users className="mt-1 size-4 text-brand-electric-indigo" />
                    <div>
                      <p className="text-sm font-medium text-brand-midnight">Employees</p>
                      <p className="mt-1 text-sm leading-6 text-brand-slate">
                        Seed data is persisted after first boot and then served from the database.
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-[auto_1fr] gap-3 border-b border-brand-silver/80 py-4">
                    <ShieldCheck className="mt-1 size-4 text-brand-teal" />
                    <div>
                      <p className="text-sm font-medium text-brand-midnight">Branch safe</p>
                      <p className="mt-1 text-sm leading-6 text-brand-slate">
                        The chat assistant hits this service through the orchestrator with internal auth.
                      </p>
                    </div>
                  </div>
                  <div className="grid grid-cols-[auto_1fr] gap-3 py-4">
                    <DatabaseZap className="mt-1 size-4 text-brand-amber" />
                    <div>
                      <p className="text-sm font-medium text-brand-midnight">Verification</p>
                      <p className="mt-1 text-sm leading-6 text-brand-slate">
                        Use these rows to verify salary, manager, and vacation answers in the chat.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section className="brand-shell border border-brand-silver px-5 py-5 sm:px-6">
              <div className="space-y-4">
                <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
                  suggested prompts
                </p>
                <p className="text-sm leading-6 text-brand-slate">
                  Dieselben Fragen lassen sich direkt im Chat testen. Der Demo-Button auf der
                  Hauptseite setzt zufaellige Varianten davon ein.
                </p>
                <div className="space-y-2">
                  {demoPrompts.map((prompt) => (
                    <div
                      key={prompt}
                      className="border border-brand-silver bg-brand-white px-4 py-3 font-mono text-[0.78rem] leading-6 text-brand-midnight"
                    >
                      {prompt}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </aside>
        </section>
      </div>
    </main>
  );
}
