import { checkBotId } from "botid/server";
import { NextResponse } from "next/server";

import {
  buildInternalHeaders,
  buildServiceUrl,
  getChatOrchestratorShareToken,
  getChatOrchestratorUrl,
  getForwardedFor,
} from "@/lib/backend";
import { allowRequest } from "@/lib/server-rate-limit";

export const runtime = "nodejs";

export async function POST(req: Request) {
  const { isBot } = await checkBotId();
  if (isBot) {
    return NextResponse.json(
      { error: "Bot detected — access denied" },
      { status: 403 },
    );
  }

  const clientIp = getForwardedFor(req);
  const rateLimit = allowRequest(`${clientIp}:stream`, 20, 60);
  if (!rateLimit.allowed) {
    return NextResponse.json(
      { error: `Rate limit exceeded. Retry in ${rateLimit.retryAfter}s.` },
      { status: 429 },
    );
  }

  const body = (await req.json()) as {
    message?: string;
    conversation_id?: string;
  };
  const message = body.message?.trim();
  if (!message) {
    return NextResponse.json(
      { error: "Missing message in request body" },
      { status: 400 },
    );
  }

  const backendHeaders = buildInternalHeaders(req);
  const streamUrl = buildServiceUrl(
    getChatOrchestratorUrl(),
    "/api/v1/chat/stream",
    getChatOrchestratorShareToken(),
  );
  streamUrl.searchParams.set("message", message);
  const conversationId = body.conversation_id?.trim();
  if (conversationId) {
    streamUrl.searchParams.set("conversation_id", conversationId);
  }

  try {
    const response = await fetch(streamUrl, {
      method: "GET",
      headers: backendHeaders,
      cache: "no-store",
    });

    if (!response.ok || !response.body) {
      return NextResponse.json(
        { error: "Streaming backend unavailable" },
        { status: response.status || 502 },
      );
    }

    return new Response(response.body, {
      status: response.status,
      headers: {
        "Cache-Control": "no-cache, no-transform",
        Connection: "keep-alive",
        "Content-Type": "text/event-stream",
      },
    });
  } catch {
    return NextResponse.json(
      { error: "Streaming backend unavailable" },
      { status: 502 },
    );
  }
}
