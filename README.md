# PlaylistAudio — YouTube Playlist & Video Audio Downloader

Convert audio from YouTube playlists, single videos, and Shorts you own or
have explicit permission to
download, into tagged MP3/M4A/WAV files. Full-stack app: Next.js frontend,
FastAPI backend, FFmpeg-based conversion pipeline, background job processing,
live progress via SSE, and automatic file cleanup.

> **Legal notice**: This tool only accesses publicly available YouTube data
> through normal, unauthenticated requests — it does not bypass DRM, access
> private/restricted content, or defeat platform access controls. Users are
> solely responsible for only submitting content they own, that is licensed
> for download, or that they otherwise have explicit permission to download.
> See [`/terms`](frontend/app/terms/page.tsx) and [`/privacy`](frontend/app/privacy/page.tsx).

## 1. Project overview

| | |
|---|---|
| **Frontend** | Next.js 16 (App Router), React, TypeScript, Tailwind CSS |
| **Backend** | Python 3.12, FastAPI |
| **Processing** | FFmpeg (audio conversion), yt-dlp (public metadata + media retrieval) |
| **Database** | SQLite (Phase 1 dev) → PostgreSQL (Phase 2 production) |
| **Queue** | In-process asyncio worker pool (Phase 1) → Redis + Celery/RQ (Phase 2) |
| **Storage** | Local filesystem (Phase 1) → S3-compatible object storage (Phase 4) |

## 2. Features (Phase 1 — implemented & tested)

- URL validation with SSRF protection (host allow-list + DNS-rebinding guard)
- Two source kinds, one pipeline:
  - **Playlist** — `/playlist?list=…`, or `/watch?v=…&list=…` (a `list=` param always wins, so opening a video from inside a playlist still gets the whole playlist)
  - **Single video** — `/watch?v=…`, `/shorts/<id>`, `/live/<id>`, `/embed/<id>`, and `youtu.be/<id>` short links. A single video is modelled as a one-item playlist, so job creation, conversion, progress, ZIP and cleanup are shared code with no special-casing
- Analysis: title, thumbnail, channel, video count, per-video duration/thumbnail/availability
- Select all / specific videos, search, sort
- MP3 (128/192/256/320 kbps), M4A, WAV output — stream-copy instead of re-encoding when the source already matches
- Automatic metadata: title, artist, album (playlist name), track number, year, embedded cover art — sanitized before writing
- Background job processing (never blocks an HTTP request)
- Live progress via Server-Sent Events, with polling fallback
- Individual file download + ZIP-all download
- Automatic temporary file cleanup (configurable retention) + orphan/abandoned-job cleanup
- Guest sessions (anonymous, cookie-based) with per-session limits
- Rate limiting, request size limits, path-traversal protection, filename sanitization
- Dark/light/system theme (persisted)
- SEO pages (How it works, Formats, FAQ, Terms, Privacy, Abuse/DMCA), sitemap, robots.txt
- Ad-slot components (disabled by default, one env var to enable)

## 3. Architecture

```
frontend/          Next.js app (App Router)
  app/              routes: /, /playlist, /download/[jobId], legal & SEO pages
  components/       ui/, home/, playlist/, download/, layout/
  hooks/            usePlaylistStore (zustand), useJobProgress (SSE)
  lib/              api client, types, validators, formatting

backend/
  app/
    api/routes/     playlist.py, download.py, health.py — HTTP layer only
    services/       business logic
      media_retrieval/   MediaRetrievalService interface + YtDlpService impl
      storage/            StorageBackend interface + LocalStorage impl
      audio_service.py    FFmpeg conversion (argv subprocess, no shell)
      metadata_service.py mutagen tagging
      job_service.py       playlist analysis + job/video orchestration
      session_service.py   guest sessions + limits
      cleanup_service.py   retention/orphan/stale-job cleanup
    workers/        InProcessJobQueue + the actual conversion pipeline
    models/         SQLAlchemy: User, Job, Playlist, Video, DownloadedFile, Subscription, SystemSettings
    schemas/        Pydantic request/response models
    utils/          validators (SSRF), security (path/filename), rate limiting, errors, logging
    config/         Settings (env-driven, CWD-independent path resolution)
  tests/            53+ tests: unit, API, integration (real ffmpeg, fake network), cleanup, rate limiting

docker/             Dockerfiles + nginx.conf (Phase 2+)
scripts/            helper scripts
docker-compose.yml  full stack (Phase 2+)
```

Every swappable concern is behind an interface + a factory function:
`get_media_retrieval_service()` and `get_storage_backend()`. Replacing
yt-dlp or moving from local disk to S3 means writing one new class and
changing one factory — no other code changes.

## 4. Requirements

- Python 3.12 (3.13/3.14 not yet validated against all pinned deps)
- Node.js 20+
- FFmpeg + ffprobe on PATH (or set `FFMPEG_PATH`/`FFPROBE_PATH`)
- Docker + Docker Compose (Phase 2+ only)

## 5. Installation

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

Install FFmpeg if you don't have it:

```bash
# Windows (winget)
winget install --id Gyan.FFmpeg -e

# macOS
brew install ffmpeg

# Debian/Ubuntu
sudo apt-get install ffmpeg
```

## 6. Environment setup

```bash
cp .env.example backend/.env       # backend reads backend/.env
cp frontend/.env.local.example frontend/.env.local
```

Edit `backend/.env` — at minimum change `SECRET_KEY` to a random value.
See [`.env.example`](.env.example) for every variable and what it controls
(limits, storage backend, database, etc.) — all are read at process start,
nothing is hard-coded.

## 7. Development

```bash
# Terminal 1 — backend (from backend/)
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend (from frontend/)
npm run dev
```

Visit http://localhost:3000. API docs (non-production only) at
http://localhost:8000/api/docs.

## 8. Running tests

```bash
# Backend (from backend/, venv active)
pytest tests/ -v

# Frontend type-check
cd frontend && npx tsc --noEmit
```

The backend suite fakes the media-retrieval layer (no network calls) but
runs **real** FFmpeg conversion and **real** mutagen tagging, so it doubles
as an integration test of the actual pipeline. A couple of tests are
skipped automatically if FFmpeg isn't found on PATH.

## 9. Docker setup (Phase 2+)

Not yet wired up for this MVP — Phase 1 intentionally has no Redis/Postgres/
Docker dependency (SQLite + in-process queue only), per the phased build
plan. `docker-compose.yml` and `docker/` Dockerfiles are scaffolded for
Phase 2 and will bring up `frontend`, `backend`, `worker`, `redis`,
`postgres`, and `nginx` with `docker compose up -d`.

## 10. Production deployment (outline, Phase 2+)

1. Provision a Linux VPS (2+ vCPU, 4GB+ RAM recommended for concurrent ffmpeg jobs)
2. Install Docker + Docker Compose
3. Clone the repository
4. Copy `.env.example` → `.env`, fill in production secrets (never commit `.env`)
5. `docker compose up -d`
6. Point your domain's A record at the VPS
7. Terminate HTTPS at the reverse proxy (nginx + Let's Encrypt/certbot, or a managed load balancer)
8. Configure nginx as reverse proxy in front of `frontend`/`backend`
9. Set up automated Postgres backups (e.g. `pg_dump` on a cron + off-box storage)
10. Monitor disk usage on the storage volume (converted files are temporary but disk fills up if cleanup stalls)
11. Confirm the cleanup worker/cron is running (`FILE_RETENTION_HOURS`, orphan cleanup) — don't rely on manual cleanup in production

## 11. Troubleshooting

**"ffmpeg_available": false at `/health`** — FFmpeg isn't on PATH. Set
`FFMPEG_PATH`/`FFPROBE_PATH` in `.env` to the full binary path, or install
FFmpeg and restart the process (a freshly-opened terminal is needed for a
PATH change from an installer to take effect).

**Playlist analyze fails with "playlist not found" or "unavailable" for a
playlist you can see fine in your browser** — yt-dlp's ability to parse
YouTube's page structure breaks whenever YouTube changes their site, so
**yt-dlp needs to be kept current**. If analysis or downloads start failing
across the board, upgrade first: `pip install -U yt-dlp`. This bit us during
development — the initially pinned version was ~20 months old and failed
with "Requested format is not available" on real videos; current releases
work.

**A "Radio"/Mix playlist (`list=RD...`) fails to analyze** — these are
generated from a seed video and YouTube rejects the bare
`/playlist?list=RD...` URL ("This playlist type is unviewable"); they only
resolve via `/watch?v=<seed>&list=RD...`. The URL validator preserves the
seed video id for exactly this reason — if you see this error, check you're
not stripping `v=` somewhere upstream. Radio mixes also commonly exceed
`MAX_PLAYLIST_VIDEOS` (they can run 300+ tracks) — that's the size guardrail
working as intended, not a bug.

**Jobs stuck in "processing"** — check `/health` for ffmpeg availability,
then check backend logs (structured JSON) for `job_started`/`video_failed`/
`job_completed` events. A job stuck past `JOB_TIMEOUT_SECONDS` is
auto-failed by the periodic cleanup cycle.

**CORS errors in the browser console** — `BACKEND_CORS_ORIGINS` in
`backend/.env` must include the exact frontend origin (e.g.
`http://localhost:3000`).

## 12. Security considerations

- URL validation restricts requests to an explicit YouTube host allow-list; IP literals and DNS-rebinding to private/loopback/link-local addresses are rejected
- All subprocess calls (ffmpeg/ffprobe) use argument arrays, never `shell=True` or string-formatted commands
- Filenames are sanitized (control chars, path separators, reserved Windows names, length) before touching the filesystem; all storage paths are verified to stay under the storage root (path traversal protection)
- Guest sessions use an opaque, signed, httponly cookie — no PII required
- Rate limiting, request body size limits, per-file and per-playlist size limits, per-session concurrent-job limits, daily conversion limits
- A job can't be deleted while its background worker is still actively processing it (prevents a database race between the delete and the in-flight worker)
- Errors returned to clients never include stack traces or internal details — see `app/main.py` exception handlers
- Secrets only ever come from environment variables (`.env`, gitignored) — nothing is hard-coded

## 13. File cleanup

Three layers:
1. **Retention on completion** — every completed/failed job gets an `expires_at` (`FILE_RETENTION_HOURS` from now); a periodic cleanup cycle (every 15 min) deletes expired jobs' files and DB rows.
2. **Stale processing jobs** — a job stuck in `processing` past `JOB_TIMEOUT_SECONDS` is auto-failed.
3. **Orphaned storage / abandoned jobs** — on-disk job directories with no matching DB row, and jobs stuck in `pending` for more than 2 hours (e.g. after a backend restart dropped the in-memory queue), are cleaned up automatically.

## 14. Scaling (Phase 4 direction)

Swap `LocalStorage` for an S3-compatible backend (interface already in
place at `app/services/storage/base.py`), swap `InProcessJobQueue` for
Celery+Redis (same enqueue/handler shape), move SQLite → Postgres (one env
var), and put multiple backend/worker replicas behind nginx/a load
balancer. None of the API or business-logic layers need to change for any
of this — that's the point of the interface boundaries.

## 15. License / usage

This is example/reference software. Deploying it publicly means you are
responsible for your own compliance with copyright law and YouTube's Terms
of Service in your jurisdiction.
