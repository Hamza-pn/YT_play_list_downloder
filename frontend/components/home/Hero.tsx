import { PlaylistForm } from "./PlaylistForm";

export function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-16 sm:px-6 sm:pt-24">
      <div className="mx-auto max-w-4xl text-center">
        <span className="inline-flex items-center rounded-full border border-default bg-subtle px-3 py-1 text-xs font-medium text-muted">
          For content you own or are authorized to download
        </span>
        <h1 className="mt-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
          Turn a playlist into audio files,{" "}
          <span className="bg-gradient-to-r from-brand-500 to-brand-700 bg-clip-text text-transparent">
            in minutes
          </span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-muted">
          Paste a playlist link, pick your tracks, choose MP3, M4A, or WAV — get clean files with
          titles, artist, and cover art already tagged.
        </p>
        <div className="mt-10">
          <PlaylistForm />
        </div>
      </div>
    </section>
  );
}
