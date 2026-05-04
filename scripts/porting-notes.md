# Porting notes

## Port first
- queue.ts -> services/queue_service.py
- queueLimits.ts -> services/queue_service.py or config
- ytPaths.ts -> utils/paths.py or services/download_service.py
- settings.ts -> services/settings_service.py
- errors.ts -> shared exception classes

## Do not port directly
- ipc.ts
- preload/
- renderer/

## Goal
Keep the backend behavior, replace the Electron shell.
