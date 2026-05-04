# Fetchr

Native GNOME rewrite of the Electron app.

## Stack
- Python
- GTK 4
- libadwaita

## Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
fetchr
```

## Notes
Port logic from the Electron app gradually:
- queue logic
- yt-dlp command building
- ffmpeg path handling
- settings persistence
- error handling
