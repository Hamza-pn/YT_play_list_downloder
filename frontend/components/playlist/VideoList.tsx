"use client";

import { useMemo, useState } from "react";
import { VideoCard } from "./VideoCard";
import { Button } from "@/components/ui/Button";
import { usePlaylistStore } from "@/hooks/usePlaylistStore";

type SortKey = "position" | "title" | "duration";

export function VideoList() {
  const playlist = usePlaylistStore((s) => s.playlist);
  const selectedIds = usePlaylistStore((s) => s.selectedIds);
  const toggleVideo = usePlaylistStore((s) => s.toggleVideo);
  const selectAll = usePlaylistStore((s) => s.selectAll);
  const deselectAll = usePlaylistStore((s) => s.deselectAll);

  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("position");

  const visibleVideos = useMemo(() => {
    if (!playlist) return [];
    const filtered = playlist.videos.filter((v) => v.title.toLowerCase().includes(query.toLowerCase()));
    const sorted = [...filtered];
    if (sortKey === "title") sorted.sort((a, b) => a.title.localeCompare(b.title));
    else if (sortKey === "duration") sorted.sort((a, b) => b.duration_seconds - a.duration_seconds);
    else sorted.sort((a, b) => a.position - b.position);
    return sorted;
  }, [playlist, query, sortKey]);

  if (!playlist) return null;

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-1 gap-2">
          <input
            type="search"
            placeholder="Search videos..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full max-w-xs rounded-lg border border-default bg-card px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            aria-label="Search videos"
          />
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="rounded-lg border border-default bg-card px-3 py-2 text-sm outline-none ring-brand-500 focus:ring-2"
            aria-label="Sort videos"
          >
            <option value="position">Playlist order</option>
            <option value="title">Title (A–Z)</option>
            <option value="duration">Duration (longest first)</option>
          </select>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={selectAll}>
            Select all
          </Button>
          <Button variant="secondary" size="sm" onClick={deselectAll}>
            Deselect all
          </Button>
        </div>
      </div>

      <p className="mt-3 text-sm text-muted">
        {selectedIds.size} of {playlist.video_count} videos selected
      </p>

      {visibleVideos.length === 0 ? (
        <div className="mt-6 rounded-lg border border-dashed border-default p-8 text-center text-sm text-muted">
          No videos match your search.
        </div>
      ) : (
        <ul className="mt-4 space-y-2">
          {visibleVideos.map((video) => (
            <VideoCard
              key={video.external_id}
              video={video}
              selected={selectedIds.has(video.external_id)}
              onToggle={toggleVideo}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
