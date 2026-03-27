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

async function readStreamErrorPayload(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json().catch(() => null)) as
    | { error?: string; detail?: string }
    | null;
}

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
  backendHeaders.set("content-type", "application/json");
  const streamUrl = buildServiceUrl(
    getChatOrchestratorUrl(),
    "/api/v1/chat/stream",
    getChatOrchestratorShareToken(),
  );
  const conversationId = body.conversation_id?.trim();

  try {
    const response = await fetch(streamUrl, {
      method: "POST",
      headers: backendHeaders,
      body: JSON.stringify({
        message,
        ...(conversationId ? { conversation_id: conversationId } : {}),
      }),
      cache: "no-store",
    });

    if (!response.ok || !response.body) {
      const payload = await readStreamErrorPayload(response);
      return NextResponse.json(
        { error: payload?.error ?? payload?.detail ?? "Streaming backend unavailable" },
        { status: response.status || 502 },
      );
    }

    const streamHeaders = new Headers(response.headers);
    streamHeaders.set("Cache-Control", "no-cache, no-transform");
    streamHeaders.set("Content-Type", response.headers.get("content-type") ?? "text/event-stream");
    streamHeaders.delete("content-length");

    return new Response(response.body, {
      status: response.status,
      headers: streamHeaders,
    });
  } catch {
    return NextResponse.json(
      { error: "Streaming backend unavailable" },
      { status: 502 },
    );
  }
}
