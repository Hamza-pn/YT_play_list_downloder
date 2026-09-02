import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Supported Formats",
  description: "MP3, M4A, and WAV audio export options and quality settings supported by PlaylistAudio.",
};

const ROWS = [
  { format: "MP3", quality: "128, 192, 256, or 320 kbps (CBR)", best: "Universal playback compatibility" },
  { format: "M4A", quality: "AAC, remuxed without re-encoding when the source allows it", best: "Best quality-to-size ratio" },
  { format: "WAV", quality: "Uncompressed 16-bit PCM", best: "Further audio editing / production" },
];

export default function FormatsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold">Supported formats & quality</h1>
      <p className="mt-3 text-muted">
        Every conversion runs through FFmpeg. When the source audio already matches your requested
        format, we remux instead of re-encoding to preserve quality and save time.
      </p>
      <div className="mt-8 overflow-x-auto rounded-xl border border-default">
        <table className="w-full text-left text-sm">
          <thead className="bg-subtle">
            <tr>
              <th className="px-4 py-3 font-semibold">Format</th>
              <th className="px-4 py-3 font-semibold">Quality options</th>
              <th className="px-4 py-3 font-semibold">Best for</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-default">
            {ROWS.map((row) => (
              <tr key={row.format}>
                <td className="px-4 py-3 font-medium">{row.format}</td>
                <td className="px-4 py-3 text-muted">{row.quality}</td>
                <td className="px-4 py-3 text-muted">{row.best}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-6 text-sm text-muted">
        Every file is tagged with title, artist, album, track number, year (when available), and
        embedded cover art — sanitized before writing.
      </p>
    </div>
  );
}
