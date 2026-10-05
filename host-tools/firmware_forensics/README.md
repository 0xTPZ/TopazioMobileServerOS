# Offline firmware forensics toolkit

This toolkit is intentionally host-only. It reads local archives and image
files, computes hashes, and emits JSON. It has no USB, ADB, fastboot, flash,
erase, unlock, or device-write integration.

Examples:

```text
python host-tools/firmware_forensics.py inventory <package.zip>
python host-tools/firmware_forensics.py boot <boot.img> --extract-dir <cache/parts>
python host-tools/firmware_forensics.py dtbo <dtbo.img>
python host-tools/firmware_forensics.py vbmeta <vbmeta.img>
python host-tools/firmware_forensics/acquire.py <url> <cache/package> --provenance <cache/package.json>
```

Extraction output must remain in an ignored host cache. Proprietary firmware is
never copied into Git; reports retain only metadata, hashes and conclusions.
