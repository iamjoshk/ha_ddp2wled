"""Utility helpers for WLED connectivity and DDP device management."""
from __future__ import annotations

import json
import logging
import socket
import urllib.request
from typing import Dict, Tuple

from ..net.ddp_queue import DDPDevice

_LOGGER = logging.getLogger(__name__)


def check_ip_alive(ip_addr: str, port: int = 80, timeout: float = 1.0) -> bool:
    """Basic reachability check using TCP connect."""
    try:
        with socket.create_connection((ip_addr, port), timeout=timeout):
            return True
    except OSError as err:
        _LOGGER.debug("IP %s not reachable on port %d: %s", ip_addr, port, err)
        return False


def _http_get_json(ip_addr: str, path: str, timeout: float = 2.0) -> dict:
    url = f"http://{ip_addr}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_wled_info(ip_addr: str, timeout: float = 2.0) -> dict:
    """Fetch basic WLED info."""
    try:
        return _http_get_json(ip_addr, "/json/info", timeout=timeout)
    except Exception as err:
        _LOGGER.debug("Failed to fetch WLED info from %s: %s", ip_addr, err)
        return {}


def get_wled_matrix_dimensions(ip_addr: str, timeout: float = 2.0) -> Tuple[int | None, int | None]:
    """Return (width, height) for the 2D matrix if available."""
    info = get_wled_info(ip_addr, timeout=timeout)
    matrix = info.get("leds", {}).get("matrix") if isinstance(info, dict) else None
    if isinstance(matrix, dict):
        return matrix.get("w"), matrix.get("h")
    return None, None


def put_wled_live(ip_addr: str, timeout: float = 2.0) -> bool:
    """Put WLED into live mode to avoid losing control during streaming."""
    payload = json.dumps({"live": True}).encode("utf-8")
    url = f"http://{ip_addr}/json/state"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout):
            return True
    except Exception as err:
        _LOGGER.debug("Failed to enable live mode on %s: %s", ip_addr, err)
        return False


def create_ddp_device(ip_addr: str, devices: Dict[str, DDPDevice] | None = None) -> DDPDevice:
    """Create or return a cached DDPDevice."""
    if devices is None:
        return DDPDevice(ip_addr)
    if ip_addr not in devices:
        devices[ip_addr] = DDPDevice(ip_addr)
    return devices[ip_addr]
