const FORMATS = [
  { name: "MP3", detail: "128 / 192 / 256 / 320 kbps", note: "Best compatibility" },
  { name: "M4A", detail: "AAC, remuxed when possible", note: "Best quality-to-size ratio" },
  { name: "WAV", detail: "Uncompressed PCM", note: "Best for further editing" },
];

export function SupportedFormats() {
  return (
    <section className="border-t border-default px-4 py-16 sm:px-6" id="formats">
      <div className="mx-auto max-w-4xl">
        <h2 className="text-center text-2xl font-bold tracking-tight">Supported formats & quality</h2>
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {FORMATS.map((f) => (
            <div key={f.name} className="rounded-xl border border-default bg-card p-5 text-center">
              <div className="text-xl font-bold text-brand-600">{f.name}</div>
              <div className="mt-1 text-sm">{f.detail}</div>
              <div className="mt-1 text-xs text-muted">{f.note}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
