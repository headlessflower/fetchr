from __future__ import annotations

import json
from pathlib import Path


class SettingsService:
    def __init__(self) -> None:
        self.config_dir = Path.home() / ".config" / "fetchr"
        self.config_file = self.config_dir / "settings.json"
        self.defaults = {
            "output_dir": str(Path.home() / "Downloads"),
        }

    def load(self) -> dict:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            return dict(self.defaults)

        try:
            data = json.loads(self.config_file.read_text())
            merged = dict(self.defaults)
            merged.update(data)
            return merged
        except Exception:
            return dict(self.defaults)

    def save(self, settings: dict) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(json.dumps(settings, indent=2))
