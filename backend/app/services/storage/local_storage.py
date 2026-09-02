from __future__ import annotations

import shutil
import time
import zipfile
from pathlib import Path

from app.config.settings import get_settings
from app.services.storage.base import StorageBackend
from app.utils.errors import StorageError
from app.utils.security import safe_join, sanitize_filename


class LocalStorage(StorageBackend):
    """Filesystem storage isolated per-job under STORAGE_LOCAL_PATH/jobs/<job_id>/.

    Every path this class hands out is verified with safe_join so a
    malicious job_id or filename can never escape the storage root.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._root = settings.storage_root / "jobs"
        self._root.mkdir(parents=True, exist_ok=True)

    def job_dir(self, job_id: str) -> Path:
        job_id = sanitize_filename(job_id, fallback="job")
        path = safe_join(self._root, job_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def resolve_file(self, job_id: str, filename: str) -> Path:
        job_id = sanitize_filename(job_id, fallback="job")
        filename = sanitize_filename(filename, fallback="file")
        return safe_join(self._root, job_id, filename)

    def list_files(self, job_id: str) -> list[Path]:
        d = self.job_dir(job_id)
        return sorted(p for p in d.iterdir() if p.is_file() and not p.name.endswith(".zip"))

    def total_size(self, job_id: str) -> int:
        return sum(p.stat().st_size for p in self.list_files(job_id))

    def create_zip(self, job_id: str, files: list[Path], zip_name: str) -> Path:
        zip_name = sanitize_filename(zip_name, fallback="playlist")
        if not zip_name.endswith(".zip"):
            zip_name += ".zip"
        dest = safe_join(self._root, job_id, zip_name)
        try:
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_STORED) as zf:
                for f in files:
                    zf.write(f, arcname=f.name)
        except OSError as exc:
            raise StorageError("Failed to create ZIP archive.") from exc
        return dest

    def delete_job(self, job_id: str) -> None:
        job_id = sanitize_filename(job_id, fallback="job")
        path = safe_join(self._root, job_id)
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)

    def job_age_hours(self, job_id: str) -> float | None:
        path = safe_join(self._root, sanitize_filename(job_id, fallback="job"))
        if not path.exists():
            return None
        age_seconds = time.time() - path.stat().st_mtime
        return age_seconds / 3600

    def list_all_job_ids(self) -> list[str]:
        if not self._root.exists():
            return []
        return [p.name for p in self._root.iterdir() if p.is_dir()]
