const ALLOWED_HOSTS = new Set(["www.youtube.com", "youtube.com", "m.youtube.com", "music.youtube.com"]);

/** Client-side pre-check only — a UX convenience so users get instant
 * feedback before the request round-trip. The backend re-validates
 * everything (host allow-list, SSRF checks) independently and is the only
 * validation that's actually trusted. */
export function isLikelyValidPlaylistUrl(raw: string): boolean {
  if (!raw || raw.trim().length === 0) return false;
  try {
    const url = new URL(raw.trim());
    if (!ALLOWED_HOSTS.has(url.hostname.toLowerCase())) return false;
    return url.searchParams.has("list");
  } catch {
    return false;
  }
}
