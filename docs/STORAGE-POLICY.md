# Storage and cleanup policy

Mission 012-C establishes this policy for Topazio Mobile Server OS.

## Classification

| Classification | Meaning | Default location | Git policy |
| --- | --- | --- | --- |
| `SOURCE_OF_TRUTH` | Code, sanitized metadata, tests, and durable docs | Repository | Track after secret/artifact scan |
| `HISTORICAL_EVIDENCE` | Audit trail or observation needed to explain a past mission | Local backup plus documented original | Do not track raw identifiers |
| `EXTERNAL_SHARED_DEPENDENCY` | Tool, WSL distribution, or host resource used beyond this project | Existing external path | Do not move, delete, or vendor |
| `FIRMWARE_CACHE` | Raw OTA, image, partition, vendor, or extracted blob | External cache | Never track raw material |
| `REPRODUCIBLE_ARTIFACT` | Build or analysis result reproducible from documented source | Ignored local cache | Track only sanitized metadata |
| `TEMPORARY_RAW_CAPTURE` | Raw command output or host capture | External temporary path | Keep only while evidence is needed |
| `BACKUP_LOCAL_ONLY` | Byte-preserving recovery copy | `local/backups/` | Ignored; hash manifest required |
| `PROTECTED_UNRELATED_PROJECT` | Other user's or unrelated project material | Original location | Do not inspect, move, or change |
| `UNKNOWN_REVIEW_REQUIRED` | Material whose ownership or purpose is not established | Quarantine only after planning | Never delete by assumption |

## Canonical layout

`local/cache/`, `local/firmware/`, `local/toolchains/`, `local/sources/`, `local/artifacts/`, `local/logs/`, `local/backups/`, and `local/quarantine/` are reserved for local-only material. All are ignored by `.gitignore` where they contain raw or recoverable data. The committed `local-manifest.json` records what exists outside the checkout and why.

## Preservation before cleanup

No material is deleted merely because its name looks temporary. Before a deletion candidate is considered, all of the following must be true:

1. ownership is clearly this project;
2. the material is not shared, protected, or referenced by another workflow;
3. a byte-verified backup exists when the material is unique;
4. the canonical metadata records source, hash, and recovery instructions;
5. regeneration or recovery has been tested, or the material is proven redundant;
6. the exact target path is reviewed immediately before deletion.

If any item is uncertain, preserve the material externally or place it in `local/quarantine/` with a manifest. Mission 012-C deleted nothing because no candidate met this proof standard.

## Privacy and secrets

Do not commit serial numbers, user profiles, raw PnP logs, tokens, keys, credentials, phone dumps, proprietary firmware, or extracted vendor modules. Sanitize observations before committing them. Use `secret_scan.py`, `git diff --check`, and the full unit-test suite before every consolidation commit.

## Shared tools and WSL

Shared Platform Tools remain at their existing host path. WSL filesystems remain outside the repository and are not exported or modified by housekeeping. Any change to either is a separate host administration task.
