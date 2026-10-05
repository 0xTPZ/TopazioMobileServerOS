"""Format-aware, offline-only firmware inspection primitives."""

from __future__ import annotations

import hashlib
import gzip
import json
import struct
import tarfile
import zipfile
from pathlib import Path
from typing import Any, BinaryIO


ANDROID_MAGIC = b"ANDROID!"
DT_TABLE_MAGIC = 0xD7B7AB1E
AVB_MAGIC = b"AVB0"


def sha256_path(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def md5_path(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def align(value: int, alignment: int) -> int:
    return (value + alignment - 1) // alignment * alignment


def compression_from_magic(data: bytes) -> str:
    if data.startswith(b"\x1f\x8b"):
        return "gzip"
    if data.startswith(b"\x02\x21\x4c\x18"):
        return "lz4-android"
    if data.startswith(b"\xfd7zXZ\x00"):
        return "xz"
    if data.startswith(b"\x28\xb5\x2f\xfd"):
        return "zstd"
    if data.startswith(b"070701") or data.startswith(b"070702"):
        return "cpio-newc"
    return "unknown"


def _lz4_block_decompress(block: bytes) -> bytes:
    output = bytearray()
    cursor = 0
    while cursor < len(block):
        token = block[cursor]
        cursor += 1
        literal_length = token >> 4
        if literal_length == 15:
            while cursor < len(block) and block[cursor] == 255:
                literal_length += 255
                cursor += 1
            if cursor >= len(block):
                raise ValueError("truncated LZ4 literal length")
            literal_length += block[cursor]
            cursor += 1
        output.extend(block[cursor : cursor + literal_length])
        cursor += literal_length
        if cursor >= len(block):
            break
        if cursor + 2 > len(block):
            raise ValueError("truncated LZ4 match offset")
        match_offset = block[cursor] | (block[cursor + 1] << 8)
        cursor += 2
        if match_offset == 0 or match_offset > len(output):
            raise ValueError("invalid LZ4 match offset")
        match_length = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while cursor < len(block) and block[cursor] == 255:
                match_length += 255
                cursor += 1
            if cursor >= len(block):
                raise ValueError("truncated LZ4 match length")
            match_length += block[cursor]
            cursor += 1
        for _ in range(match_length):
            output.append(output[-match_offset])
    return bytes(output)


def decompress_lz4_frame(data: bytes) -> bytes:
    if not data.startswith(b"\x02\x21\x4c\x18"):
        raise ValueError("missing LZ4 frame magic")
    # Android ramdisks commonly use the legacy LZ4 block wrapper: magic,
    # little-endian compressed size, then one LZ4 block.  It is not an LZ4F
    # frame even though it shares the four-byte magic.
    if data[4] >> 6 != 1:
        compressed_size = struct.unpack_from("<I", data, 4)[0]
        payload = data[8 : 8 + compressed_size]
        if len(payload) != compressed_size:
            raise ValueError("truncated legacy LZ4 payload")
        return _lz4_block_decompress(payload)
    if len(data) < 7:
        raise ValueError("truncated LZ4 frame header")
    flags = data[4]
    cursor = 6
    if flags & 0x08:
        cursor += 8
    if flags & 0x01:
        cursor += 4
    cursor += 1  # header checksum
    output = bytearray()
    while True:
        if cursor + 4 > len(data):
            raise ValueError("truncated LZ4 frame block size")
        block_size = struct.unpack_from("<I", data, cursor)[0]
        cursor += 4
        if block_size == 0:
            break
        raw = bool(block_size & 0x80000000)
        block_size &= 0x7FFFFFFF
        block = data[cursor : cursor + block_size]
        if len(block) != block_size:
            raise ValueError("truncated LZ4 frame block")
        output.extend(block if raw else _lz4_block_decompress(block))
        cursor += block_size
    if flags & 0x04:
        if cursor + 4 > len(data):
            raise ValueError("truncated LZ4 content checksum")
        cursor += 4
    return bytes(output)


def _cpio_newc_inventory(data: bytes) -> dict[str, Any]:
    entries = []
    cursor = 0
    while cursor + 110 <= len(data):
        magic = data[cursor : cursor + 6]
        if magic not in (b"070701", b"070702"):
            break
        namesize = int(data[cursor + 94 : cursor + 102], 16)
        filesize = int(data[cursor + 54 : cursor + 62], 16)
        name_start = cursor + 110
        name_end = name_start + namesize
        name = data[name_start : max(name_start, name_end - 1)].decode("utf-8", "replace")
        file_start = align(name_end, 4)
        entries.append({"name": name, "size_bytes": filesize})
        cursor = align(file_start + filesize, 4)
        if name == "TRAILER!!!":
            break
    return {
        "format": "cpio-newc",
        "entry_count": len(entries),
        "entries": entries,
        "parse_complete": bool(entries and entries[-1]["name"] == "TRAILER!!!"),
    }


def _cpio_text_metadata(data: bytes) -> dict[str, Any]:
    selected_properties: dict[str, str] = {}
    fstab_paths: list[str] = []
    cursor = 0
    while cursor + 110 <= len(data):
        magic = data[cursor : cursor + 6]
        if magic not in (b"070701", b"070702"):
            break
        namesize = int(data[cursor + 94 : cursor + 102], 16)
        filesize = int(data[cursor + 54 : cursor + 62], 16)
        name_start = cursor + 110
        name_end = name_start + namesize
        name = data[name_start : max(name_start, name_end - 1)].decode("utf-8", "replace")
        file_start = align(name_end, 4)
        body = data[file_start : file_start + filesize]
        if "fstab" in name.lower():
            fstab_paths.append(name)
        if name.endswith("build.prop") and filesize <= 1024 * 1024:
            for line in body.decode("utf-8", "replace").splitlines():
                if "=" not in line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                if key.startswith(("ro.product.bootimage.", "ro.bootimage.build.")):
                    selected_properties[key] = value
        cursor = align(file_start + filesize, 4)
        if name == "TRAILER!!!":
            break
    return {"selected_properties": selected_properties, "fstab_paths": fstab_paths}


def analyze_ramdisk(data: bytes) -> dict[str, Any]:
    compression = compression_from_magic(data[:32])
    result: dict[str, Any] = {
        "compressed_size_bytes": len(data),
        "compression": compression,
    }
    try:
        if compression == "gzip":
            uncompressed = gzip.decompress(data)
        elif compression == "lz4-android":
            uncompressed = decompress_lz4_frame(data)
        elif compression == "cpio-newc":
            uncompressed = data
        else:
            result["analysis_status"] = "COMPRESSION_UNSUPPORTED"
            return result
        result["uncompressed_size_bytes"] = len(uncompressed)
        result["sha256_uncompressed"] = hashlib.sha256(uncompressed).hexdigest()
        if uncompressed.startswith((b"070701", b"070702")):
            result["cpio"] = _cpio_newc_inventory(uncompressed)
            result["text_metadata"] = _cpio_text_metadata(uncompressed)
        else:
            result["analysis_status"] = "NOT_CPIO_NEWC"
    except (OSError, ValueError, EOFError) as error:
        result["analysis_status"] = "DECOMPRESSION_ERROR"
        result["error"] = str(error)
    return result


def analyze_kernel(data: bytes) -> dict[str, Any]:
    compression = compression_from_magic(data[:32])
    result: dict[str, Any] = {"compressed_size_bytes": len(data), "compression": compression}
    if compression != "gzip":
        result["analysis_status"] = "COMPRESSION_UNSUPPORTED"
        return result
    try:
        uncompressed = gzip.decompress(data)
        result["uncompressed_size_bytes"] = len(uncompressed)
        result["sha256_uncompressed"] = hashlib.sha256(uncompressed).hexdigest()
        marker = b"Linux version "
        start = uncompressed.find(marker)
        if start >= 0:
            end = uncompressed.find(b"\x00", start)
            result["linux_version_string"] = uncompressed[start : end if end >= 0 else start + 256].decode(
                "utf-8", "replace"
            )
        result["analysis_status"] = "DECOMPRESSED"
    except (OSError, EOFError) as error:
        result["analysis_status"] = "DECOMPRESSION_ERROR"
        result["error"] = str(error)
    return result


def decode_os_version(value: int) -> dict[str, int]:
    return {
        "raw": value,
        "major": (value >> 25) & 0x7F,
        "minor": (value >> 18) & 0x7F,
        "patch": (value >> 11) & 0x7F,
        "year": 2000 + ((value >> 4) & 0x7F),
        "month": value & 0xF,
    }


def _component(path: Path, offset: int, size: int, data: bytes) -> dict[str, Any]:
    payload = data[offset : offset + size]
    return {
        "offset": offset,
        "size_bytes": size,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "compression": compression_from_magic(payload[:32]),
    }


def _extract_component(
    image: Path, output_dir: Path, name: str, offset: int, size: int
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / name
    with image.open("rb") as source, destination.open("wb") as target:
        source.seek(offset)
        remaining = size
        while remaining:
            block = source.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError(f"unexpected EOF while extracting {name}")
            target.write(block)
            remaining -= len(block)
    return str(destination)


def parse_android_boot(image: Path, extract_dir: Path | None = None) -> dict[str, Any]:
    """Parse Android boot image headers without changing the source image."""

    image = image.resolve()
    file_size = image.stat().st_size
    data = image.read_bytes()
    header = data[:4096]
    if not header.startswith(ANDROID_MAGIC):
        raise ValueError("missing ANDROID! boot image magic")

    header_version = struct.unpack_from("<I", header, 40)[0]
    result: dict[str, Any] = {
        "path": str(image),
        "file_size_bytes": file_size,
        "magic": ANDROID_MAGIC.decode("ascii"),
        "header_version": header_version,
        "format": "android-boot-img",
    }

    if header_version >= 3:
        kernel_size, ramdisk_size, os_version, header_size = struct.unpack_from(
            "<IIII", header, 8
        )
        page_size = 4096
        kernel_offset = page_size
        ramdisk_offset = align(kernel_offset + kernel_size, page_size)
        result.update(
            {
                "page_size": page_size,
                "header_size": header_size,
                "os_version": decode_os_version(os_version),
                "kernel": _component(image, kernel_offset, kernel_size, data),
                "kernel_analysis": analyze_kernel(data[kernel_offset : kernel_offset + kernel_size]),
                "ramdisk": _component(image, ramdisk_offset, ramdisk_size, data),
                "ramdisk_analysis": analyze_ramdisk(data[ramdisk_offset : ramdisk_offset + ramdisk_size]),
                "second_stage": None,
                "dtb": {
                    "status": "NOT_IN_BOOT_V3_HEADER",
                    "expected_location": "vendor_boot_or_separate_container",
                },
                "cmdline": {
                    "status": "NOT_IN_BOOT_V3_HEADER",
                    "expected_location": "vendor_boot_or_bootconfig",
                },
                "board": {"status": "NOT_IN_BOOT_V3_HEADER"},
            }
        )
    else:
        fields = struct.unpack_from("<10I", header, 8)
        kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size, second_addr, tags_addr, page_size, os_version, _unused = fields
        kernel_offset = page_size
        ramdisk_offset = align(kernel_offset + kernel_size, page_size)
        second_offset = align(ramdisk_offset + ramdisk_size, page_size)
        result.update(
            {
                "page_size": page_size,
                "header_size": 1632 if header_version >= 2 else 608,
                "os_version": decode_os_version(os_version),
                "addresses": {
                    "kernel": kernel_addr,
                    "ramdisk": ramdisk_addr,
                    "second": second_addr,
                    "tags": tags_addr,
                },
                "kernel": _component(image, kernel_offset, kernel_size, data),
                "kernel_analysis": analyze_kernel(data[kernel_offset : kernel_offset + kernel_size]),
                "ramdisk": _component(image, ramdisk_offset, ramdisk_size, data),
                "ramdisk_analysis": analyze_ramdisk(data[ramdisk_offset : ramdisk_offset + ramdisk_size]),
                "second_stage": (
                    _component(image, second_offset, second_size, data)
                    if second_size
                    else None
                ),
                "dtb": {"status": "HEADER_VERSION_DEPENDENT"},
                "cmdline": {"status": "LEGACY_HEADER_FIELD"},
            }
        )

    if extract_dir is not None:
        extracted: dict[str, str] = {}
        for name in ("kernel", "ramdisk"):
            component = result[name]
            extracted[name] = _extract_component(
                image, extract_dir, name, component["offset"], component["size_bytes"]
            )
        if result.get("second_stage"):
            component = result["second_stage"]
            extracted["second_stage"] = _extract_component(
                image, extract_dir, "second_stage", component["offset"], component["size_bytes"]
            )
        result["extracted"] = extracted
    return result


def _be_u32(data: bytes, offset: int) -> int:
    return struct.unpack_from(">I", data, offset)[0]


def parse_dtbo(image: Path) -> dict[str, Any]:
    data = image.read_bytes()
    if len(data) < 32 or _be_u32(data, 0) != DT_TABLE_MAGIC:
        raise ValueError("missing Android DT table magic")
    total_size, header_size, entry_size, entry_count, entries_offset, page_size, version = struct.unpack_from(
        ">7I", data, 4
    )
    if entry_size < 32 or entries_offset + entry_size * entry_count > len(data):
        raise ValueError("invalid DT table bounds")
    entries = []
    for index in range(entry_count):
        offset = entries_offset + index * entry_size
        dt_size, dt_offset, dt_id, rev, custom0, custom1, custom2, custom3 = struct.unpack_from(
            ">8I", data, offset
        )
        payload = data[dt_offset : dt_offset + dt_size]
        entries.append(
            {
                "index": index,
                "size_bytes": dt_size,
                "offset": dt_offset,
                "id": dt_id,
                "rev": rev,
                "custom": [custom0, custom1, custom2, custom3],
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bounds_valid": len(payload) == dt_size,
            }
        )
    return {
        "path": str(image.resolve()),
        "file_size_bytes": len(data),
        "magic": hex(DT_TABLE_MAGIC),
        "total_size": total_size,
        "header_size": header_size,
        "entry_size": entry_size,
        "entry_count": entry_count,
        "entries_offset": entries_offset,
        "page_size": page_size,
        "version": version,
        "entries": entries,
    }


def _descriptor_name(tag: int) -> str:
    return {
        0: "property",
        1: "hashtree",
        2: "hash",
        3: "chain_partition",
        4: "kernel_cmdline",
    }.get(tag, f"unknown_{tag}")


def parse_vbmeta(image: Path) -> dict[str, Any]:
    data = image.read_bytes()
    if len(data) < 256 or data[:4] != AVB_MAGIC:
        raise ValueError("missing AVB0 vbmeta magic")
    fields = struct.unpack_from(">IIQQIQQQQQQQQQQQII", data, 4)
    version_major, version_minor = fields[0:2]
    auth_size, aux_size, algorithm = fields[2:5]
    hash_offset, hash_size, signature_offset, signature_size = fields[5:9]
    public_key_offset, public_key_size, public_key_metadata_offset, public_key_metadata_size = fields[9:13]
    descriptors_offset, descriptors_size = fields[13:15]
    rollback_index, flags, rollback_location = fields[15:18]
    release = data[128:176].split(b"\x00", 1)[0].decode("utf-8", "replace")
    descriptor_start = 256 + auth_size + descriptors_offset
    descriptor_end = descriptor_start + descriptors_size
    descriptors = []
    cursor = descriptor_start
    while cursor + 16 <= descriptor_end and cursor + 16 <= len(data):
        tag, num_bytes = struct.unpack_from(">QQ", data, cursor)
        if num_bytes < 16 or cursor + num_bytes > descriptor_end:
            break
        descriptors.append(
            {
                "tag": tag,
                "type": _descriptor_name(tag),
                "size_bytes": num_bytes,
                "sha256": hashlib.sha256(data[cursor : cursor + num_bytes]).hexdigest(),
            }
        )
        cursor += num_bytes
    return {
        "path": str(image.resolve()),
        "file_size_bytes": len(data),
        "magic": AVB_MAGIC.decode("ascii"),
        "version": {"major": version_major, "minor": version_minor},
        "algorithm_type": algorithm,
        "authentication_data_block_size": auth_size,
        "auxiliary_data_block_size": aux_size,
        "hash": {"offset": hash_offset, "size_bytes": hash_size},
        "signature": {"offset": signature_offset, "size_bytes": signature_size},
        "public_key": {"offset": public_key_offset, "size_bytes": public_key_size},
        "public_key_metadata": {
            "offset": public_key_metadata_offset,
            "size_bytes": public_key_metadata_size,
        },
        "rollback_index": rollback_index,
        "flags": flags,
        "rollback_index_location": rollback_location,
        "release_string": release,
        "descriptors": descriptors,
        "descriptor_parse_complete": cursor == descriptor_end,
    }


def inventory_package(path: Path) -> dict[str, Any]:
    """Inventory archive metadata without extracting proprietary contents."""

    path = path.resolve()
    result: dict[str, Any] = {
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "sha256": sha256_path(path),
        "md5": md5_path(path),
        "type": "file",
        "entries": [],
    }
    lower = path.name.lower()
    if lower.endswith((".zip", ".ota")):
        result["type"] = "zip"
        with zipfile.ZipFile(path) as archive:
            result["entries"] = [
                {
                    "name": item.filename,
                    "size_bytes": item.file_size,
                    "compressed_size_bytes": item.compress_size,
                    "crc32": f"{item.CRC:08x}",
                }
                for item in archive.infolist()
            ]
    elif lower.endswith((".tgz", ".tar.gz", ".tar")):
        result["type"] = "tar"
        with tarfile.open(path, "r:*") as archive:
            result["entries"] = [
                {
                    "name": item.name,
                    "size_bytes": item.size,
                    "type": "directory" if item.isdir() else "file",
                }
                for item in archive.getmembers()
            ]
    result["known_names"] = {
        name: any(entry.get("name", "").lower().endswith(name) for entry in result["entries"])
        for name in (
            "boot.img",
            "vendor_boot.img",
            "init_boot.img",
            "dtbo.img",
            "vbmeta.img",
            "super.img",
            "payload.bin",
            "scatter.txt",
        )
    }
    return result


def dump_json(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
