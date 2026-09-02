import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "How PlaylistAudio handles session data, playlist submissions, and temporary files.",
};

export default function PrivacyPage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold">Privacy Policy</h1>
      <p className="mt-2 text-sm text-muted">Last updated: {new Date().toLocaleDateString()}</p>

      <div className="prose-sm mt-8 space-y-6 text-sm leading-relaxed">
        <section>
          <h2 className="text-lg font-semibold">What we collect</h2>
          <p className="mt-2 text-muted">
            As a guest, we assign your browser an anonymous, random session identifier stored in an
            httponly cookie. We do not require registration, an email address, or any personal
            information to use the core service. We store the playlist URLs you submit, the videos
            you select, and job status/progress records tied to that anonymous session id.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">What we don&apos;t do</h2>
          <p className="mt-2 text-muted">
            We do not sell your data, place tracking pixels from third parties beyond the ad slots you
            can disable server-side, or permanently retain converted media — files are deleted
            automatically after a limited retention window.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">Cookies</h2>
          <p className="mt-2 text-muted">
            We use a single essential, httponly session cookie to associate your jobs with your
            browser and enforce fair-use limits. We also store your light/dark theme preference in
            your browser&apos;s local storage.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">Data retention</h2>
          <p className="mt-2 text-muted">
            Converted audio files and their metadata are deleted automatically after the configured
            retention period, and abandoned or orphaned jobs are cleaned up periodically by a
            background process.
          </p>
        </section>
        <section>
          <h2 className="text-lg font-semibold">Contact</h2>
          <p className="mt-2 text-muted">
            Questions about this policy can be sent to the admin contact listed on our{" "}
            <a href="/abuse" className="underline underline-offset-2">
              abuse reporting page
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
