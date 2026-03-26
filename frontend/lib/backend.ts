export function getChatOrchestratorUrl() {
  return process.env.CHAT_ORCHESTRATOR_URL ?? "http://localhost:8001"
}

export function getInternalApiKey() {
  return process.env.INTERNAL_API_KEY ?? ""
}

export function getForwardedFor(request: Request) {
  return request.headers.get("x-forwarded-for") ?? "unknown"
}

export function buildInternalHeaders(request: Request) {
  const headers = new Headers()
  const internalApiKey = getInternalApiKey()
  if (internalApiKey) {
    headers.set("x-internal-api-key", internalApiKey)
  }

  headers.set("x-forwarded-for", getForwardedFor(request))
  headers.set("x-request-id", crypto.randomUUID())
  return headers
}
