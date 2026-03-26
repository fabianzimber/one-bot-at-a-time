export function getChatOrchestratorUrl() {
  return process.env.CHAT_ORCHESTRATOR_URL ?? "http://localhost:8001"
}

export function getChatOrchestratorShareToken() {
  return process.env.CHAT_ORCHESTRATOR_SHARE_TOKEN ?? ""
}

export function getRagServiceUrl() {
  return process.env.RAG_SERVICE_URL ?? "http://localhost:8002"
}

export function getRagServiceShareToken() {
  return process.env.RAG_SERVICE_SHARE_TOKEN ?? ""
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

export function buildServiceUrl(baseUrl: string, path: string, shareToken = "") {
  const url = new URL(path, `${baseUrl.replace(/\/$/, "")}/`)
  if (shareToken) {
    url.searchParams.set("_vercel_share", shareToken)
  }
  return url
}
