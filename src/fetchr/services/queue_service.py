from __future__ import annotations

import threading
from typing import Callable, Optional

from ..models.job import Job, JobStatus
from .download_service import DownloadService

QueueChangedCallback = Callable[[list[Job]], None]


class QueueService:
    def __init__(self, download_service: DownloadService) -> None:
        self.download_service = download_service
        self.jobs: list[Job] = []
        self._lock = threading.Lock()
        self._active_job_id: Optional[str] = None
        self._queue_changed_callback: Optional[QueueChangedCallback] = None

    def set_queue_changed_callback(self, callback: QueueChangedCallback) -> None:
        self._queue_changed_callback = callback

    def _notify(self) -> None:
        if self._queue_changed_callback:
            self._queue_changed_callback(list(self.jobs))

    def add_job(self, url: str) -> Job:
        job = Job(url=url)
        with self._lock:
            self.jobs.append(job)
        self._notify()
        self._start_next_if_idle()
        return job

    def get_jobs(self) -> list[Job]:
        with self._lock:
            return list(self.jobs)

    def remove_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._find_job_locked(job_id)
            if job is None:
                return False

            if job.id == self._active_job_id:
                return False

            self.jobs = [
                existing_job for existing_job in self.jobs if existing_job.id != job_id
            ]

        self._notify()
        return True

    def retry_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._find_job_locked(job_id)
            if job is None:
                return False

            if job.id == self._active_job_id:
                return False

            if job.status not in (
                JobStatus.FAILED,
                JobStatus.COMPLETED,
                JobStatus.CANCELED,
            ):
                return False

            job.status = JobStatus.QUEUED
            job.error = None
            job.output_path = None
            job.filename = None
            job.download_percent = 0.0
            job.convert_percent = 0.0
            job.download_text = "Waiting"
            job.convert_text = "Waiting"

        self._notify()
        self._start_next_if_idle()
        return True

    def _find_job_locked(self, job_id: str) -> Optional[Job]:
        return next((job for job in self.jobs if job.id == job_id), None)

    def _start_next_if_idle(self) -> None:
        with self._lock:
            if self._active_job_id is not None:
                return

            next_job = next(
                (job for job in self.jobs if job.status == JobStatus.QUEUED), None
            )
            if next_job is None:
                return

            self._active_job_id = next_job.id

        thread = threading.Thread(target=self._run_job, args=(next_job,), daemon=True)
        thread.start()

    def _run_job(self, job: Job) -> None:
        job.status = JobStatus.DOWNLOADING
        job.download_text = "Starting download"
        self._notify()

        def handle_progress(event_type: str, payload: dict) -> None:
            if event_type == "title":
                title = payload.get("title")
                if title:
                    job.title = title

            elif event_type == "destination":
                filename = payload.get("filename")
                if filename:
                    job.filename = filename
                    if not job.output_path:
                        job.output_path = filename

            elif event_type == "final_path":
                filename = payload.get("filename")
                if filename:
                    job.output_path = filename

            elif event_type == "download_progress":
                job.status = JobStatus.DOWNLOADING
                job.download_percent = float(payload.get("percent", 0.0))
                job.download_text = payload.get("text", "Downloading")

            elif event_type == "download_status":
                job.status = JobStatus.DOWNLOADING
                job.download_text = payload.get("text", "Downloading")

            elif event_type == "convert_status":
                job.status = JobStatus.CONVERTING
                if job.convert_percent < 10:
                    job.convert_percent = 10.0
                else:
                    job.convert_percent = min(job.convert_percent + 5.0, 95.0)
                job.convert_text = payload.get("text", "Converting")

            self._notify()

        try:
            return_code = self.download_service.download_audio(
                url=job.url,
                audio_format="mp3",
                progress_callback=handle_progress,
            )

            if return_code == 0:
                job.status = JobStatus.COMPLETED
                job.download_percent = 100.0
                job.convert_percent = 100.0
                job.download_text = "Download complete"
                job.convert_text = "Conversion complete"
            else:
                job.status = JobStatus.FAILED
                job.error = f"yt-dlp exited with code {return_code}"

        except Exception as error:
            job.status = JobStatus.FAILED
            job.error = str(error)

        finally:
            with self._lock:
                self._active_job_id = None
            self._notify()
            self._start_next_if_idle()
