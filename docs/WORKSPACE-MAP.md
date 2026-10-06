# Workspace map — Mission 012-C

Status: consolidated and documented on 2026-10-06.

## Canonical project

`E:\TopazioMobileServerOS` is the only source of truth for code, sanitized device observations, build profiles, tests, and project documentation.

Important tracked areas:

| Area | Role |
| --- | --- |
| `core/`, `devices/`, `profiles/`, `services/` | Project source and device/profile definitions |
| `host-tools/` | Read-only host validation, inventory, and forensic helpers |
| `scripts/`, `installer/`, `recovery/` | Reproducible host/build/recovery workflows |
| `tests/` | Mission gates and regression tests |
| `docs/` | Architecture, provenance, recovery, storage, and mission handoff |
| `build/` | Generated build outputs; never treated as source of truth |
| `local/` | Local-only cache, backup, and quarantine area; ignored by Git |

## Preserved external material

| Location | Classification | Action |
| --- | --- | --- |
| `C:\AndroidTools\platform-tools` | Shared external dependency | Keep in place; version and hashes are recorded in `EXTERNAL-DEPENDENCIES.md` |
| `C:\RedmiLabAudit` | Historical evidence | Keep original for compatibility and preserve a byte-identical copy under `local/backups/mission-012c/` |
| `%TEMP%\topazio-mission009-cache` | Firmware/boot analysis cache | Keep external and documented; do not commit raw images |
| `E:\TopazioMission010Cache` | DTBO/vbmeta cache | Keep external and documented; do not commit raw images |
| `E:\TopazioMission011Cache` | vendor_dlkm cache | Keep external and documented; do not commit proprietary modules |
| `%TEMP%\topazio-mission012-raw` | Host-only raw capture | Keep external until a separately approved cleanup window |
| `%TEMP%\topazio-mission012b-raw` | Transport probe output | Keep external until a separately approved cleanup window |

The external caches remain outside Git intentionally: they are large, contain proprietary or raw firmware material, and their deletion was not proven safe. The canonical manifest records their relationship, size, and reason.

## Boundaries

The following are explicitly outside this project's change scope: `E:\Topazio`, `E:\TopazioReader`, `E:\TopazioAudioVideo`, `E:\AFolha`, `E:\LocalCoder`, `E:\MuOnline`, `E:\TopazioProjectManager`, `E:\OpenCut`, `E:\informacoes vps.txt`, Windows system directories, and the contents of all WSL distributions. Independent Git repositories found at `E:\AlicePlatform`, `E:\TopazioAI`, and `E:\Zelvya` were not inspected or changed.

No ADB, fastboot, WSL filesystem, driver installation, firmware operation, deletion, or Mission 013 activity belongs to this consolidation pass.
