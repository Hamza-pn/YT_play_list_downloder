import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "How It Works",
  description: "Learn how PlaylistAudio analyzes a YouTube playlist, converts selected videos to audio, and delivers your downloads.",
};

const STEPS = [
  {
    title: "1. Submit a playlist URL",
    body: "Paste a public YouTube playlist link. We validate the URL and reject anything that isn't a genuine youtube.com playlist link before any lookup happens.",
  },
  {
    title: "2. We analyze the playlist",
    body: "We fetch publicly available metadata only — title, channel, thumbnails, and per-video duration. Private, members-only, or otherwise restricted videos are marked unavailable and cannot be selected.",
  },
  {
    title: "3. You select videos and a format",
    body: "Choose all videos or specific ones, then pick MP3 (with a bitrate), M4A, or WAV.",
  },
  {
    title: "4. Background conversion",
    body: "A background worker downloads each selected video's audio track, converts it with FFmpeg (re-encoding only when necessary), and embeds sanitized metadata and cover art.",
  },
  {
    title: "5. Download your files",
    body: "Download tracks individually or as a single ZIP. Files are automatically deleted after a configurable retention window.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold">How PlaylistAudio works</h1>
      <p className="mt-3 text-muted">
        A transparent look at each step of the pipeline, from the link you paste to the files you
        download.
      </p>
      <div className="mt-10 space-y-8">
        {STEPS.map((step) => (
          <div key={step.title}>
            <h2 className="text-lg font-semibold">{step.title}</h2>
            <p className="mt-2 text-muted">{step.body}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
