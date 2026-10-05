"""Fail-closed, sanitized physical SEA inventory helpers."""

from .collector import DeviceInventory
from .report import build_observation

__all__ = ["DeviceInventory", "build_observation"]
