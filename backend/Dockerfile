# syntax=docker/dockerfile:1

FROM python:3.12-slim

# ffmpeg/ffprobe are required at runtime for audio conversion (see app/services/audio_service.py)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Storage dir for SQLite db + converted files (ephemeral on most free hosts — that's fine,
# the app already retention-cleans everything itself, see cleanup_service.py)
RUN mkdir -p /app/storage

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

EXPOSE 8000

# Render/Railway/Fly/Cloud Run all inject $PORT — fall back to 8000 for local `docker run`
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
