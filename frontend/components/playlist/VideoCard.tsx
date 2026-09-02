import Image from "next/image";
import { formatDuration } from "@/lib/format";
import type { VideoOut } from "@/lib/types";

interface VideoCardProps {
  video: VideoOut;
  selected: boolean;
  onToggle: (id: string) => void;
}

export function VideoCard({ video, selected, onToggle }: VideoCardProps) {
  return (
    <li>
      <label
        className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
          video.available
            ? "cursor-pointer border-default hover:bg-subtle"
            : "cursor-not-allowed border-default opacity-50"
        } ${selected && video.available ? "ring-2 ring-brand-500" : ""}`}
      >
        <input
          type="checkbox"
          className="h-4 w-4 shrink-0 accent-brand-600"
          checked={selected}
          disabled={!video.available}
          onChange={() => onToggle(video.external_id)}
          aria-label={`Select ${video.title}`}
        />

        <div className="relative h-12 w-20 shrink-0 overflow-hidden rounded-md bg-subtle">
          {video.thumbnail_url ? (
            <Image
              src={video.thumbnail_url}
              alt=""
              fill
              sizes="80px"
              className="object-cover"
              unoptimized
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-xs text-muted">No image</div>
          )}
        </div>

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{video.title}</p>
          <p className="truncate text-xs text-muted">{video.channel_name ?? "Unknown channel"}</p>
        </div>

        <div className="shrink-0 text-right">
          <p className="text-xs tabular-nums text-muted">{formatDuration(video.duration_seconds)}</p>
          {!video.available && <p className="mt-0.5 text-[10px] font-medium text-red-500">Unavailable</p>}
        </div>
      </label>
    </li>
  );
}
