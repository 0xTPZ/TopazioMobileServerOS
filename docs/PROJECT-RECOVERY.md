# Project recovery runbook

This runbook reconstructs the safe host state after a checkout, disk migration, or workstation replacement. It does not unlock, flash, erase, write to, or otherwise modify a phone.

## 1. Restore the canonical checkout

Clone or open `E:\TopazioMobileServerOS` and confirm that `main` points to the expected remote. The Mission 012-C completion gate requires a clean working tree and `HEAD == origin/main`.

Run the repository-only checks:

```powershell
python host-tools/verify_repo.py
python host-tools/secret_scan.py --working-tree
python -m unittest discover -s tests -v
git diff --check
```

## 2. Restore external host tools

Keep Android Platform Tools at `C:\AndroidTools\platform-tools`, or record the deliberate replacement path in the local manifest. Verify the package version and the hashes in `EXTERNAL-DEPENDENCIES.md`; do not copy the binaries into Git.

The official download source is the Android Developers Platform Tools page. A replacement package must be re-inventoried before it is used by later missions.

## 3. Restore historical evidence

If the local backup was carried separately, restore it to:

`E:\TopazioMobileServerOS\local\backups\mission-012c\redmi-lab-audit`

Validate every file against `local/backups/mission-012c/sha256-manifest.json`. If the original `C:\RedmiLabAudit` is retained, compare both copies before considering any future cleanup. The raw audit should remain local-only.

## 4. Restore or regenerate caches

Mission 009, 010, and 011 caches are not part of the Git checkout. Prefer regenerating them from the recorded public source, URL, commit, and hash metadata. If a cache is restored from a disk backup, keep it at its documented external path and verify the hashes before use. Never add raw `.img`, `.bin`, `.dtb`, `.ko`, OTA, or proprietary vendor files to Git.

## 5. WSL build environment

Use the existing `Ubuntu-24.04` WSL 2 distribution according to `docs/BUILD.md`. Do not import, export, or modify WSL distributions as part of repository recovery. If the distribution is missing, treat its recreation as a separate host-setup task.

## 6. Physical-device boundary

The last known state is partial hardware identification: Windows observed a Redmi Note 12S/SEA history, but the live transport probe had no ADB or fastboot device. Mission 012-C intentionally performed no device transport call. Any future transport work must be explicitly scoped as a new mission with its own read-only gate and recovery plan.

## 7. Backup verification

The canonical Git repository is reproducible source. Local-only material is recoverable only from an external disk backup or the preserved `local/backups` directory; it is intentionally ignored. Before disk maintenance, rerun the SHA-256 manifest checks, capture free space for C: and E:, and record the result in a new dated report.
