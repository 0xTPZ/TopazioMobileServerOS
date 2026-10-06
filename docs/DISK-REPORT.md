# Disk report — Mission 012-C

Captured on 2026-10-06 (America/Sao_Paulo). Values are Windows `Get-PSDrive` byte counters.

## Before preservation

| Volume | Used bytes | Free bytes |
| --- | ---: | ---: |
| `C:` | 203,566,874,624 | 36,248,547,328 |
| `E:` | 135,291,731,968 | 864,384,970,752 |

The pre-preservation project tree was measured at approximately 2,586,613,766 bytes. The exact method included the generated build tree and is retained as a baseline for this pass.

## After preservation

| Volume | Used bytes | Free bytes | Delta used |
| --- | ---: | ---: | ---: |
| `C:` | 203,559,927,808 | 36,255,690,752 | -6,946,816 |
| `E:` | 135,302,635,520 | 864,374,067,200 | +10,903,552 |

The local preservation copy contains 9,077,833 bytes. The small discrepancy in volume deltas is normal filesystem allocation and concurrent host activity; no cleanup deletion was performed. The current repository working tree measurement, excluding `.git` metadata, is 2,592,407,990 bytes; it includes the ignored local backup.

## Interpretation

The consolidation added a verified local recovery copy and documentation. It did not reclaim space because deletion of any external cache or evidence was not proven safe. Raw firmware caches remain documented external material and can be handled by a later, separately approved retention decision.
