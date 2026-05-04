from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk

from ..models.job import Job, JobStatus


class JobRow(Gtk.Box):
    def __init__(
        self,
        job: Job,
        on_open_file,
        on_open_folder,
        on_retry,
        on_remove,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(8)
        self.set_margin_end(8)

        self._job_id = job.id
        self._on_open_file = on_open_file
        self._on_open_folder = on_open_folder
        self._on_retry = on_retry
        self._on_remove = on_remove

        self.title_label = Gtk.Label(xalign=0)
        self.title_label.set_wrap(True)
        self.title_label.set_selectable(True)

        self.status_label = Gtk.Label(xalign=0)
        self.status_label.add_css_class("dim-label")
        self.status_label.set_wrap(True)

        self.download_bar = Gtk.ProgressBar()
        self.download_bar.set_show_text(True)

        self.convert_bar = Gtk.ProgressBar()
        self.convert_bar.set_show_text(True)

        self.button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.open_file_button = Gtk.Button(label="Open File")
        self.open_file_button.connect(
            "clicked", lambda *_: self._on_open_file(self._job_id)
        )

        self.open_folder_button = Gtk.Button(label="Open Folder")
        self.open_folder_button.connect(
            "clicked", lambda *_: self._on_open_folder(self._job_id)
        )

        self.retry_button = Gtk.Button(label="Retry")
        self.retry_button.connect("clicked", lambda *_: self._on_retry(self._job_id))

        self.remove_button = Gtk.Button(label="Remove")
        self.remove_button.connect("clicked", lambda *_: self._on_remove(self._job_id))

        self.button_box.append(self.open_file_button)
        self.button_box.append(self.open_folder_button)
        self.button_box.append(self.retry_button)
        self.button_box.append(self.remove_button)

        self.append(self.title_label)
        self.append(self.status_label)
        self.append(self.download_bar)
        self.append(self.convert_bar)
        self.append(self.button_box)

        self.update(job)

    def update(self, job: Job) -> None:
        title = job.title or job.url
        self.title_label.set_text(title)

        if job.status == JobStatus.QUEUED:
            state_text = "Queued"
        elif job.status == JobStatus.DOWNLOADING:
            state_text = job.download_text or "Downloading"
        elif job.status == JobStatus.CONVERTING:
            state_text = job.convert_text or "Converting"
        elif job.status == JobStatus.COMPLETED:
            if job.output_path:
                from pathlib import Path

                name = Path(job.output_path).name

                if len(name) > 50:
                    name = name[:47] + "..."

                state_text = f"Completed • {name}"
            else:
                state_text = "Completed"
        elif job.status == JobStatus.FAILED:
            state_text = f"Failed: {job.error or 'Unknown error'}"
        elif job.status == JobStatus.CANCELED:
            state_text = "Canceled"
        else:
            state_text = job.status.value.capitalize()

        self.status_label.set_text(state_text)

        self.download_bar.set_fraction(max(0.0, min(job.download_percent / 100.0, 1.0)))
        self.download_bar.set_text(f"Download {job.download_percent:.0f}%")

        self.convert_bar.set_fraction(max(0.0, min(job.convert_percent / 100.0, 1.0)))
        self.convert_bar.set_text(f"Convert {job.convert_percent:.0f}%")

        has_output = bool(job.output_path)
        is_failed = job.status == JobStatus.FAILED
        is_active = job.status in (JobStatus.DOWNLOADING, JobStatus.CONVERTING)
        can_remove = not is_active

        self.open_file_button.set_sensitive(
            has_output and job.status == JobStatus.COMPLETED
        )
        self.open_folder_button.set_sensitive(has_output)
        self.retry_button.set_sensitive(is_failed)
        self.remove_button.set_sensitive(can_remove)
