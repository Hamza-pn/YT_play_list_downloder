"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { useJobProgress } from "@/hooks/useJobProgress";
import { ProgressPanel } from "@/components/download/ProgressPanel";
import { FileList } from "@/components/download/FileList";
import { Button } from "@/components/ui/Button";
import { AdSlot } from "@/components/ui/AdSlot";
import { getJobFiles, ApiRequestError } from "@/lib/api";
import type { JobFilesOut } from "@/lib/types";

export default function DownloadPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = params.jobId;
  const { event, connectionError, notFound } = useJobProgress(jobId);
  const [files, setFiles] = useState<JobFilesOut | null>(null);
  const [filesError, setFilesError] = useState<string | null>(null);

  useEffect(() => {
    if (event?.status !== "completed" || files) return;
    getJobFiles(jobId)
      .then(setFiles)
      .catch((err) => {
        const message = err instanceof ApiRequestError ? err.message : "Could not load your files.";
        setFilesError(message);
        toast.error(message);
      });
  }, [event?.status, jobId, files]);

  const isTerminal = event && ["completed", "failed", "cancelled", "expired"].includes(event.status);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold">Conversion</h1>

      <div className="mt-6">
        {notFound && (
          <div className="rounded-xl border border-default bg-card p-8 text-center">
            <p className="text-lg font-semibold">Job not found</p>
            <p className="mt-2 text-sm text-muted">
              This conversion doesn&apos;t exist, or its files have already expired and been removed.
            </p>
            <Link href="/" className="mt-6 inline-block">
              <Button>Go to homepage</Button>
            </Link>
          </div>
        )}

        {!notFound && !isTerminal && <ProgressPanel event={event} connectionError={connectionError} />}

        {event?.status === "completed" && (
          <>
            {files && <FileList jobId={jobId} files={files} />}
            {filesError && (
              <div className="rounded-xl border border-default bg-card p-6 text-center">
                <p className="text-sm text-red-500">{filesError}</p>
                <Button className="mt-4" variant="secondary" onClick={() => setFilesError(null)}>
                  Retry
                </Button>
              </div>
            )}
            {event.failed_videos > 0 && (
              <p className="mt-4 text-sm text-amber-600 dark:text-amber-400">
                {event.failed_videos} video{event.failed_videos === 1 ? "" : "s"} could not be converted and{" "}
                {event.failed_videos === 1 ? "was" : "were"} skipped.
              </p>
            )}
          </>
        )}

        {(event?.status === "failed" || event?.status === "cancelled" || event?.status === "expired") && (
          <div className="rounded-xl border border-default bg-card p-8 text-center">
            <p className="text-lg font-semibold">
              {event.status === "cancelled" ? "Job cancelled" : "Conversion failed"}
            </p>
            <p className="mt-2 text-sm text-muted">
              {event.status === "failed"
                ? "All videos in this job failed to convert. This can happen if the source videos are unavailable or restricted."
                : "This job did not complete."}
            </p>
            <Link href="/playlist" className="mt-6 inline-block">
              <Button>Try again</Button>
            </Link>
          </div>
        )}
      </div>

      <AdSlot slot="download-page" className="mt-8" />
    </div>
  );
}
