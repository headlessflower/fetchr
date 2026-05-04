import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio, Adw

from .window import MainWindow


class FetchrApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="dev.headlessflower.Fetchr")
        self._create_actions()

    def do_activate(self) -> None:
        window = self.props.active_window
        if not window:
            window = MainWindow(application=self)
        window.present()

    def _create_actions(self) -> None:
        actions = {
            "quit": self.on_quit,
            "about": self.on_about,
            "preferences": self.on_preferences,
            "open-download": self.on_open_download,
        }

        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        self.set_accels_for_action("app.quit", ["<Primary>q"])
        self.set_accels_for_action("app.open-download", ["<Primary>o"])

    def on_quit(self, action: Gio.SimpleAction, param) -> None:
        self.quit()

    def on_about(self, action: Gio.SimpleAction, param) -> None:
        if self.props.active_window:
            self.props.active_window.show_about_dialog()

    def on_preferences(self, action: Gio.SimpleAction, param) -> None:
        if self.props.active_window:
            self.props.active_window.show_preferences()

    def on_open_download(self, action: Gio.SimpleAction, param) -> None:
        if self.props.active_window:
            self.props.active_window.focus_url_entry()
