"use client";

import { Button } from "@/components/ui/Button";
import { formatBytes } from "@/lib/format";
import { fileDownloadUrl, zipDownloadUrl } from "@/lib/api";
import type { JobFilesOut } from "@/lib/types";

export function FileList({ jobId, files }: { jobId: string; files: JobFilesOut }) {
  const hasMultiple = files.files.length > 1;

  return (
    <div className="rounded-xl border border-default bg-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">Your files are ready</h2>
          <p className="text-sm text-muted">
            {files.files.length} file{files.files.length === 1 ? "" : "s"} · {formatBytes(files.total_size_bytes)} total
            {files.expires_at && (
              <> · available until {new Date(files.expires_at).toLocaleString()}</>
            )}
          </p>
        </div>
        {hasMultiple && (
          <a href={zipDownloadUrl(jobId)}>
            <Button>Download All (ZIP)</Button>
          </a>
        )}
      </div>

      <ul className="mt-5 divide-y divide-default border-t border-default">
        {files.files.map((f) => (
          <li key={f.id} className="flex items-center justify-between gap-3 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{f.filename}</p>
              <p className="text-xs text-muted">
                {f.audio_format.toUpperCase()}
                {f.quality_kbps ? ` · ${f.quality_kbps} kbps` : ""} · {formatBytes(f.size_bytes)}
              </p>
            </div>
            <a href={fileDownloadUrl(jobId, f.id)}>
              <Button variant="secondary" size="sm">
                Download
              </Button>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
