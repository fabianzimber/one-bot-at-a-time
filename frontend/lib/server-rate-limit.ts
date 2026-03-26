const buckets = new Map<string, number[]>()

export function allowRequest(key: string, limit = 12, windowSeconds = 60) {
  const now = Date.now()
  const windowStart = now - windowSeconds * 1000
  const requests = buckets.get(key) ?? []
  const active = requests.filter((timestamp) => timestamp > windowStart)

  if (active.length >= limit) {
    buckets.set(key, active)
    return { allowed: false, retryAfter: windowSeconds }
  }

  active.push(now)
  buckets.set(key, active)
  return { allowed: true, retryAfter: 0 }
}
