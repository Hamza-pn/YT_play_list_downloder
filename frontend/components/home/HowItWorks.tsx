const STEPS = [
  {
    title: "Paste a URL",
    description: "Drop in a public YouTube playlist, video, or Shorts link.",
  },
  { title: "Analyze it", description: "We fetch titles, thumbnails, and durations." },
  { title: "Select videos", description: "Choose all tracks or hand-pick specific ones." },
  { title: "Choose format & quality", description: "MP3 (128–320 kbps), M4A, or WAV." },
  { title: "Start conversion", description: "Track live progress for every video." },
  { title: "Download result", description: "Grab individual files or one ZIP archive." },
];

export function HowItWorks() {
  return (
    <section className="px-4 py-20 sm:px-6" id="how-it-works">
      <div className="mx-auto max-w-6xl">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
          <p className="mt-3 text-muted">Six steps from a YouTube link to finished audio files.</p>
        </div>
        <ol className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {STEPS.map((step, idx) => (
            <li key={step.title} className="relative rounded-xl border border-default bg-card p-6">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                {idx + 1}
              </span>
              <h3 className="mt-4 font-semibold">{step.title}</h3>
              <p className="mt-1.5 text-sm text-muted">{step.description}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
