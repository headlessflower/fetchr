# Fetchr

A native GNOME desktop application for downloading and converting online audio using **yt-dlp**, **ffmpeg**, **GTK4**, and **libadwaita**.

Fetchr was designed as a lightweight Linux-first alternative to Electron-based media downloaders, with a focus on GNOME integration, queue management, and a clean desktop workflow.

---

## Features

### Download Queue
- Add individual video or playlist URLs
- Sequential queue processing
- Automatic progression to the next item

### Live Progress Tracking
Each job displays:

- Download progress
- Conversion progress
- Current processing state

Examples:

- Queued
- Downloading
- Converting
- Completed
- Failed

---

## Audio Conversion

Fetchr currently supports:

- MP3
- FLAC
- WAV

Audio extraction is powered by:

- yt-dlp
- ffmpeg

Supported sources depend on yt-dlp support.

Examples include:

- YouTube
- SoundCloud
- Bandcamp
- Mixcloud
- Hundreds of additional supported extractors

---

## File Management

Fetchr includes:

### Output Folder Selection
Choose where downloads are saved.

### Recent Files Panel
Automatically scans the active output directory and displays:

- Recently created audio files
- File sizes
- Quick actions:
  - Open file
  - Open containing folder

### Queue Item Actions

Completed jobs:
- Open File
- Open Folder
- Remove

Failed jobs:
- Retry
- Remove

---

## Native GNOME Experience

Built using:

- Python 3
- GTK 4
- libadwaita

Fetchr integrates with:

- GNOME Files
- GNOME App Launcher
- GNOME File Picker portals
- Flatpak sandbox permissions

---

## Included Packages

### Runtime

Fetchr bundles or depends on:

| Package | Purpose |
|--------|---------|
| yt-dlp | Media extraction |
| ffmpeg | Audio conversion |
| PyGObject | GTK Python bindings |
| GTK4 | User interface |
| libadwaita | GNOME styling/components |

### Flatpak Runtime

Current runtime:

- `org.gnome.Platform`
- Runtime version: `48`

SDK:

- `org.gnome.Sdk`

---

## Current Architecture

Project layout:

```text
fetchr/
├── flatpak/
├── src/
│   └── fetchr/
│       ├── models/
│       ├── services/
│       ├── widgets/
│       ├── application.py
│       ├── window.py
│       └── main.py
├── data/
├── scripts/
└── tests/
```
