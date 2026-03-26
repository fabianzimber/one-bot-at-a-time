import { checkBotId } from "botid/server";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const { isBot } = await checkBotId();

  if (isBot) {
    return NextResponse.json(
      { error: "Bot detected — access denied" },
      { status: 403 },
    );
  }

  const body = await req.json();

  return NextResponse.json({
    message: "Request accepted",
    received: body,
  });
}
