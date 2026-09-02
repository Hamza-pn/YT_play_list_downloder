import type {
  ApiResponse,
  AudioFormat,
  JobFilesOut,
  JobStatusOut,
  PlaylistOut,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiRequestError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    });
  } catch {
    throw new ApiRequestError(
      "Could not reach the server. Check your connection and try again.",
      "network_error",
      0
    );
  }

  let body: ApiResponse<T> | null = null;
  try {
    body = await res.json();
  } catch {
    // non-JSON response (e.g. file download uses a different call path)
  }

  if (!res.ok || (body && body.success === false)) {
    const message =
      (body && !body.success && body.error?.message) || "Something went wrong. Please try again.";
    const code = (body && !body.success && body.error?.code) || "unknown_error";
    throw new ApiRequestError(message, code, res.status);
  }

  return (body as ApiResponse<T> & { success: true }).data;
}

export function analyzePlaylist(url: string): Promise<PlaylistOut> {
  return request<PlaylistOut>("/api/playlist/analyze", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function createDownloadJob(params: {
  playlistUrl: string;
  videoIds: string[];
  audioFormat: AudioFormat;
  qualityKbps: number | null;
}): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE_URL}/api/download/create`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      playlist_url: params.playlistUrl,
      video_ids: params.videoIds,
      audio_format: params.audioFormat,
      quality_kbps: params.qualityKbps,
    }),
  });
  const body = await res.json();
  if (!res.ok || body.success === false) {
    throw new ApiRequestError(body?.error?.message || "Could not start conversion.", body?.error?.code || "unknown_error", res.status);
  }
  return body;
}

export function getJobStatus(jobId: string): Promise<JobStatusOut> {
  return request<JobStatusOut>(`/api/download/${jobId}`);
}

export function getJobFiles(jobId: string): Promise<JobFilesOut> {
  return request<JobFilesOut>(`/api/download/${jobId}/files`);
}

export function deleteJob(jobId: string): Promise<null> {
  return request<null>(`/api/download/${jobId}`, { method: "DELETE" });
}

export function fileDownloadUrl(jobId: string, fileId: string): string {
  return `${API_BASE_URL}/api/download/${jobId}/file/${fileId}`;
}

export function zipDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/api/download/${jobId}/zip`;
}

export function progressStreamUrl(jobId: string): string {
  return `${API_BASE_URL}/api/download/${jobId}/progress`;
}
