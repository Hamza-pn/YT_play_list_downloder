"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AudioFormat, PlaylistOut } from "@/lib/types";

interface PlaylistState {
  playlist: PlaylistOut | null;
  selectedIds: Set<string>;
  audioFormat: AudioFormat;
  qualityKbps: number;
  activeJobId: string | null;

  setPlaylist: (playlist: PlaylistOut) => void;
  toggleVideo: (externalId: string) => void;
  selectAll: () => void;
  deselectAll: () => void;
  setAudioFormat: (format: AudioFormat) => void;
  setQualityKbps: (kbps: number) => void;
  setActiveJobId: (jobId: string | null) => void;
  reset: () => void;
}

// Set isn't JSON-serializable by default; persist as an array instead.
type PersistedShape = Omit<PlaylistState, "selectedIds"> & { selectedIds: string[] };

export const usePlaylistStore = create<PlaylistState>()(
  persist(
    (set, get) => ({
      playlist: null,
      selectedIds: new Set(),
      audioFormat: "mp3",
      qualityKbps: 192,
      activeJobId: null,

      setPlaylist: (playlist) =>
        set({
          playlist,
          selectedIds: new Set(playlist.videos.filter((v) => v.available).map((v) => v.external_id)),
        }),

      toggleVideo: (externalId) => {
        const next = new Set(get().selectedIds);
        if (next.has(externalId)) next.delete(externalId);
        else next.add(externalId);
        set({ selectedIds: next });
      },

      selectAll: () => {
        const playlist = get().playlist;
        if (!playlist) return;
        set({ selectedIds: new Set(playlist.videos.filter((v) => v.available).map((v) => v.external_id)) });
      },

      deselectAll: () => set({ selectedIds: new Set() }),
      setAudioFormat: (audioFormat) => set({ audioFormat }),
      setQualityKbps: (qualityKbps) => set({ qualityKbps }),
      setActiveJobId: (activeJobId) => set({ activeJobId }),
      reset: () => set({ playlist: null, selectedIds: new Set(), activeJobId: null }),
    }),
    {
      name: "ytad-playlist-store",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state): PersistedShape => ({
        ...state,
        selectedIds: Array.from(state.selectedIds),
      }),
      merge: (persisted, current) => {
        const p = persisted as PersistedShape | undefined;
        if (!p) return current;
        return { ...current, ...p, selectedIds: new Set(p.selectedIds) };
      },
    }
  )
);
