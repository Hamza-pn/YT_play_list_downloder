const FEATURES = [
  {
    title: "Format & quality control",
    description: "Export to MP3 (128–320 kbps), M4A, or WAV. We skip re-encoding when the source already matches your request.",
    icon: "🎚️",
  },
  {
    title: "Automatic tagging",
    description: "Title, artist, album, year, track number, and cover art are embedded automatically — sanitized before writing.",
    icon: "🏷️",
  },
  {
    title: "Live progress",
    description: "Watch every track move through downloading, converting, and done — with an overall progress bar and ETA.",
    icon: "📊",
  },
  {
    title: "Batch or selective",
    description: "Convert an entire playlist or hand-pick specific tracks. Search and sort before you commit.",
    icon: "✅",
  },
  {
    title: "One-click ZIP",
    description: "Download tracks individually or grab the whole batch as a single ZIP archive.",
    icon: "📦",
  },
  {
    title: "Files don't linger",
    description: "Converted files are automatically deleted after a configurable retention window — nothing sits on our servers.",
    icon: "🧹",
  },
];

export function Features() {
  return (
    <section className="border-t border-default bg-subtle px-4 py-20 sm:px-6" id="features">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">Everything you need, nothing you don&apos;t</h2>
          <p className="mt-3 text-muted">Built for speed and clarity — no clutter, no dark patterns.</p>
        </div>
        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="rounded-xl border border-default bg-card p-6">
              <div className="text-2xl">{f.icon}</div>
              <h3 className="mt-4 font-semibold">{f.title}</h3>
              <p className="mt-2 text-sm text-muted">{f.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
