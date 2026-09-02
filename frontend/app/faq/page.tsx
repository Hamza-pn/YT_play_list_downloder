import type { Metadata } from "next";
import { FAQ } from "@/components/home/FAQ";

export const metadata: Metadata = {
  title: "FAQ",
  description: "Answers to common questions about using PlaylistAudio responsibly.",
};

export default function FAQPage() {
  return (
    <div className="py-8">
      <div className="mx-auto max-w-3xl px-4 pt-8 sm:px-6">
        <h1 className="text-3xl font-bold">Frequently asked questions</h1>
      </div>
      <FAQ />
    </div>
  );
}
