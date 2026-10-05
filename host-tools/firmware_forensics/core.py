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
PAYLOAD_MAGIC = b"CrAU"


_PAYLOAD_OPERATION_TYPES = {
    0: "REPLACE",
    1: "REPLACE_BZ",
    2: "MOVE",
    3: "BSDIFF",
    4: "SOURCE_COPY",
    5: "SOURCE_BSDIFF",
    6: "ZERO",
    7: "DISCARD",
    8: "REPLACE_XZ",
    9: "PUFFDIFF",
    10: "BROTLI_BSDIFF",
    11: "ZUCCHINI",
    12: "LZ4DIFF_BSDIFF",
    13: "LZ4DIFF_PUFFDIFF",
}


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while True:
        if offset >= len(data) or shift >= 64:
            raise ValueError("truncated protobuf varint")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7


def _protobuf_fields(data: bytes) -> list[tuple[int, int, int | bytes]]:
    """Parse the wire types needed by Android update_metadata.proto."""

    fields: list[tuple[int, int, int | bytes]] = []
    offset = 0
    while offset < len(data):
        key, offset = _read_varint(data, offset)
        number, wire_type = key >> 3, key & 0x07
        if number <= 0:
            raise ValueError("invalid protobuf field number")
        if wire_type == 0:
            value, offset = _read_varint(data, offset)
        elif wire_type == 1:
            value = data[offset : offset + 8]
            if len(value) != 8:
                raise ValueError("truncated protobuf fixed64")
            offset += 8
        elif wire_type == 2:
            length, offset = _read_varint(data, offset)
            value = data[offset : offset + length]
            if len(value) != length:
                raise ValueError("truncated protobuf bytes")
            offset += length
        elif wire_type == 5:
            value = data[offset : offset + 4]
            if len(value) != 4:
                raise ValueError("truncated protobuf fixed32")
            offset += 4
        else:
            raise ValueError(f"unsupported protobuf wire type: {wire_type}")
        fields.append((number, wire_type, value))
    return fields


def _protobuf_values(data: bytes, field_number: int) -> list[int | bytes]:
    return [value for number, _wire_type, value in _protobuf_fields(data) if number == field_number]


def _protobuf_one(data: bytes, field_number: int, default: Any = None) -> Any:
    values = _protobuf_values(data, field_number)
    return values[0] if values else default


def _parse_payload_extent(data: bytes) -> dict[str, int]:
    return {
        "start_block": int(_protobuf_one(data, 1, 0)),
        "num_blocks": int(_protobuf_one(data, 2, 0)),
    }


def _parse_partition_info(data: bytes | None) -> dict[str, Any] | None:
    if data is None:
        return None
    raw_hash = _protobuf_one(data, 2, b"")
    return {
        "size_bytes": int(_protobuf_one(data, 1, 0)),
        "sha256": raw_hash.hex() if isinstance(raw_hash, bytes) and raw_hash else None,
    }


def _parse_payload_operation(data: bytes) -> dict[str, Any]:
    raw_type = int(_protobuf_one(data, 1, 0))
    raw_hash = _protobuf_one(data, 8, b"")
    return {
        "type": _PAYLOAD_OPERATION_TYPES.get(raw_type, f"UNKNOWN_{raw_type}"),
        "type_value": raw_type,
        "data_offset": int(_protobuf_one(data, 2, 0)),
        "data_length": int(_protobuf_one(data, 3, 0)),
        "src_extents": [_parse_payload_extent(item) for item in _protobuf_values(data, 4)],
        "src_length": int(_protobuf_one(data, 5, 0)),
        "dst_extents": [_parse_payload_extent(item) for item in _protobuf_values(data, 6)],
        "dst_length": int(_protobuf_one(data, 7, 0)),
        "data_sha256": raw_hash.hex() if isinstance(raw_hash, bytes) and raw_hash else None,
        "src_sha256": (
            _protobuf_one(data, 9, b"").hex()
            if isinstance(_protobuf_one(data, 9, b""), bytes) and _protobuf_one(data, 9, b"")
            else None
        ),
    }


def _parse_dynamic_partition_metadata(data: bytes) -> dict[str, Any]:
    groups = []
    for group in _protobuf_values(data, 1):
        groups.append(
            {
                "name": bytes(_protobuf_one(group, 1, b"")).decode("utf-8", "replace"),
                "size_bytes": int(_protobuf_one(group, 2, 0)),
                "partition_names": [
                    bytes(item).decode("utf-8", "replace") for item in _protobuf_values(group, 3)
                ],
            }
        )
    return {
        "groups": groups,
        "snapshot_enabled": bool(_protobuf_one(data, 2, False)),
        "vabc_enabled": bool(_protobuf_one(data, 3, False)),
        "vabc_compression_param": bytes(_protobuf_one(data, 4, b"")).decode("utf-8", "replace"),
        "cow_version": int(_protobuf_one(data, 5, 0)),
    }


def parse_update_payload(data: bytes, source: str | None = None) -> dict[str, Any]:
    """Parse an Android update_engine payload manifest without applying it."""

    if len(data) < 20 or data[:4] != PAYLOAD_MAGIC:
        raise ValueError("missing CrAU payload magic or truncated header")
    major_version, manifest_size = struct.unpack_from(">QQ", data, 4)
    if major_version >= 2 and len(data) < 24:
        raise ValueError("truncated payload v2 header")
    metadata_signature_size = struct.unpack_from(">I", data, 20)[0] if major_version >= 2 else 0
    manifest_offset = 24 if major_version >= 2 else 20
    manifest_end = manifest_offset + manifest_size
    signature_end = manifest_end + metadata_signature_size
    if signature_end > len(data):
        raise ValueError("payload metadata is truncated")
    manifest = data[manifest_offset:manifest_end]
    top = _protobuf_fields(manifest)
    partitions = []
    for _number, _wire_type, raw_partition in top:
        if _number != 13 or not isinstance(raw_partition, bytes):
            continue
        partition_name = bytes(_protobuf_one(raw_partition, 1, b"")).decode("utf-8", "replace")
        operations = [
            _parse_payload_operation(item) for item in _protobuf_values(raw_partition, 8)
        ]
        partitions.append(
            {
                "name": partition_name,
                "old_partition_info": _parse_partition_info(
                    _protobuf_one(raw_partition, 6, None)
                ),
                "new_partition_info": _parse_partition_info(
                    _protobuf_one(raw_partition, 7, None)
                ),
                "operations": operations,
                "operation_count": len(operations),
                "data_bytes": sum(item["data_length"] for item in operations),
                "operation_types": sorted({item["type"] for item in operations}),
                "requires_source_partition": any(item["src_extents"] for item in operations),
            }
        )
    dynamic_raw = _protobuf_one(manifest, 15, None)
    dynamic = (
        _parse_dynamic_partition_metadata(dynamic_raw)
        if isinstance(dynamic_raw, bytes)
        else None
    )
    return {
        "source": source,
        "magic": PAYLOAD_MAGIC.decode("ascii"),
        "major_version": major_version,
        "manifest_size_bytes": manifest_size,
        "metadata_signature_size_bytes": metadata_signature_size,
        "metadata_size_bytes": signature_end,
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "data_area_offset": signature_end,
        "block_size": int(_protobuf_one(manifest, 3, 4096)),
        "signatures_offset": int(_protobuf_one(manifest, 4, 0)),
        "signatures_size": int(_protobuf_one(manifest, 5, 0)),
        "minor_version": int(_protobuf_one(manifest, 12, 0)),
        "max_timestamp": int(_protobuf_one(manifest, 14, 0)),
        "partial_update": bool(_protobuf_one(manifest, 16, False)),
        "security_patch_level": bytes(_protobuf_one(manifest, 18, b"")).decode("utf-8", "replace"),
        "dynamic_partition_metadata": dynamic,
        "is_full_payload": not any(item["old_partition_info"] for item in partitions),
        "partitions": partitions,
        "partition_names": [item["name"] for item in partitions],
        "payload_signature_range": {
            "offset_from_data_area": int(_protobuf_one(manifest, 4, 0)),
            "size_bytes": int(_protobuf_one(manifest, 5, 0)),
        },
    }


def parse_update_payload_file(path: Path) -> dict[str, Any]:
    """Read only the header, manifest and metadata signature from a payload."""

    path = path.resolve()
    with path.open("rb") as stream:
        header_prefix = stream.read(20)
        if len(header_prefix) < 20 or header_prefix[:4] != PAYLOAD_MAGIC:
            raise ValueError("missing CrAU payload magic or truncated header")
        major_version, manifest_size = struct.unpack_from(">QQ", header_prefix, 4)
        signature_header = stream.read(4) if major_version >= 2 else b""
        if major_version >= 2 and len(signature_header) != 4:
            raise ValueError("truncated payload metadata signature size")
        signature_size = struct.unpack(">I", signature_header)[0] if major_version >= 2 else 0
        header_size = 24 if major_version >= 2 else 20
        metadata = header_prefix + signature_header + stream.read(manifest_size + signature_size)
    if len(metadata) != (24 if major_version >= 2 else 20) + manifest_size + signature_size:
        raise ValueError("payload metadata file is truncated")
    return parse_update_payload(metadata, str(path))


def parse_ota_properties(data: bytes | str) -> dict[str, str]:
    """Parse the line-oriented META-INF/com/android/metadata contract."""

    text = data.decode("utf-8", "replace") if isinstance(data, bytes) else data
    properties: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            properties[key.strip()] = value.strip()
    return properties


def parse_fdt(data: bytes, source: str | None = None) -> dict[str, Any]:
    """Read a flattened device-tree header and structural summary."""

    if len(data) < 40 or data[:4] != b"\xd0\x0d\xfe\xed":
        raise ValueError("missing FDT magic")
    (
        _magic,
        total_size,
        structure_offset,
        strings_offset,
        reserved_offset,
        version,
        last_compatible,
        boot_cpuid,
        strings_size,
        structure_size,
    ) = struct.unpack_from(">10I", data, 0)
    if total_size > len(data) or structure_offset + structure_size > total_size:
        raise ValueError("invalid FDT bounds")
    strings = data[strings_offset : strings_offset + strings_size]
    properties: list[dict[str, Any]] = []
    nodes: list[str] = []
    cursor = structure_offset
    end = structure_offset + structure_size
    while cursor + 4 <= end:
        token = struct.unpack_from(">I", data, cursor)[0]
        cursor += 4
        if token == 1:  # FDT_BEGIN_NODE
            name_end = data.find(b"\x00", cursor, end)
            if name_end < 0:
                raise ValueError("unterminated FDT node name")
            nodes.append(data[cursor:name_end].decode("utf-8", "replace"))
            cursor = align(name_end + 1, 4)
        elif token == 2:  # FDT_END_NODE
            if nodes:
                nodes.pop()
        elif token == 3:  # FDT_PROP
            if cursor + 8 > end:
                raise ValueError("truncated FDT property")
            length, name_offset = struct.unpack_from(">II", data, cursor)
            cursor += 8
            value = data[cursor : cursor + length]
            cursor = align(cursor + length, 4)
            name_end = strings.find(b"\x00", name_offset)
            if name_offset >= len(strings) or name_end < 0:
                raise ValueError("invalid FDT property name offset")
            properties.append(
                {
                    "path": "/" + "/".join(nodes),
                    "name": strings[name_offset:name_end].decode("utf-8", "replace"),
                    "size_bytes": length,
                    "sha256": hashlib.sha256(value).hexdigest(),
                    "text": value.rstrip(b"\x00").decode("utf-8", "replace")
                    if b"\x00" in value or all(32 <= byte < 127 or byte in (9, 10, 13) for byte in value)
                    else None,
                }
            )
        elif token == 4:  # FDT_NOP
            continue
        elif token == 9:  # FDT_END
            break
        else:
            raise ValueError(f"unknown FDT token: {token}")
    return {
        "source": source,
        "magic": "d00dfeed",
        "total_size": total_size,
        "structure_offset": structure_offset,
        "strings_offset": strings_offset,
        "reserved_map_offset": reserved_offset,
        "version": version,
        "last_compatible_version": last_compatible,
        "boot_cpuid_phys": boot_cpuid,
        "strings_size": strings_size,
        "structure_size": structure_size,
        "node_count": len({item["path"] for item in properties}),
        "properties": properties,
        "parse_complete": cursor <= end,
    }


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


def parse_vendor_boot(image: Path) -> dict[str, Any]:
    """Parse the common vendor_boot v3/v4 header and component boundaries."""

    image = image.resolve()
    data = image.read_bytes()
    if len(data) < 40 or data[:8] != b"VNDRBOOT":
        raise ValueError("missing VNDRBOOT vendor_boot magic")
    header_version, page_size, vendor_ramdisk_size, ramdisk_addr, tags_addr, header_size, dtb_size = struct.unpack_from(
        "<7I", data, 8
    )
    dtb_addr = struct.unpack_from("<Q", data, 36)[0]
    vendor_ramdisk_offset = page_size
    dtb_offset = align(vendor_ramdisk_offset + vendor_ramdisk_size, page_size)
    return {
        "path": str(image),
        "file_size_bytes": len(data),
        "magic": "VNDRBOOT",
        "header_version": header_version,
        "page_size": page_size,
        "header_size": header_size,
        "vendor_ramdisk": {
            "offset": vendor_ramdisk_offset,
            "size_bytes": vendor_ramdisk_size,
            "bounds_valid": vendor_ramdisk_offset + vendor_ramdisk_size <= len(data),
        },
        "dtb": {
            "offset": dtb_offset,
            "size_bytes": dtb_size,
            "address": dtb_addr,
            "bounds_valid": dtb_offset + dtb_size <= len(data),
        },
        "addresses": {"ramdisk": ramdisk_addr, "tags": tags_addr},
        "vendor_bootconfig_status": "HEADER_VERSION_DEPENDENT",
    }


def compare_dt_semantics(
    stock: dict[str, Any] | None, experimental: dict[str, Any] | None
) -> dict[str, Any]:
    """Compare parsed FDT property identities, failing closed without stock DT."""

    if not stock or not experimental:
        return {
            "status": "BLOCKED_NO_STOCK_REFERENCE",
            "overall_score": None,
            "subsystems": {},
        }
    stock_names = {item["name"] for item in stock.get("properties", [])}
    experimental_names = {item["name"] for item in experimental.get("properties", [])}
    union = stock_names | experimental_names
    score = len(stock_names & experimental_names) / len(union) if union else 1.0
    subsystem_keywords = {
        "cpu": ("cpu", "opp"),
        "ram": ("memory", "reserved-memory", "cma"),
        "ufs": ("ufs", "ufshci"),
        "usb": ("usb", "typec", "phy"),
        "wifi": ("wifi", "wlan"),
        "pmic": ("pmic", "regulator", "charger"),
        "thermal": ("thermal", "cooling"),
        "display": ("dsi", "panel", "display"),
        "touch": ("touch", "focal", "ft5"),
    }
    subsystem_scores = {}
    for subsystem, keywords in subsystem_keywords.items():
        stock_subset = {name for name in stock_names if any(key in name.lower() for key in keywords)}
        experimental_subset = {
            name for name in experimental_names if any(key in name.lower() for key in keywords)
        }
        local_union = stock_subset | experimental_subset
        subsystem_scores[subsystem] = (
            len(stock_subset & experimental_subset) / len(local_union) if local_union else None
        )
    return {
        "status": "COMPARED_PROPERTY_IDENTITY",
        "overall_score": score,
        "subsystems": subsystem_scores,
        "stock_property_count": len(stock_names),
        "experimental_property_count": len(experimental_names),
    }


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
        3: "kernel_cmdline",
        4: "chain_partition",
    }.get(tag, f"unknown_{tag}")


def _parse_avb_descriptor(tag: int, payload: bytes) -> dict[str, Any]:
    details: dict[str, Any] = {}
    if tag == 0 and len(payload) >= 16:
        key_size, value_size = struct.unpack_from(">QQ", payload, 0)
        key_start = 16
        value_start = key_start + key_size
        details = {
            "key": payload[key_start:value_start].strip(b"\x00").decode("utf-8", "replace"),
            "value": payload[value_start : value_start + value_size]
            .strip(b"\x00")
            .decode("utf-8", "replace"),
        }
    elif tag == 2 and len(payload) >= 116:
        image_size, hash_algorithm, partition_name_size, salt_size, digest_size, flags = struct.unpack_from(
            ">Q32sIIII", payload, 0
        )
        cursor = 116
        details = {
            "image_size_bytes": image_size,
            "hash_algorithm": hash_algorithm.rstrip(b"\x00").decode("ascii", "replace"),
            "partition_name": payload[cursor : cursor + partition_name_size]
            .rstrip(b"\x00")
            .decode("utf-8", "replace"),
            "salt_size_bytes": salt_size,
            "digest_size_bytes": digest_size,
            "flags": flags,
        }
    elif tag == 1 and len(payload) >= 164:
        (
            dm_verity_version,
            image_size,
            tree_offset,
            tree_size,
            data_block_size,
            hash_block_size,
            fec_num_roots,
            fec_offset,
            fec_size,
            hash_algorithm,
            partition_name_size,
            salt_size,
            root_digest_size,
            flags,
        ) = struct.unpack_from(">IQQQIIIQQ32sIIII", payload, 0)
        cursor = 164
        details = {
            "dm_verity_version": dm_verity_version,
            "image_size_bytes": image_size,
            "tree_offset": tree_offset,
            "tree_size": tree_size,
            "data_block_size": data_block_size,
            "hash_block_size": hash_block_size,
            "fec_num_roots": fec_num_roots,
            "fec_offset": fec_offset,
            "fec_size": fec_size,
            "hash_algorithm": hash_algorithm.rstrip(b"\x00").decode("ascii", "replace"),
            "partition_name": payload[cursor : cursor + partition_name_size]
            .rstrip(b"\x00")
            .decode("utf-8", "replace"),
            "salt_size_bytes": salt_size,
            "root_digest_size_bytes": root_digest_size,
            "flags": flags,
        }
    elif tag == 4 and len(payload) >= 76:
        rollback_location, partition_name_size, public_key_size, flags = struct.unpack_from(">IIII", payload, 0)
        cursor = 76
        details = {
            "rollback_index_location": rollback_location,
            "flags": flags,
            "partition_name": payload[cursor : cursor + partition_name_size]
            .rstrip(b"\x00")
            .decode("utf-8", "replace"),
            "public_key_size_bytes": public_key_size,
        }
    elif tag == 3 and len(payload) >= 72:
        flags, cmdline_size = struct.unpack_from(">II", payload, 0)
        cursor = 72
        details = {
            "flags": flags,
            "cmdline": payload[cursor : cursor + cmdline_size]
            .rstrip(b"\x00")
            .decode("utf-8", "replace"),
        }
    return details


def parse_vbmeta_bytes(data: bytes, source: str | None = None) -> dict[str, Any]:
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
        tag, num_bytes_following = struct.unpack_from(">QQ", data, cursor)
        total_size = 16 + num_bytes_following
        if total_size < 16 or cursor + total_size > descriptor_end:
            break
        raw_descriptor = data[cursor : cursor + total_size]
        descriptors.append(
            {
                "tag": tag,
                "type": _descriptor_name(tag),
                "size_bytes": total_size,
                "num_bytes_following": num_bytes_following,
                "sha256": hashlib.sha256(raw_descriptor).hexdigest(),
                "details": _parse_avb_descriptor(tag, raw_descriptor[16:]),
            }
        )
        cursor += total_size
    return {
        "path": source,
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


def parse_vbmeta(image: Path) -> dict[str, Any]:
    image = image.resolve()
    return parse_vbmeta_bytes(image.read_bytes(), str(image))


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
