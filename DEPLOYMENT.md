# Deploying PlaylistAudio for $0

This app is two separate pieces that talk to each other over HTTP:

| Piece | What it needs | Where it goes |
|---|---|---|
| `frontend/` (Next.js) | Node build | **Vercel** — free, built by the Next.js team, zero-config |
| `backend/` (FastAPI + ffmpeg + yt-dlp) | A real, persistent Python process + ffmpeg binary | **Render** — free Docker-based web service |

Neither of these needs a credit card to sign up. Both give you a free
`*.vercel.app` / `*.onrender.com` URL with HTTPS automatically — that's your
starting point before you touch a custom domain at all.

A `Dockerfile` for the backend is already sitting in `backend/Dockerfile` —
it installs ffmpeg and runs `uvicorn` bound to Render's `$PORT`. You don't
need to touch it.

---

## 0. Push the code to GitHub

Both Vercel and Render deploy by watching a GitHub repo. If it's not on
GitHub yet:

```bash
cd youtube_playlist_downloder
git init
git add .
git commit -m "Initial commit"
```

Create an empty repo on github.com, then:

```bash
git remote add origin https://github.com/<you>/<repo>.git
git branch -M main
git push -u origin main
```

Your `.gitignore` already excludes `.env`, `node_modules`, `.venv`, and the
SQLite db, so no secrets or junk get pushed.

---

## 1. Deploy the backend on Render

1. Go to render.com → sign up (GitHub login is easiest) → **New → Web Service**.
2. Connect the repo, and set:
   - **Root Directory**: `backend`
   - **Runtime**: Docker (it'll auto-detect the `Dockerfile`)
   - **Instance type**: Free
3. Add environment variables (Render dashboard → Environment):
   ```
   ENVIRONMENT=production
   SECRET_KEY=<generate a random 64-char string>
   DATABASE_URL=sqlite+pysqlite:///./storage/app.db
   BACKEND_CORS_ORIGINS=http://localhost:3000
   ```
   (You'll come back and fix `BACKEND_CORS_ORIGINS` in step 3 once you know
   your real frontend URL — leave it as a placeholder for now.)
4. Deploy. Once it's live, open `https://<your-service>.onrender.com/health`
   — you should see `"ffmpeg_available": true`.

**Free-tier reality check:** Render's free web services spin down after 15
minutes idle and take ~30–60s to wake back up on the next request. That's
fine for a personal project — your first visitor after a quiet period just
waits a bit. Disk is ephemeral (wiped on restart/redeploy), which is
actually a non-issue here since this app already treats storage as
temporary and self-cleans (`FILE_RETENTION_HOURS`).

---

## 2. Deploy the frontend on Vercel

1. Go to vercel.com → sign up → **Add New → Project** → import the same repo.
2. Set **Root Directory** to `frontend`. Vercel auto-detects Next.js — no
   build config needed.
3. Add environment variables (Project Settings → Environment Variables):
   ```
   NEXT_PUBLIC_API_BASE_URL=https://<your-service>.onrender.com
   NEXT_PUBLIC_SITE_URL=https://<your-project>.vercel.app
   NEXT_PUBLIC_ADS_ENABLED=false
   ```
4. Deploy.

---

## 3. Connect the two

Go back to Render → your backend's environment variables → update:

```
BACKEND_CORS_ORIGINS=https://<your-project>.vercel.app
```

This is what allows the browser (on your Vercel domain) to call the API (on
your Render domain) without CORS errors. Redeploy the backend after
changing it.

At this point you have a fully working, live app on free subdomains — try
it end to end before spending any more time on domains/SEO.

---

## 4. Domain name — realistic options at $0 and near-$0

Quick honest note: no legitimate registrar gives away a real `.com`/`.net`
for free — ICANN charges registries per registration, so a site promising
that is either bundling a paid plan or cutting corners somewhere (this is
why services like the one you asked about earlier score poorly on
trust/scam checkers). Real options, cheapest to most polished:

- **Free, starting today**: just use `your-project.vercel.app`. Totally
  fine for launch and for SEO — Google doesn't penalize subdomains.
- **Free, real subdomain**: [is-a.dev](https://www.is-a.dev/) is a
  legitimate, long-running open-source project (backed by GitHub) that
  gives developers a free `yourname.is-a.dev` domain via a pull request —
  no payment, no catch. You point it at Vercel with a CNAME.
- **Cheap, when you're ready**: a real domain from Cloudflare Registrar,
  Porkbun, or Namecheap runs **$1–15/year** depending on the TLD (`.com` is
  usually ~$9–12/yr at cost, no markup at Cloudflare). This is the
  legitimate version of what "free domain" sites are trying to imitate.

Once you have any domain: add it in Vercel (Project → Domains), point its
DNS at Vercel per their instructions (usually a CNAME or A record), and
update `NEXT_PUBLIC_SITE_URL` + Render's `BACKEND_CORS_ORIGINS` to match.

---

## 5. SEO — getting found on Google

The good news: the app already ships with the groundwork — a sitemap,
`robots.txt`, and dedicated SEO pages (How it works, Formats, FAQ). Here's
what actually moves the needle from here:

1. **Google Search Console** (free) — verify your domain, submit
   `https://yourdomain.com/sitemap.xml`. This is what gets you crawled and
   indexed in the first place; skip this and nothing else matters.
2. **Unique, real title/description per page** — you already have this via
   `metadata` exports in `layout.tsx` and each page. Keep them specific
   ("Convert a YouTube Playlist to MP3 — Free" beats a generic tagline).
3. **Page speed** — Vercel handles most of this for you (CDN, image
   optimization via `next/image`), but keep an eye on Core Web Vitals in
   Search Console once you have traffic.
4. **Content depth** — a one-page tool ranks worse than one with genuine
   supporting content. Your FAQ/Formats/How-it-works pages already help;
   expanding them with real, specific detail (not filler) helps more.
5. **Backlinks** — this is the slow, real bottleneck for any new site.
   Sharing it where it's actually relevant (relevant subreddits, dev
   directories, Product Hunt, your own socials) does more than any
   technical SEO tweak once the basics above are in place.

One honest caveat specific to this category: YouTube-downloader-type tools
are a competitive, sometimes adversarial SEO niche, and some sites in this
space get deindexed or lose ad-network approval over time regardless of
technical SEO quality, because of the copyright gray area inherent to the
category — not something on-page SEO can fix. Worth knowing going in.

---

## 6. Google Analytics (GA4)

Already wired into the code (`frontend/components/ui/GoogleAnalytics.tsx`,
loaded from `layout.tsx`) — it's a no-op until you give it an ID, same
pattern as the existing ad-slot toggle. To turn it on:

1. Go to [analytics.google.com](https://analytics.google.com) → **Admin →
   Create Property** → give it your site's name.
2. Add a **Web** data stream, enter your site URL. You'll get a
   **Measurement ID** that looks like `G-XXXXXXXXXX`.
3. In Vercel → Project Settings → Environment Variables, add:
   ```
   NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
   ```
4. Redeploy (env var changes need a redeploy to take effect).
5. Visit your live site, then check **Analytics → Reports → Realtime** —
   you should see yourself as an active user within ~30 seconds.

Optional but worth doing at the same time: link the same property in
**Search Console → Settings → Associations** so search performance data
shows up alongside your traffic data in one place.

---

## Order of operations, summarized

1. Push to GitHub
2. Deploy backend → Render (get its URL)
3. Deploy frontend → Vercel, pointing at that backend URL
4. Fix CORS on the backend to point at the real frontend URL
5. Test the live app end to end
6. (Optional) Add a real domain
7. Search Console + sitemap submission
8. GA4 measurement ID
