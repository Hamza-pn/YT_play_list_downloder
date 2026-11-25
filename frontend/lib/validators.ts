const ALLOWED_HOSTS = new Set([
  "www.youtube.com",
  "youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtu.be",
  "www.youtu.be",
]);

const SHORT_LINK_HOSTS = new Set(["youtu.be", "www.youtu.be"]);

/** Path prefixes that carry a bare video id in the next segment:
 * /shorts/<id>, /live/<id>, /embed/<id>, /v/<id> */
const VIDEO_PATH_PREFIXES = new Set(["shorts", "live", "embed", "v"]);

const VIDEO_ID_RE = /^[A-Za-z0-9_-]{10,12}$/;

function extractVideoId(url: URL): string | null {
  const v = url.searchParams.get("v");
  if (v && VIDEO_ID_RE.test(v)) return v;

  const segments = url.pathname.split("/").filter(Boolean);
  const host = url.hostname.toLowerCase();

  const first = segments[0];
  if (SHORT_LINK_HOSTS.has(host)) {
    // youtu.be/<id> — the id is the whole path, no prefix.
    return first && VIDEO_ID_RE.test(first) ? first : null;
  }

  const second = segments[1];
  if (first && second && VIDEO_PATH_PREFIXES.has(first.toLowerCase())) {
    return VIDEO_ID_RE.test(second) ? second : null;
  }

  return null;
}

/** Client-side pre-check only — a UX convenience so users get instant
 * feedback before the request round-trip. The backend re-validates
 * everything (host allow-list, SSRF checks) independently and is the only
 * validation that's actually trusted.
 *
 * Accepts both supported source kinds: a playlist (`list=`) or a single
 * video — a normal watch URL, a Short, a live replay, or a youtu.be link. */
export function isLikelyValidSourceUrl(raw: string): boolean {
  if (!raw || raw.trim().length === 0) return false;
  try {
    const url = new URL(raw.trim());
    if (url.protocol !== "http:" && url.protocol !== "https:") return false;
    if (!ALLOWED_HOSTS.has(url.hostname.toLowerCase())) return false;
    return url.searchParams.has("list") || extractVideoId(url) !== null;
  } catch {
    return false;
  }
}

/** True when the URL points at one video rather than a playlist — used
 * only to word the UI (e.g. "1 video" vs a playlist listing). Mirrors the
 * backend rule that a `list=` param wins over a video id. */
export function isSingleVideoUrl(raw: string): boolean {
  if (!raw || raw.trim().length === 0) return false;
  try {
    const url = new URL(raw.trim());
    if (!ALLOWED_HOSTS.has(url.hostname.toLowerCase())) return false;
    if (url.searchParams.has("list")) return false;
    return extractVideoId(url) !== null;
  } catch {
    return false;
  }
}

/** @deprecated Use isLikelyValidSourceUrl — kept so older imports keep
 * working. Now also accepts single videos and Shorts. */
export const isLikelyValidPlaylistUrl = isLikelyValidSourceUrl;
