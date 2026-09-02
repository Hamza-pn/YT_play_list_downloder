from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def job_dir(self, job_id: str) -> Path: ...

    @abstractmethod
    def resolve_file(self, job_id: str, filename: str) -> Path: ...

    @abstractmethod
    def list_files(self, job_id: str) -> list[Path]: ...

    @abstractmethod
    def total_size(self, job_id: str) -> int: ...

    @abstractmethod
    def create_zip(self, job_id: str, files: list[Path], zip_name: str) -> Path: ...

    @abstractmethod
    def delete_job(self, job_id: str) -> None: ...

    @abstractmethod
    def job_age_hours(self, job_id: str) -> float | None: ...

    @abstractmethod
    def list_all_job_ids(self) -> list[str]: ...
