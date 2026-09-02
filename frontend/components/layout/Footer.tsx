import Link from "next/link";

const COLUMNS = [
  {
    title: "Product",
    links: [
      { href: "/", label: "Home" },
      { href: "/how-it-works", label: "How it works" },
      { href: "/formats", label: "Supported formats" },
      { href: "/faq", label: "FAQ" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "/terms", label: "Terms of Service" },
      { href: "/privacy", label: "Privacy Policy" },
      { href: "/abuse", label: "Report abuse / DMCA" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-default bg-subtle">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
          <div className="col-span-2 sm:col-span-2">
            <div className="flex items-center gap-2 font-semibold">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-white text-xs">
                PA
              </span>
              PlaylistAudio
            </div>
            <p className="mt-3 max-w-sm text-sm text-muted">
              A tool for converting audio from content you own or have explicit permission to
              download. We do not host, index, or distribute copyrighted media.
            </p>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h3 className="text-sm font-semibold">{col.title}</h3>
              <ul className="mt-3 space-y-2">
                {col.links.map((link) => (
                  <li key={link.href}>
                    <Link href={link.href} className="text-sm text-muted hover:text-current">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 border-t border-default pt-6 text-xs text-muted">
          <p>
            © {new Date().getFullYear()} PlaylistAudio. You are solely responsible for ensuring you
            have the right to download and convert any content you submit.
          </p>
        </div>
      </div>
    </footer>
  );
}
