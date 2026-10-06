# External dependencies and recovery points

This document records material that must remain outside Git but is required to reproduce or interpret the current project state.

## Android Platform Tools

Path: `C:\AndroidTools\platform-tools`

Observed package: `adb`/`fastboot` version `37.0.1-15733141`, Windows x64. The directory contains 14 files and 17,529,398 bytes. Relevant hashes:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `adb.exe` | 8,273,560 | `B4A6B455702684652CCCF7B46258B29E653538904359A58FD4931CF3EF286B3F` |
| `fastboot.exe` | 2,429,080 | `B2D9CBFF4CE9AE7EB448CFC831BAFC867935F50F5BE38F8F81057FD7EB3B8D86` |
| `source.properties` | 38 | `2DCCD788C0234D8CF7F7457377E57F57527A86A629C6ED54FEB8AF0F549DAC38` |

Keep this installation external because it is shared by other Android work. If it is absent on a new host, obtain Platform Tools from the official Android Developers page and update the local inventory after verifying the package version and hashes: <https://developer.android.com/tools/releases/platform-tools>.

Mission 012-C did not address a phone with ADB or fastboot. The last known transport result remains the sanitized Mission 012-B observation: both device lists were empty.

## Historical Redmi audit and local caches

The project-owned historical audit is preserved canonically at `E:\TopazioMobileServerOS\local\backups\mission-012c\redmi-lab-audit` with 13 files and 9,077,833 bytes. It includes the report, command history, a failed HTML download saved with a `.zip` suffix, and an extracted Google USB driver package that did not match the live MediaTek hardware ID.

The exact byte-identical local preservation is at:

`E:\TopazioMobileServerOS\local\backups\mission-012c\redmi-lab-audit`

Its SHA-256 manifest is at `local/backups/mission-012c/sha256-manifest.json`. The directory is ignored, and the raw report is not committed because it contains device/local-environment identifiers. The original `C:\RedmiLabAudit` was removed manually after the exact duplicate was revalidated.

## Mission caches

| Path | Files | Bytes | Interpretation |
| --- | ---: | ---: | --- |
| `E:\TopazioMobileServerOS\local\cache\mission009` | 15 | 170,505,276 | OTA/boot image and extracted kernel/ramdisk material |
| `E:\TopazioMobileServerOS\local\cache\mission010` | 13 | 10,543,474 | DTBO/vbmeta analysis and operation fragments |
| `E:\TopazioMobileServerOS\local\cache\mission011` | 220 | 58,881,629 | vendor_dlkm image, extraction, and kernel modules |
| `E:\TopazioMobileServerOS\local\logs\mission012` | 1 | 9,274 | Host audit JSON |
| `E:\TopazioMobileServerOS\local\logs\mission012b` | 4 | 28 | Empty/short transport command outputs |

These are canonical local-only, ignored, and documented rather than copied into Git. The repository already contains the analytical metadata and hashes needed to identify them. Their original C:/E: trees were copied and verified file-by-file, then removed manually after the Mission 012-E cleanup gate. No duplicate cleanup remains pending.

No separate `mt6781`, `k6781`, `sea-t-oss`, firmware, OTA, or toolchain checkout was adopted from the permitted C:/E: scan. The tracked repository is the source for reconstruction metadata; WSL Ubuntu 24.04 is the documented build environment. Other Topazio-named folders and independent Git repositories were classified as unrelated and were not made dependencies.

## WSL

The host has WSL 2 with stopped distributions `Ubuntu-24.04`, `Zelvya-Dev`, and `Alice-DB-Test`. The project build documentation uses Ubuntu 24.04, but Mission 012-C did not enter, enumerate, export, or modify any WSL filesystem. WSL distributions remain external dependencies and project boundaries.
