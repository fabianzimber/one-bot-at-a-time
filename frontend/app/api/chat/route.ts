import { checkBotId } from "botid/server";
import { NextResponse } from "next/server";

import { buildInternalHeaders, getChatOrchestratorUrl, getForwardedFor } from "@/lib/backend";
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
  const rateLimit = allowRequest(clientIp);
  if (!rateLimit.allowed) {
    return NextResponse.json(
      { error: `Rate limit exceeded. Retry in ${rateLimit.retryAfter}s.` },
      { status: 429 },
    );
  }

  const body = await req.json();
  const backendHeaders = buildInternalHeaders(req);
  backendHeaders.set("content-type", "application/json");

  try {
    const response = await fetch(`${getChatOrchestratorUrl()}/api/v1/chat`, {
      method: "POST",
      headers: backendHeaders,
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const payload = await response.json();
    if (!response.ok) {
      return NextResponse.json(payload, { status: response.status });
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { error: "Chat orchestrator unavailable" },
      { status: 502 },
    );
  }
}
