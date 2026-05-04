from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class Job:
    url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    output_path: Optional[str] = None
    error: Optional[str] = None

    download_percent: float = 0.0
    convert_percent: float = 0.0

    download_text: str = "Waiting"
    convert_text: str = "Waiting"

    extractor: Optional[str] = None
    filename: Optional[str] = None
