import type { Metadata } from "next";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { Toaster } from "@/components/ui/Toaster";
import { GoogleAnalytics } from "@/components/ui/GoogleAnalytics";
import "./globals.css";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "PlaylistAudio — Convert YouTube Playlists to MP3, M4A, WAV",
    template: "%s | PlaylistAudio",
  },
  description:
    "Convert authorized YouTube playlists into tagged MP3, M4A, or WAV audio files. Select tracks, choose quality, and download individually or as a ZIP.",
  openGraph: {
    title: "PlaylistAudio — Convert YouTube Playlists to Audio",
    description:
      "Convert authorized YouTube playlists into tagged MP3, M4A, or WAV audio files.",
    url: SITE_URL,
    siteName: "PlaylistAudio",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "PlaylistAudio — Convert YouTube Playlists to Audio",
    description:
      "Convert authorized YouTube playlists into tagged MP3, M4A, or WAV audio files.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="flex min-h-screen flex-col antialiased">
        <GoogleAnalytics />
        <ThemeProvider>
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
