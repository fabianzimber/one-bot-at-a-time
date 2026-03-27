const buckets = new Map<string, number[]>()
const MAX_BUCKETS = 10_000

function pruneStale(windowStart: number) {
  if (buckets.size <= MAX_BUCKETS) {
    return
  }
  for (const [key, timestamps] of buckets) {
    if (timestamps.every((ts) => ts <= windowStart)) {
      buckets.delete(key)
    }
    if (buckets.size <= MAX_BUCKETS) {
      break
    }
  }
}

export function allowRequest(key: string, limit = 12, windowSeconds = 60) {
  const now = Date.now()
  const windowStart = now - windowSeconds * 1000
  const requests = buckets.get(key) ?? []
  const active = requests.filter((timestamp) => timestamp > windowStart)

  if (active.length === 0) {
    buckets.delete(key)
  } else {
    buckets.set(key, active)
  }

  pruneStale(windowStart)

  if (active.length >= limit) {
    buckets.set(key, active)
    return { allowed: false, retryAfter: windowSeconds }
  }

  active.push(now)
  buckets.set(key, active)
  return { allowed: true, retryAfter: 0 }
}
