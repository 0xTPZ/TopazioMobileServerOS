"""Platform-tools discovery without PATH mutation or automatic downloads."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil


DEFAULT_PLATFORM_TOOLS = Path(r"C:\AndroidTools\platform-tools")


@dataclass(frozen=True)
class ToolSelection:
    name: str
    path: str | None
    source: str

    @property
    def available(self) -> bool:
        return self.path is not None


def discover_tool(name: str, *, explicit: str | None = None, platform_tools: Path | None = None) -> ToolSelection:
    """Choose explicit path, PATH, then the documented local fallback."""

    if explicit:
        candidate = Path(explicit)
        if candidate.is_file():
            return ToolSelection(name, str(candidate.resolve()), "explicit")
        return ToolSelection(name, None, "explicit_missing")
    path_value = shutil.which(name)
    if path_value:
        return ToolSelection(name, str(Path(path_value).resolve()), "PATH")
    root = platform_tools or Path(os.environ.get("TOPAZIO_PLATFORM_TOOLS", DEFAULT_PLATFORM_TOOLS))
    candidate = root / f"{name}.exe"
    if candidate.is_file():
        return ToolSelection(name, str(candidate.resolve()), "documented_local_path")
    return ToolSelection(name, None, "not_found")


def discover_tools(*, adb: str | None = None, fastboot: str | None = None, platform_tools: Path | None = None) -> dict[str, ToolSelection]:
    return {
        "adb": discover_tool("adb", explicit=adb, platform_tools=platform_tools),
        "fastboot": discover_tool("fastboot", explicit=fastboot, platform_tools=platform_tools),
    }
