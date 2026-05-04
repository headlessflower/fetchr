from pathlib import Path


def get_app_data_dir() -> Path:
    return Path.home() / ".local" / "share"
