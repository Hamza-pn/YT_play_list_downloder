import { Hero } from "@/components/home/Hero";
import { HowItWorks } from "@/components/home/HowItWorks";
import { Features } from "@/components/home/Features";
import { SupportedFormats } from "@/components/home/SupportedFormats";
import { FAQ } from "@/components/home/FAQ";
import { AdSlot } from "@/components/ui/AdSlot";

export default function HomePage() {
  return (
    <>
      <Hero />
      <SupportedFormats />
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <AdSlot slot="homepage-mid" className="py-6" />
      </div>
      <HowItWorks />
      <Features />
      <FAQ />
    </>
  );
}
