import { ChatContainer } from "@/components/chat/ChatContainer";

export default function Home() {
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
        className="pointer-events-none absolute left-[8%] top-32 h-28 w-28 border border-brand-amber/35 animate-drift-line"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[12%] top-24 h-16 w-16 bg-brand-scarlet"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute bottom-28 right-[7%] h-32 w-32 rounded-full border border-brand-electric-indigo/30"
      />

      <section className="relative flex min-h-screen w-full items-stretch px-4 py-4 sm:px-6 lg:px-8">
        <ChatContainer />
      </section>
    </main>
  );
}
