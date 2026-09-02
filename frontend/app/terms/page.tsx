import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service",
  description: "Terms governing use of PlaylistAudio, including permitted use and content responsibility.",
};

export default function TermsPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold">Terms of Service</h1>
      <p className="mt-2 text-sm text-muted">Last updated: {new Date().toLocaleDateString()}</p>

      <div className="prose-sm mt-8 space-y-6 text-sm leading-relaxed">
        <section>
          <h2 className="text-lg font-semibold">1. Permitted use</h2>
          <p className="mt-2 text-muted">
            You may only submit content that you own, that is licensed for download (e.g. released
            under a Creative Commons or public-domain license), or that you otherwise have explicit,
            verifiable permission to download and convert. You are solely responsible for confirming
            you have the necessary rights before submitting any playlist.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">2. Prohibited use</h2>
          <p className="mt-2 text-muted">
            You may not use this service to download copyrighted content you do not have rights to,
            circumvent access controls, download private or age/region-restricted content, or
            redistribute converted files in a way that infringes third-party rights. We do not access
            authenticated, private, or DRM-protected content, and we do not attempt to bypass any
            platform's access controls.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">3. No warranty</h2>
          <p className="mt-2 text-muted">
            The service is provided &quot;as is&quot; without warranty of any kind. Playlist metadata,
            availability, and conversion results depend on third-party sources outside our control.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">4. Limits and fair use</h2>
          <p className="mt-2 text-muted">
            To keep the service usable for everyone, guest sessions are subject to limits on playlist
            size, concurrent jobs, audio quality, and daily conversions. We may adjust these limits at
            any time.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">5. Temporary storage</h2>
          <p className="mt-2 text-muted">
            Converted files are stored temporarily and deleted automatically after a limited retention
            period. We do not retain media beyond what is operationally necessary to deliver your
            download.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">6. Termination</h2>
          <p className="mt-2 text-muted">
            We may suspend or block access for any use that violates these terms, applicable law, or
            third-party platform terms of service.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">7. Copyright / DMCA</h2>
          <p className="mt-2 text-muted">
            If you believe content processed through this service infringes your copyright, see our{" "}
            <a href="/abuse" className="underline underline-offset-2">
              abuse and copyright reporting page
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
