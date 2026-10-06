# Disk report — Mission 012-E closeout

Captured on 2026-10-06 (America/Sao_Paulo). Values are Windows `Get-PSDrive` byte counters.

## Before preservation

| Volume | Used bytes | Free bytes |
| --- | ---: | ---: |
| `C:` | 203,566,874,624 | 36,248,547,328 |
| `E:` | 135,291,731,968 | 864,384,970,752 |

The pre-preservation project tree was measured at approximately 2,586,613,766 bytes. The exact method included the generated build tree and is retained as a baseline for this pass.

## After preservation and canonical copy

| Volume | Used bytes | Free bytes | Delta used |
| --- | ---: | ---: | ---: |
| `C:` | 203,252,379,648 | 36,563,238,912 | -314,494,976 |
| `E:` | 133,502,304,256 | 866,174,398,464 | -1,789,427,712 |

The canonical local copy contains 266 migrated payload files and 249,017,514 bytes; with its one local manifest file, `local/` contains 267 files and 249,019,935 bytes. The complete working tree, excluding `.git` metadata, currently measures 545 files and 2,835,120,649 bytes, including ignored local material and the cleanup record. Mission 012-E revalidated all six approved source/destination pairs by file set, count, bytes, timestamps, and SHA-256, then confirmed all six original paths were removed manually while all canonical destinations remained present.

## Interpretation

The consolidation added a verified local recovery copy and documentation, then removed the six verified duplicate source trees. Bytes liberated: 249,017,514 across 266 files. Bytes preserved in canonical local storage: 249,017,514 payload bytes (249,019,935 bytes including the local manifest). Shared dependencies remaining outside the workspace are Platform Tools and WSL; no known project-owned path remains outside the workspace.
