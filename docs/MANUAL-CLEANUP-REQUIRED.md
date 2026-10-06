# Manual cleanup required — Mission 012-D

Status: `COMPLETE_EXCEPT_MANUAL_CLEANUP`.

The six original trees below were revalidated on 2026-10-06. For every tree, the source and canonical destination have identical relative file sets, file counts, byte totals, timestamps, and SHA-256 values. The `C:\RedmiLabAudit` files also match `local/backups/mission-012c/sha256-manifest.json`.

The host blocked the first explicit `Remove-Item` call before execution. No protection was bypassed, no ACL was changed, and no source was removed. The commands below are intentionally separate and exact; run them manually only if the user wants to perform this final cleanup with the required Windows privilege.

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

After each command, confirm that its exact original path no longer exists and that the canonical destination still exists. If any command fails or any comparison changes, stop and leave the remaining candidates intact. Do not remove `C:\AndroidTools\platform-tools`, any WSL distribution, `E:\TopazioMobileServerOS\local\`, its backup, or any protected/unrelated project.

The six originals currently remain because the host denied the removal operation; current reclaimed bytes are zero.
