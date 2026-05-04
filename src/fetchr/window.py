from __future__ import annotations

from pathlib import Path

import gi
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gio, GLib, Gtk

from .models.job import Job
from .services.download_service import DownloadService
from .services.queue_service import QueueService
from .services.settings_service import SettingsService
from .widgets.job_row import JobRow


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_title("Fetchr")
        self.set_default_size(1100, 760)

        self.settings_service = SettingsService()
        self.settings = self.settings_service.load()

        self.download_service = DownloadService()
        self.download_service.set_output_dir(Path(self.settings["output_dir"]))

        self.queue_service = QueueService(self.download_service)
        self.queue_service.set_queue_changed_callback(self.on_queue_changed)

        self.job_rows: dict[str, JobRow] = {}
        self.jobs_by_id: dict[str, Job] = {}

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        add_button = Gtk.Button(label="Add to Queue")
        add_button.add_css_class("suggested-action")
        add_button.connect("clicked", lambda *_: self.on_download_clicked())
        header_bar.pack_start(add_button)

        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")

        menu_button = Gtk.MenuButton(icon_name="open-menu-symbolic")
        menu_button.set_menu_model(menu)
        header_bar.pack_end(menu_button)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        toolbar_view.set_content(paned)

        left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_box.set_margin_top(12)
        left_box.set_margin_bottom(12)
        left_box.set_margin_start(12)
        left_box.set_margin_end(6)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_box.set_margin_top(12)
        right_box.set_margin_bottom(12)
        right_box.set_margin_start(6)
        right_box.set_margin_end(12)

        paned.set_start_child(left_box)
        paned.set_end_child(right_box)
        paned.set_position(720)

        url_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text("Paste a video or playlist URL")
        self.url_entry.set_hexpand(True)
        self.url_entry.connect("activate", lambda *_: self.on_download_clicked())

        self.download_button = Gtk.Button(label="Add to Queue")
        self.download_button.add_css_class("suggested-action")
        self.download_button.connect("clicked", lambda *_: self.on_download_clicked())

        url_box.append(self.url_entry)
        url_box.append(self.download_button)
        left_box.append(url_box)

        queue_header = Gtk.Label(label="Queue", xalign=0)
        queue_header.add_css_class("title-4")
        left_box.append(queue_header)

        self.queue_list = Gtk.ListBox()
        self.queue_list.add_css_class("boxed-list")
        self.queue_list.set_selection_mode(Gtk.SelectionMode.NONE)

        queue_scroller = Gtk.ScrolledWindow()
        queue_scroller.set_vexpand(True)
        queue_scroller.set_child(self.queue_list)
        left_box.append(queue_scroller)

        options_group = Adw.PreferencesGroup(title="Download Options")

        self.format_row = Adw.ComboRow(title="Format")
        format_model = Gtk.StringList.new(["MP3", "FLAC", "WAV"])
        self.format_row.set_model(format_model)
        self.format_row.set_selected(0)
        options_group.add(self.format_row)

        metadata_row = Adw.ActionRow(title="Embed metadata")
        self.metadata_switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.metadata_switch.set_active(True)
        metadata_row.add_suffix(self.metadata_switch)
        metadata_row.set_activatable_widget(self.metadata_switch)
        options_group.add(metadata_row)

        right_box.append(options_group)

        output_group = Adw.PreferencesGroup(title="Output")

        self.output_row = Adw.ActionRow(title="Download folder")
        self.output_row.set_subtitle(self.settings["output_dir"])
        self.choose_folder_button = Gtk.Button(label="Choose Folder")
        self.choose_folder_button.connect("clicked", self.on_choose_folder_clicked)
        self.output_row.add_suffix(self.choose_folder_button)
        output_group.add(self.output_row)

        right_box.append(output_group)
        self.recent_file_rows = []
        self.recent_files_group = Adw.PreferencesGroup(title="Recent Files")

        recent_files_scroller = Gtk.ScrolledWindow()
        recent_files_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        recent_files_scroller.set_min_content_height(260)
        recent_files_scroller.set_max_content_height(800)
        recent_files_scroller.set_child(self.recent_files_group)

        right_box.append(recent_files_scroller)

        self.refresh_recent_files()

        self.status_page = Adw.StatusPage()
        self.status_page.set_title("Ready")
        self.status_page.set_description("Add one or more URLs to start downloading.")
        left_box.append(self.status_page)

    def focus_url_entry(self) -> None:
        self.url_entry.grab_focus()

    def on_download_clicked(self) -> None:
        url = self.url_entry.get_text().strip()
        if not url:
            self.status_page.set_title("Missing URL")
            self.status_page.set_description("Paste a video or playlist URL first.")
            return

        self.queue_service.add_job(url)
        self.url_entry.set_text("")
        self.status_page.set_title("Queued")
        self.status_page.set_description("Download added to queue.")

    def on_queue_changed(self, jobs: list[Job]) -> None:
        def apply_update() -> bool:
            self.jobs_by_id = {job.id: job for job in jobs}
            current_ids = set(job.id for job in jobs)

            for child in list(iter_listbox_rows(self.queue_list)):
                row_id = getattr(child, "_job_id", None)
                if row_id and row_id not in current_ids:
                    self.queue_list.remove(child)

            self.job_rows = {
                job_id: row_widget
                for job_id, row_widget in self.job_rows.items()
                if job_id in current_ids
            }

            for job in jobs:
                if job.id in self.job_rows:
                    self.job_rows[job.id].update(job)
                else:
                    job_widget = JobRow(
                        job=job,
                        on_open_file=self.on_open_file,
                        on_open_folder=self.on_open_folder,
                        on_retry=self.on_retry_job,
                        on_remove=self.on_remove_job,
                    )
                    row = Gtk.ListBoxRow()
                    row.set_child(job_widget)
                    row._job_id = job.id
                    self.queue_list.append(row)
                    self.job_rows[job.id] = job_widget

            completed_count = sum(1 for job in jobs if job.status.value == "completed")

            if getattr(self, "_last_completed_count", 0) != completed_count:
                self._last_completed_count = completed_count
                self.refresh_recent_files()

            return False

        GLib.idle_add(apply_update)

    def on_open_file(self, job_id: str) -> None:
        job = self.jobs_by_id.get(job_id)
        if not job or not job.output_path:
            self.set_status_message(
                "Open file failed", "No output file is available yet."
            )
            return

        path = Path(job.output_path)
        if not path.exists():
            self.set_status_message("Open file failed", f"File not found: {path}")
            return

        uri = Gio.File.new_for_path(str(path)).get_uri()
        try:
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception as error:
            self.set_status_message("Open file failed", str(error))

    def on_open_folder(self, job_id: str) -> None:
        job = self.jobs_by_id.get(job_id)
        if not job or not job.output_path:
            self.set_status_message(
                "Open folder failed", "No output location is available yet."
            )
            return

        path = Path(job.output_path)
        folder = path.parent if path.suffix else path

        if not folder.exists():
            self.set_status_message("Open folder failed", f"Folder not found: {folder}")
            return

        uri = Gio.File.new_for_path(str(folder)).get_uri()
        try:
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception as error:
            self.set_status_message("Open folder failed", str(error))

    def on_retry_job(self, job_id: str) -> None:
        success = self.queue_service.retry_job(job_id)
        if success:
            self.set_status_message(
                "Retry queued", "The job was added back to the queue."
            )
        else:
            self.set_status_message(
                "Retry unavailable", "This job cannot be retried right now."
            )

    def on_remove_job(self, job_id: str) -> None:
        success = self.queue_service.remove_job(job_id)
        if success:
            self.set_status_message("Removed", "The job was removed from the queue.")
        else:
            self.set_status_message(
                "Remove unavailable", "Active jobs cannot be removed."
            )

    def on_choose_folder_clicked(self, button: Gtk.Button) -> None:
        dialog = Gtk.FileDialog(title="Choose Download Folder")
        dialog.select_folder(self, None, self.on_folder_selected)

    def on_folder_selected(self, dialog: Gtk.FileDialog, result) -> None:
        try:
            folder = dialog.select_folder_finish(result)
            if folder is None:
                return

            path = folder.get_path()
            if not path:
                return

            resolved_path = str(Path(path).expanduser().resolve())

            self.settings["output_dir"] = resolved_path
            self.settings_service.save(self.settings)
            self.download_service.set_output_dir(Path(resolved_path))
            self.output_row.set_subtitle(resolved_path)
            self.refresh_recent_files()

            self.set_status_message(
                "Folder updated",
                f"Downloads will be saved to: {resolved_path}",
            )
        except Exception as error:
            self.set_status_message("Folder selection failed", str(error))

    def set_status_message(self, title: str, description: str) -> None:
        self.status_page.set_title(title)
        self.status_page.set_description(description)

    def show_preferences(self) -> None:
        dialog = Adw.PreferencesDialog()
        page = Adw.PreferencesPage()

        group = Adw.PreferencesGroup(title="General")
        row = Adw.SwitchRow(title="Enable debug logging")
        group.add(row)

        page.add(group)
        dialog.add(page)
        dialog.present(self)

    def show_about_dialog(self) -> None:
        about = Adw.AboutDialog(
            application_name="Fetchr",
            application_icon="dev.headlessflower.Fetchr",
            developer_name="Gerardo Garcia",
            version="0.1.0",
            developers=["Gerardo Garcia"],
        )
        about.present(self)


    def refresh_recent_files(self) -> None:
        for row in self.recent_file_rows:
            self.recent_files_group.remove(row)

        self.recent_file_rows = []

        output_dir = Path(self.settings["output_dir"])

        if not output_dir.exists():
            row = Adw.ActionRow(title="Folder not found")
            self.recent_files_group.add(row)
            self.recent_file_rows.append(row)
            return

        audio_exts = {".mp3", ".flac", ".wav", ".m4a", ".opus", ".ogg", ".aac"}

        files = [
            path for path in output_dir.iterdir()
            if path.is_file() and path.suffix.lower() in audio_exts
        ]

        files.sort(key=lambda path: path.stat().st_mtime, reverse=True)

        if not files:
            row = Adw.ActionRow(title="No recent files")
            self.recent_files_group.add(row)
            self.recent_file_rows.append(row)
            return

        for path in files[:25]:
            row = Adw.ActionRow(title=path.name)
            row.set_subtitle(self.format_file_subtitle(path))

            open_button = Gtk.Button(label="Open")
            open_button.connect("clicked", lambda _button, p=path: self.open_path(p))
            row.add_suffix(open_button)

            folder_button = Gtk.Button(label="Folder")
            folder_button.connect("clicked", lambda _button, p=path: self.open_path(p.parent))
            row.add_suffix(folder_button)

            self.recent_files_group.add(row)
            self.recent_file_rows.append(row)


    def format_file_subtitle(self, path: Path) -> str:
        try:
            size_mb = path.stat().st_size / 1024 / 1024
            return f"{size_mb:.1f} MB"
        except OSError:
            return ""


    def open_path(self, path: Path) -> None:
        try:
            uri = Gio.File.new_for_path(str(path)).get_uri()
            Gio.AppInfo.launch_default_for_uri(uri, None)
        except Exception as error:
            self.set_status_message("Open failed", str(error))


def iter_listbox_rows(listbox: Gtk.ListBox):
    child = listbox.get_first_child()
    while child:
        yield child
        child = child.get_next_sibling()
