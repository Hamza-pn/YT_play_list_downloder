"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { usePlaylistStore } from "@/hooks/usePlaylistStore";
import { VideoList } from "@/components/playlist/VideoList";
import { FormatSelector } from "@/components/playlist/FormatSelector";
import { Button } from "@/components/ui/Button";
import { AdSlot } from "@/components/ui/AdSlot";
import { createDownloadJob, ApiRequestError } from "@/lib/api";

export default function PlaylistPage() {
  const router = useRouter();
  const playlist = usePlaylistStore((s) => s.playlist);
  const selectedIds = usePlaylistStore((s) => s.selectedIds);
  const audioFormat = usePlaylistStore((s) => s.audioFormat);
  const qualityKbps = usePlaylistStore((s) => s.qualityKbps);
  const setActiveJobId = usePlaylistStore((s) => s.setActiveJobId);
  const [starting, setStarting] = useState(false);

  if (!playlist) {
    return (
      <div className="mx-auto max-w-lg px-4 py-24 text-center">
        <h1 className="text-xl font-semibold">No playlist loaded</h1>
        <p className="mt-2 text-sm text-muted">Analyze a playlist first to select videos to convert.</p>
        <Link href="/" className="mt-6 inline-block">
          <Button>Go to homepage</Button>
        </Link>
      </div>
    );
  }

  async function handleStartConversion() {
    if (!playlist) return;
    if (selectedIds.size === 0) {
      toast.error("Select at least one video to convert.");
      return;
    }
    setStarting(true);
    try {
      const { job_id } = await createDownloadJob({
        playlistUrl: playlist.source_url,
        videoIds: Array.from(selectedIds),
        audioFormat,
        qualityKbps: audioFormat === "mp3" ? qualityKbps : null,
      });
      setActiveJobId(job_id);
      router.push(`/download/${job_id}`);
    } catch (err) {
      const message = err instanceof ApiRequestError ? err.message : "Could not start conversion.";
      toast.error(message);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative h-28 w-48 shrink-0 overflow-hidden rounded-lg bg-subtle">
          {playlist.thumbnail_url ? (
            <Image src={playlist.thumbnail_url} alt="" fill className="object-cover" unoptimized />
          ) : null}
        </div>
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-bold">{playlist.title}</h1>
          <p className="mt-1 text-sm text-muted">{playlist.channel_name ?? "Unknown channel"}</p>
          <p className="mt-1 text-sm text-muted">{playlist.video_count} videos available</p>
        </div>
      </div>

      <AdSlot slot="playlist-results" className="my-8" />

      <div className="rounded-xl border border-default bg-card p-5">
        <VideoList />
      </div>

      <div className="mt-6 rounded-xl border border-default bg-card p-5">
        <FormatSelector />
      </div>

      <div className="sticky bottom-4 mt-6 flex items-center justify-between rounded-xl border border-default bg-card p-4 shadow-lg">
        <p className="text-sm">
          <span className="font-semibold">{selectedIds.size}</span> video{selectedIds.size === 1 ? "" : "s"} selected
        </p>
        <Button size="lg" loading={starting} disabled={selectedIds.size === 0} onClick={handleStartConversion}>
          Start Conversion
        </Button>
      </div>
    </div>
  );
}
