"use client";

import { useState } from "react";

const FAQS = [
  {
    q: "Am I allowed to use this to download any video?",
    a: "No. You may only download content you own, that is licensed for download (e.g. Creative Commons), or that you otherwise have explicit permission to download. You are responsible for how you use this tool — see our Terms of Service.",
  },
  {
    q: "How long are my converted files kept?",
    a: "Files are automatically deleted after a configurable retention window (a few hours by default). Download what you need before it expires.",
  },
  {
    q: "What audio formats are supported?",
    a: "MP3 at 128/192/256/320 kbps, M4A, and WAV. We avoid re-encoding when the source already matches your requested format.",
  },
  {
    q: "Do you store the videos or audio permanently?",
    a: "No. We only keep converted files temporarily so you can download them, and delete them automatically after the retention period.",
  },
  {
    q: "Is there a limit on playlist size?",
    a: "Yes — guest sessions have a maximum playlist size, daily conversion limit, and concurrent job limit to keep the service fair for everyone.",
  },
  {
    q: "What if a video in the playlist is private or unavailable?",
    a: "Unavailable videos are marked as such and skipped automatically; the rest of the playlist still converts normally.",
  },
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="border-t border-default bg-subtle px-4 py-20 sm:px-6" id="faq">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-center text-3xl font-bold tracking-tight">Frequently asked questions</h2>
        <div className="mt-10 divide-y divide-default rounded-xl border border-default bg-card">
          {FAQS.map((item, idx) => {
            const open = openIndex === idx;
            return (
              <div key={item.q}>
                <button
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                  aria-expanded={open}
                  onClick={() => setOpenIndex(open ? null : idx)}
                >
                  <span className="font-medium">{item.q}</span>
                  <span className={`shrink-0 text-muted transition-transform ${open ? "rotate-45" : ""}`}>+</span>
                </button>
                {open && <p className="px-5 pb-4 text-sm text-muted">{item.a}</p>}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
