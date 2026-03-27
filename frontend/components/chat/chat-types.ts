export type ChatMessage = {
  id: string;
  role: "bot" | "user";
  content: string;
  pending?: boolean;
};
