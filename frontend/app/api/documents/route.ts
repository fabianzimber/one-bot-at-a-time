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

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB
const ALLOWED_EXTENSIONS = new Set([".pdf", ".txt", ".md", ".docx"]);

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
  const file = formData.get("file");
  if (!file || !(file instanceof File)) {
    return NextResponse.json(
      { error: "No file provided" },
      { status: 400 },
    );
  }

  if (file.size > MAX_FILE_SIZE) {
    return NextResponse.json(
      { error: "File too large (max 10 MB)" },
      { status: 413 },
    );
  }

  const extension = file.name.includes(".")
    ? `.${file.name.split(".").pop()?.toLowerCase()}`
    : "";
  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return NextResponse.json(
      { error: "Unsupported file type" },
      { status: 400 },
    );
  }

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
