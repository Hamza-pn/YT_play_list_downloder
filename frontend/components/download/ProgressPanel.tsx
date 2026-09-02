import { ProgressBar } from "@/components/ui/ProgressBar";
import { formatEta } from "@/lib/format";
import type { JobProgressEvent, VideoProgressOut } from "@/lib/types";

const STATUS_ICON: Record<VideoProgressOut["status"], string> = {
  waiting: "○",
  downloading: "⟳",
  converting: "⟳",
  completed: "✓",
  failed: "✗",
  skipped: "—",
};

const STATUS_COLOR: Record<VideoProgressOut["status"], string> = {
  waiting: "text-muted",
  downloading: "text-brand-600",
  converting: "text-brand-600",
  completed: "text-green-600",
  failed: "text-red-500",
  skipped: "text-muted",
};

const STATUS_LABEL: Record<VideoProgressOut["status"], string> = {
  waiting: "Waiting",
  downloading: "Downloading",
  converting: "Converting",
  completed: "Completed",
  failed: "Failed",
  skipped: "Skipped",
};

export function ProgressPanel({ event, connectionError }: { event: JobProgressEvent | null; connectionError: boolean }) {
  if (!event) {
    return (
      <div className="rounded-xl border border-default bg-card p-6">
        <div className="skeleton h-3 w-32 rounded" />
        <div className="skeleton mt-4 h-2.5 w-full rounded-full" />
      </div>
    );
  }

  const completed = event.videos.filter((v) => v.status === "completed").length;
  const processing = event.videos.filter((v) => v.status === "downloading" || v.status === "converting").length;
  const waiting = event.videos.filter((v) => v.status === "waiting").length;
  const failed = event.videos.filter((v) => v.status === "failed").length;

  return (
    <div className="rounded-xl border border-default bg-card p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Processing playlist...</h2>
        <span className="text-sm tabular-nums text-muted">{event.overall_percent}%</span>
      </div>

      <ProgressBar percent={event.overall_percent} className="mt-3" />

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted">
        <span>
          {event.completed_videos + event.failed_videos} / {event.total_videos} videos
        </span>
        {event.estimated_seconds_remaining !== null && <span>{formatEta(event.estimated_seconds_remaining)}</span>}
      </div>

      {event.current_video_title && (
        <p className="mt-4 truncate text-sm">
          <span className="text-muted">Currently processing: </span>
          <span className="font-medium">{event.current_video_title}</span>
        </p>
      )}

      {connectionError && (
        <p className="mt-3 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-600 dark:text-amber-400">
          Live updates interrupted — falling back to periodic refresh.
        </p>
      )}

      <div className="mt-5 flex flex-wrap gap-4 text-sm">
        <span className="text-green-600">✓ {completed} completed</span>
        <span className="text-brand-600">⟳ {processing} processing</span>
        <span className="text-muted">○ {waiting} waiting</span>
        {failed > 0 && <span className="text-red-500">✗ {failed} failed</span>}
      </div>

      {event.videos.length > 0 && (
        <ul className="mt-5 max-h-72 space-y-1 overflow-y-auto border-t border-default pt-4">
          {event.videos.map((v) => (
            <li key={v.id} className="flex items-center gap-3 py-1 text-sm">
              <span className={`w-4 shrink-0 text-center ${STATUS_COLOR[v.status]}`} aria-hidden>
                {STATUS_ICON[v.status]}
              </span>
              <span className="min-w-0 flex-1 truncate">{v.title}</span>
              <span className={`shrink-0 text-xs ${STATUS_COLOR[v.status]}`}>{STATUS_LABEL[v.status]}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
