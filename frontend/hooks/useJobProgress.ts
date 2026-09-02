"use client";

import { useEffect, useRef, useState } from "react";
import { progressStreamUrl, getJobStatus, ApiRequestError } from "@/lib/api";
import type { JobProgressEvent, JobStatusValue } from "@/lib/types";

const TERMINAL: JobStatusValue[] = ["completed", "failed", "cancelled", "expired"];

export function useJobProgress(jobId: string | null) {
  const [event, setEvent] = useState<JobProgressEvent | null>(null);
  const [connectionError, setConnectionError] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) return;
    setEvent(null);
    setConnectionError(false);
    setNotFound(false);

    let cancelled = false;
    let source: EventSource | null = null;

    const startFallbackPolling = () => {
      if (pollRef.current) return;
      pollRef.current = setInterval(async () => {
        try {
          const status = await getJobStatus(jobId);
          setEvent((prev) => ({
            job_id: status.job_id,
            status: status.status,
            total_videos: status.total_videos,
            completed_videos: status.completed_videos,
            failed_videos: status.failed_videos,
            overall_percent: status.total_videos
              ? Math.round(((status.completed_videos + status.failed_videos) / status.total_videos) * 100)
              : 0,
            current_video_title: status.current_video_title,
            videos: prev?.videos ?? [],
            estimated_seconds_remaining: null,
          }));
          if (TERMINAL.includes(status.status) && pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        } catch (err) {
          if (err instanceof ApiRequestError && err.status === 404 && pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
            setNotFound(true);
          }
          // otherwise keep retrying silently; the UI shows a connection warning already
        }
      }, 3000);
    };

    // Check the job exists before opening a long-lived SSE connection, so an
    // invalid/expired job id surfaces a clear "not found" state instead of
    // an indefinite skeleton loader with silently-failing retries.
    getJobStatus(jobId)
      .then(() => {
        if (cancelled) return;
        source = new EventSource(progressStreamUrl(jobId), { withCredentials: true });

        source.onmessage = (msg) => {
          try {
            const parsed: JobProgressEvent = JSON.parse(msg.data);
            setEvent(parsed);
            setConnectionError(false);
            if (TERMINAL.includes(parsed.status)) {
              source?.close();
            }
          } catch {
            // ignore malformed frame
          }
        };

        source.onerror = () => {
          setConnectionError(true);
          source?.close();
          startFallbackPolling();
        };
      })
      .catch((err) => {
        if (cancelled) return;
        if (err instanceof ApiRequestError && err.status === 404) {
          setNotFound(true);
        } else {
          // Transient failure (network, 5xx) — fall back to polling rather
          // than giving up immediately.
          startFallbackPolling();
        }
      });

    return () => {
      cancelled = true;
      source?.close();
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [jobId]);

  return { event, connectionError, notFound };
}
