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
python host-tools/firmware_forensics.py fdt <dtb-or-overlay.dtb>
python host-tools/firmware_forensics.py payload <payload.bin>
python host-tools/firmware_forensics/acquire.py <url> <cache/package> --provenance <cache/package.json>
python host-tools/firmware_forensics/acquire.py <url> <cache/range> --range-start 0 --range-end 1048575
python host-tools/firmware_forensics/acquire.py <url> <cache/package> --resume
```

Extraction output must remain in an ignored host cache. Proprietary firmware is
never copied into Git; reports retain only metadata, hashes and conclusions.
Payload parsing is metadata-only: it inventories partition operations and
dynamic-partition metadata but never applies an OTA or writes to a device.
