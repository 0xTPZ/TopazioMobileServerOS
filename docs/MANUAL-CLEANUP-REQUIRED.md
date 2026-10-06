# Manual cleanup record — Mission 012-E

Status: `COMPLETE`.

The six original trees below were revalidated on 2026-10-06. For every tree, the source and canonical destination have identical relative file sets, file counts, byte totals, timestamps, and SHA-256 values. The `C:\RedmiLabAudit` files also match `local/backups/mission-012c/sha256-manifest.json`.

The user subsequently executed the six exact restricted commands below manually. No protection was bypassed and no ACL was changed. Post-cleanup checks confirmed that every original path is absent and every canonical destination remains present. This file is retained as the historical approval and command record; cleanup pending is `0`.

## Approved candidates

| Original path | Canonical destination | Files | Bytes | Evidence |
| --- | --- | ---: | ---: | --- |
| `C:\RedmiLabAudit` | `E:\TopazioMobileServerOS\local\backups\mission-012c\redmi-lab-audit` | 13 | 9,077,833 | backup SHA-256 manifest + 012-D revalidation |
| `C:\Users\User\AppData\Local\Temp\topazio-mission009-cache` | `E:\TopazioMobileServerOS\local\cache\mission009` | 15 | 170,505,276 | 012-C migration record + 012-D full SHA-256 revalidation |
| `E:\TopazioMission010Cache` | `E:\TopazioMobileServerOS\local\cache\mission010` | 13 | 10,543,474 | 012-C migration record + 012-D full SHA-256 revalidation |
| `E:\TopazioMission011Cache` | `E:\TopazioMobileServerOS\local\cache\mission011` | 220 | 58,881,629 | 012-C migration record + 012-D full SHA-256 revalidation |
| `C:\Users\User\AppData\Local\Temp\topazio-mission012-raw` | `E:\TopazioMobileServerOS\local\logs\mission012` | 1 | 9,274 | 012-C migration record + 012-D full SHA-256 revalidation |
| `C:\Users\User\AppData\Local\Temp\topazio-mission012b-raw` | `E:\TopazioMobileServerOS\local\logs\mission012b` | 4 | 28 | 012-C migration record + 012-D full SHA-256 revalidation |

## Exact restricted commands

Run one command at a time. Do not replace a path with a wildcard or a broader parent directory.

```powershell
Remove-Item -LiteralPath 'C:\RedmiLabAudit' -Recurse -Force
Remove-Item -LiteralPath 'C:\Users\User\AppData\Local\Temp\topazio-mission009-cache' -Recurse -Force
Remove-Item -LiteralPath 'E:\TopazioMission010Cache' -Recurse -Force
Remove-Item -LiteralPath 'E:\TopazioMission011Cache' -Recurse -Force
Remove-Item -LiteralPath 'C:\Users\User\AppData\Local\Temp\topazio-mission012-raw' -Recurse -Force
Remove-Item -LiteralPath 'C:\Users\User\AppData\Local\Temp\topazio-mission012b-raw' -Recurse -Force
```

The commands were run one at a time, with the exact original paths and canonical destinations checked afterward. Do not remove `C:\AndroidTools\platform-tools`, any WSL distribution, `E:\TopazioMobileServerOS\local\`, its backup, or any protected/unrelated project.

All six originals were removed; the canonical local copies remain intact. Files removed from the six duplicate source trees: 266. Bytes reclaimed: 249,017,514. No cleanup action remains pending.
