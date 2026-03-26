import { checkBotId } from "botid/server";
import { NextResponse } from "next/server";

import {
  buildInternalHeaders,
  buildServiceUrl,
  getForwardedFor,
  getRagServiceShareToken,
  getRagServiceUrl,
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
  const rateLimit = allowRequest(`${clientIp}:documents`, 6, 60);
  if (!rateLimit.allowed) {
    return NextResponse.json(
      { error: `Rate limit exceeded. Retry in ${rateLimit.retryAfter}s.` },
      { status: 429 },
    );
  }

  const formData = await req.formData();
  const backendHeaders = buildInternalHeaders(req);

  try {
    const response = await fetch(
      buildServiceUrl(
        getRagServiceUrl(),
        "/api/v1/ingest",
        getRagServiceShareToken(),
      ),
      {
      method: "POST",
      headers: backendHeaders,
      body: formData,
      cache: "no-store",
      },
    );

    const payload = await response.json();
    if (!response.ok) {
      return NextResponse.json(payload, { status: response.status });
    }

    return NextResponse.json(payload);
  } catch {
    return NextResponse.json(
      { error: "Document ingestion unavailable" },
      { status: 502 },
    );
  }
}
