import Link from "next/link"

import {
  buildInternalServerHeaders,
  buildServiceUrl,
  getChatOrchestratorShareToken,
  getChatOrchestratorUrl,
} from "@/lib/backend"
import { demoPrompts } from "@/lib/demo-prompts"
import type { MockDataOverview } from "@/types"

export const dynamic = "force-dynamic"

function formatCurrency(value: number | null, currency: string) {
  if (value === null) {
    return "n/a"
  }

  return new Intl.NumberFormat("de-DE", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value)
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
  )

  if (!response.ok) {
    throw new Error("Mock data unavailable")
  }

  return (await response.json()) as MockDataOverview
}

export default async function MockDataPage() {
  let overview: MockDataOverview | null = null
  let loadError: string | null = null

  try {
    overview = await getMockDataOverview()
  } catch (error) {
    loadError = error instanceof Error ? error.message : "Mock data unavailable"
  }

  return (
    <main className="min-h-screen bg-background px-4 py-6 sm:px-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-4 border border-brand-slate bg-brand-midnight px-5 py-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="space-y-2">
            <p className="font-mono text-[0.68rem] uppercase tracking-[0.24em] text-brand-slate-light">
              Mock data
            </p>
            <h1 className="text-2xl font-medium tracking-[-0.04em] text-brand-white">
              Seeded HR snapshot
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-brand-slate-light">
              Diese Tabelle zeigt die fiktiven HR-Daten, die der Chatbot im selben Branch
              ueber seine HR-Tools abfragen kann.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {overview ? (
              <div className="rounded-full border border-brand-slate px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-slate-light">
                {overview.employee_count} employees / {overview.departments.length} departments
              </div>
            ) : null}
            <Link
              href="/"
              className="rounded-full border border-brand-electric-indigo px-3 py-1 font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-ghost transition-colors hover:bg-brand-electric-indigo hover:text-brand-white"
            >
              back to chat
            </Link>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.4fr_0.7fr]">
          <div className="overflow-hidden border border-brand-slate bg-brand-midnight">
            {loadError ? (
              <div className="px-5 py-6 text-sm text-brand-scarlet-light">{loadError}</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse text-left">
                  <thead className="border-b border-brand-slate bg-brand-midnight/95">
                    <tr className="font-mono text-[0.68rem] uppercase tracking-[0.18em] text-brand-slate-light">
                      <th className="px-4 py-3">Employee</th>
                      <th className="px-4 py-3">Department</th>
                      <th className="px-4 py-3">Position</th>
                      <th className="px-4 py-3">Manager</th>
                      <th className="px-4 py-3">Vacation</th>
                      <th className="px-4 py-3">Pay grade</th>
                      <th className="px-4 py-3">Gross annual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {overview?.rows.map((row) => (
                      <tr
                        key={row.employee_id}
                        className="border-b border-brand-slate/70 text-sm text-brand-ghost last:border-b-0"
                      >
                        <td className="px-4 py-3 align-top">
                          <div className="space-y-1">
                            <div className="font-medium text-brand-white">{row.name}</div>
                            <div className="font-mono text-[0.72rem] uppercase tracking-[0.16em] text-brand-slate-light">
                              {row.employee_id}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 align-top text-brand-slate-light">{row.department}</td>
                        <td className="px-4 py-3 align-top">{row.position}</td>
                        <td className="px-4 py-3 align-top text-brand-slate-light">{row.manager_name}</td>
                        <td className="px-4 py-3 align-top">
                          {row.remaining_vacation_days === null ? "n/a" : `${row.remaining_vacation_days} days`}
                        </td>
                        <td className="px-4 py-3 align-top">{row.pay_grade ?? "n/a"}</td>
                        <td className="px-4 py-3 align-top text-brand-slate-light">
                          {formatCurrency(row.gross_annual, row.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <aside className="flex flex-col gap-4 border border-brand-slate bg-brand-midnight px-5 py-5">
            <div className="space-y-2">
              <p className="font-mono text-[0.68rem] uppercase tracking-[0.22em] text-brand-slate-light">
                Suggested prompts
              </p>
              <p className="text-sm leading-6 text-brand-slate-light">
                Dieselben Fragen lassen sich direkt ueber den Chat testen. Der Demo-Button auf
                der Hauptseite setzt zufaellige Varianten davon ein.
              </p>
            </div>

            <div className="space-y-2">
              {demoPrompts.map((prompt) => (
                <div
                  key={prompt}
                  className="border border-brand-slate px-3 py-3 font-mono text-[0.78rem] leading-6 text-brand-ghost"
                >
                  {prompt}
                </div>
              ))}
            </div>
          </aside>
        </section>
      </div>
    </main>
  )
}
