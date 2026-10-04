"""Plan and validate a device artifact package without synthesizing boot images."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from device_manifest import load_manifest


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def plan(manifest: dict[str, Any], inputs: dict[str, Path | None]) -> dict[str, Any]:
    missing = [name for name, path in inputs.items() if path is None or not path.is_file()]
    if manifest.get("support_state") == "RESEARCH" or manifest.get("installable") is not True:
        missing.append("DSP_not_installable")
    return {
        "device": f"{manifest.get('vendor')}-{manifest.get('codename')}",
        "status": "READY_TO_PACKAGE" if not missing else "BLOCKED",
        "missing": missing,
        "writes_to_device": False,
        "policy": "inputs are copied only after explicit paths and hashes exist; no boot image is synthesized",
    }


def package(output: Path, manifest: dict[str, Any], inputs: dict[str, Path]) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    artifacts = [{"name": name, "path": str(path), "sha256": sha256(path), "size": path.stat().st_size}
                 for name, path in inputs.items()]
    result = {"schema": 1, "device": "xiaomi-sea", "status": "PACKAGED", "artifacts": artifacts,
              "writes_to_device": False}
    (output / "boot-artifacts.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate explicit sea artifacts without creating a boot image")
    parser.add_argument("--manifest", type=Path, default=Path("devices/xiaomi-sea/device.json"))
    parser.add_argument("--kernel", type=Path)
    parser.add_argument("--dtb", type=Path)
    parser.add_argument("--boot-image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("build/out/devices/xiaomi-sea"))
    parser.add_argument("--package", action="store_true")
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    inputs = {"kernel": args.kernel, "dtb": args.dtb, "boot_image": args.boot_image}
    result = plan(manifest, inputs)
    if args.package and result["status"] == "READY_TO_PACKAGE":
        result = package(args.output, manifest, {name: path for name, path in inputs.items() if path is not None})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"READY_TO_PACKAGE", "PACKAGED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
