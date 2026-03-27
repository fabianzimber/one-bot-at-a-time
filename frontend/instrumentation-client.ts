import { initBotId } from "botid/client/core";

initBotId({
  protect: [
    { path: "/api/chat", method: "POST" },
    { path: "/api/chat/stream", method: "POST" },
    { path: "/api/documents", method: "POST" },
  ],
});
