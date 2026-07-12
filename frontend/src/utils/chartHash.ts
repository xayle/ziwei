export async function buildChartHash(seed: string): Promise<string> {
  const data = new TextEncoder().encode(seed)
  const digest = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
    .slice(0, 24)
}
