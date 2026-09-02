"use client";

import { usePlaylistStore } from "@/hooks/usePlaylistStore";
import { MP3_QUALITIES } from "@/lib/types";
import type { AudioFormat } from "@/lib/types";

const FORMATS: { value: AudioFormat; label: string; description: string }[] = [
  { value: "mp3", label: "MP3", description: "Best compatibility" },
  { value: "m4a", label: "M4A", description: "Best quality-to-size ratio" },
  { value: "wav", label: "WAV", description: "Uncompressed, best for editing" },
];

export function FormatSelector() {
  const audioFormat = usePlaylistStore((s) => s.audioFormat);
  const setAudioFormat = usePlaylistStore((s) => s.setAudioFormat);
  const qualityKbps = usePlaylistStore((s) => s.qualityKbps);
  const setQualityKbps = usePlaylistStore((s) => s.setQualityKbps);

  return (
    <div>
      <h3 className="text-sm font-semibold">Audio format</h3>
      <div className="mt-2 grid grid-cols-3 gap-2">
        {FORMATS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setAudioFormat(f.value)}
            aria-pressed={audioFormat === f.value}
            className={`rounded-lg border p-3 text-left transition-colors ${
              audioFormat === f.value
                ? "border-brand-600 bg-brand-50 dark:bg-brand-900/20"
                : "border-default hover:bg-subtle"
            }`}
          >
            <div className="font-semibold">{f.label}</div>
            <div className="text-xs text-muted">{f.description}</div>
          </button>
        ))}
      </div>

      {audioFormat === "mp3" && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold">MP3 quality</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {MP3_QUALITIES.map((kbps) => (
              <button
                key={kbps}
                type="button"
                onClick={() => setQualityKbps(kbps)}
                aria-pressed={qualityKbps === kbps}
                className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${
                  qualityKbps === kbps
                    ? "border-brand-600 bg-brand-600 text-white"
                    : "border-default hover:bg-subtle"
                }`}
              >
                {kbps} kbps
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
