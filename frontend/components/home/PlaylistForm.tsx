"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import { analyzePlaylist, ApiRequestError } from "@/lib/api";
import { isLikelyValidPlaylistUrl } from "@/lib/validators";
import { usePlaylistStore } from "@/hooks/usePlaylistStore";

export function PlaylistForm() {
  const router = useRouter();
  const setPlaylist = usePlaylistStore((s) => s.setPlaylist);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [fieldError, setFieldError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFieldError(null);

    const trimmed = url.trim();
    if (!isLikelyValidPlaylistUrl(trimmed)) {
      setFieldError("Enter a valid YouTube playlist URL, e.g. https://www.youtube.com/playlist?list=...");
      return;
    }

    setLoading(true);
    try {
      const playlist = await analyzePlaylist(trimmed);
      setPlaylist(playlist);
      router.push("/playlist");
    } catch (err) {
      const message = err instanceof ApiRequestError ? err.message : "Something went wrong. Please try again.";
      setFieldError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto w-full max-w-2xl" noValidate>
      <div className="flex flex-col gap-3 sm:flex-row">
        <label htmlFor="playlist-url" className="sr-only">
          YouTube playlist URL
        </label>
        <input
          id="playlist-url"
          type="url"
          inputMode="url"
          autoComplete="off"
          placeholder="https://www.youtube.com/playlist?list=..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          aria-invalid={!!fieldError}
          aria-describedby={fieldError ? "playlist-url-error" : undefined}
          className="flex-1 rounded-lg border border-default bg-card px-4 py-3.5 text-base outline-none ring-brand-500 transition-shadow focus:ring-2"
        />
        <Button type="submit" size="lg" loading={loading} disabled={!url.trim()}>
          {loading ? "Analyzing..." : "Analyze Playlist"}
        </Button>
      </div>
      {fieldError && (
        <p id="playlist-url-error" role="alert" className="mt-2 text-sm text-red-500">
          {fieldError}
        </p>
      )}
      <p className="mt-3 text-xs text-muted">
        Only submit playlists you own or have explicit permission to download. See our{" "}
        <a href="/terms" className="underline underline-offset-2">
          Terms of Service
        </a>
        .
      </p>
    </form>
  );
}
