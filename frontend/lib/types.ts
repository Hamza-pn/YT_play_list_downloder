export type AudioFormat = "mp3" | "m4a" | "wav";

export const MP3_QUALITIES = [128, 192, 256, 320] as const;
export type Mp3Quality = (typeof MP3_QUALITIES)[number];

export interface VideoOut {
  external_id: string;
  title: string;
  channel_name: string | null;
  thumbnail_url: string | null;
  duration_seconds: number;
  position: number;
  available: boolean;
}

export interface PlaylistOut {
  external_id: string;
  title: string;
  channel_name: string | null;
  thumbnail_url: string | null;
  video_count: number;
  videos: VideoOut[];
  source_url: string;
}

export interface VideoProgressOut {
  id: string;
  external_id: string;
  title: string;
  status: "waiting" | "downloading" | "converting" | "completed" | "failed" | "skipped";
  progress_percent: number;
  error_message: string | null;
}

export type JobStatusValue =
  | "pending"
  | "analyzing"
  | "processing"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

export interface JobProgressEvent {
  job_id: string;
  status: JobStatusValue;
  total_videos: number;
  completed_videos: number;
  failed_videos: number;
  overall_percent: number;
  current_video_title: string | null;
  videos: VideoProgressOut[];
  estimated_seconds_remaining: number | null;
}

export interface JobStatusOut {
  job_id: string;
  status: JobStatusValue;
  audio_format: AudioFormat;
  quality_kbps: number | null;
  total_videos: number;
  completed_videos: number;
  failed_videos: number;
  current_video_title: string | null;
  error_message: string | null;
  total_size_bytes: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  expires_at: string | null;
}

export interface FileOut {
  id: string;
  filename: string;
  audio_format: AudioFormat;
  quality_kbps: number | null;
  size_bytes: number;
}

export interface JobFilesOut {
  job_id: string;
  status: JobStatusValue;
  files: FileOut[];
  total_size_bytes: number;
  expires_at: string | null;
}

export interface ApiSuccess<T> {
  success: true;
  data: T;
  message?: string | null;
}

export interface ApiError {
  success: false;
  error: { code: string; message: string };
}

export type ApiResponse<T> = ApiSuccess<T> | ApiError;
