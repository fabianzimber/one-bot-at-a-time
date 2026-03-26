import { ChatContainer } from "@/components/chat/ChatContainer";

export default function Home() {
  return (
    <main className="flex min-h-screen w-full items-center justify-center bg-background px-4 py-6 sm:px-6">
      <ChatContainer />
    </main>
  );
}
