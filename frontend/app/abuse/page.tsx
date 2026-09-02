import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Report Abuse / DMCA",
  description: "How to report copyright infringement or abuse of PlaylistAudio.",
};

export default function AbusePage() {
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
      <h1 className="text-3xl font-bold">Report abuse or a copyright concern</h1>
      <div className="prose-sm mt-8 space-y-6 text-sm leading-relaxed">
        <section>
          <p className="text-muted">
            PlaylistAudio is intended only for content the submitter owns, has a license to download,
            or otherwise has explicit permission to download. If you believe this service was used to
            infringe your copyright, or you want to report abusive use, contact our admin team with:
          </p>
          <ul className="mt-3 list-disc space-y-1 pl-5 text-muted">
            <li>The playlist or video URL in question</li>
            <li>A description of the right you hold and how it was infringed</li>
            <li>Your contact information</li>
          </ul>
        </section>
        <section>
          <h2 className="text-lg font-semibold">Contact</h2>
          <p className="mt-2 text-muted">
            Email the address configured as <code>ADMIN_EMAIL</code> in this deployment&apos;s
            environment configuration. We review reports and can disable processing or delete
            associated files upon valid request.
          </p>
        </section>
      </div>
    </div>
  );
}
