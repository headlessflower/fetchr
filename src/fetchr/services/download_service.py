from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

ProgressCallback = Callable[[str, dict], None]


class DownloadService:
    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or (Path.home() / "Downloads")

    def set_output_dir(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    def find_ytdlp(self) -> str:
        candidate = shutil.which("yt-dlp")
        if not candidate:
            raise RuntimeError("yt-dlp is not installed or not in PATH.")
        return candidate

    def find_ffmpeg(self) -> str:
        candidate = shutil.which("ffmpeg")
        if not candidate:
            raise RuntimeError("ffmpeg is not installed or not in PATH.")
        return candidate

    def download_audio(
        self,
        url: str,
        audio_format: str = "mp3",
        progress_callback: Optional[ProgressCallback] = None,
    ) -> int:
        ytdlp = self.find_ytdlp()
        ffmpeg = self.find_ffmpeg()

        self.output_dir.mkdir(parents=True, exist_ok=True)

        command = [
            ytdlp,
            "--newline",
            "--extract-audio",
            "--audio-format",
            audio_format,
            "--embed-metadata",
            "--ffmpeg-location",
            ffmpeg,
            "--output",
            str(self.output_dir / "%(title)s.%(ext)s"),
            url,
        ]

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if process.stdout is None:
            raise RuntimeError("Could not capture yt-dlp output.")

        download_re = re.compile(r"\[download\]\s+(\d+(?:\.\d+)?)%")
        destination_re = re.compile(r"\[download\]\s+Destination:\s+(.*)")
        already_downloaded_re = re.compile(
            r"\[download\]\s+(.*) has already been downloaded"
        )
        extract_audio_dest_re = re.compile(r"\[ExtractAudio\]\s+Destination:\s+(.*)")
        title_re = re.compile(r"\[download\]\s+(.+?)\s+\[[^\]]+\]")

        for raw_line in process.stdout:
            line = raw_line.strip()

            if progress_callback:
                progress_callback("log", {"line": line})

            title_match = title_re.search(line)
            if title_match and progress_callback:
                progress_callback("title", {"title": title_match.group(1)})

            match = destination_re.search(line)
            if match and progress_callback:
                progress_callback("destination", {"filename": match.group(1)})

            match = already_downloaded_re.search(line)
            if match and progress_callback:
                progress_callback("destination", {"filename": match.group(1)})
                progress_callback(
                    "download_progress",
                    {
                        "percent": 100.0,
                        "text": "Already downloaded",
                    },
                )

            match = extract_audio_dest_re.search(line)
            if match and progress_callback:
                progress_callback("final_path", {"filename": match.group(1)})
                progress_callback(
                    "convert_status",
                    {
                        "text": line,
                    },
                )

            match = download_re.search(line)
            if match and progress_callback:
                progress_callback(
                    "download_progress",
                    {
                        "percent": float(match.group(1)),
                        "text": line,
                    },
                )
                continue

            if line.startswith("[download]") and progress_callback:
                progress_callback(
                    "download_status",
                    {
                        "text": line,
                    },
                )

            if (
                "[ExtractAudio]" in line
                or "ffmpeg" in line.lower()
                or "Post-process" in line
            ) and progress_callback:
                progress_callback(
                    "convert_status",
                    {
                        "text": line,
                    },
                )

        return process.wait()
