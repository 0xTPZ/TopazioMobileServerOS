# Workspace map — Mission 012-E closeout

Status: `COMPLETE`, consolidated and documented on 2026-10-06.

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

## Preserved non-Git material

| Location | Classification | Action |
| --- | --- | --- |
| `C:\AndroidTools\platform-tools` | Shared external dependency | Keep in place; version and hashes are recorded in `EXTERNAL-DEPENDENCIES.md` |
| `local/backups/mission-012c/redmi-lab-audit` | Historical evidence | Canonical local-only preservation; raw identifiers stay out of Git |
| `local/cache/mission009` | Firmware/boot analysis cache | Canonical local-only cache; raw images stay out of Git |
| `local/cache/mission010` | DTBO/vbmeta cache | Canonical local-only cache; raw images stay out of Git |
| `local/cache/mission011` | vendor_dlkm cache | Canonical local-only cache; proprietary modules stay out of Git |
| `local/logs/mission012` | Host-only raw capture | Canonical local-only log |
| `local/logs/mission012b` | Transport probe output | Canonical local-only log |

The local caches remain outside Git intentionally: they are large, contain proprietary or raw firmware material, and are now under the canonical `local/` root. Their six original C:/E: locations were revalidated completely and then removed manually by the user. The exact commands remain in `docs/MANUAL-CLEANUP-REQUIRED.md` as a historical record; cleanup pending is `0`.

## Boundaries

The following are explicitly outside this project's change scope: `E:\Topazio`, `E:\TopazioReader`, `E:\TopazioAudioVideo`, `E:\AFolha`, `E:\LocalCoder`, `E:\MuOnline`, `E:\TopazioProjectManager`, `E:\OpenCut`, `E:\informacoes vps.txt`, Windows system directories, and the contents of all WSL distributions. Independent Git repositories found at `E:\AlicePlatform`, `E:\TopazioAI`, and `E:\Zelvya` were not inspected or changed.

No ADB, fastboot, WSL filesystem, driver installation, firmware operation, or Mission 013 activity belongs to this consolidation pass. The six known project-owned duplicate roots are absent, `PROJECT_OWNED_OUTSIDE_WORKSPACE = 0`, and no UNKNOWN path was identified.
