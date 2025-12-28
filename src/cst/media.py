"""CAST media handling for WLED DDP streaming."""
from __future__ import annotations

import logging
from typing import Dict

from ..net.ddp_queue import DDPDevice

_LOGGER = logging.getLogger(__name__)


class CASTMedia:
    """Manage DDP devices for media casting."""

    def __init__(self) -> None:
        self._devices: Dict[str, DDPDevice] = {}

    def get_device(self, ip_addr: str) -> DDPDevice:
        """Return an existing DDPDevice or create a new one for the IP."""
        if ip_addr not in self._devices:
            _LOGGER.debug("Creating new DDPDevice for %s", ip_addr)
            self._devices[ip_addr] = DDPDevice(ip_addr)
        return self._devices[ip_addr]

    def cast_frame(self, ip_addr: str, rgb_data: bytes, width: int | None = None, height: int | None = None) -> None:
        """Queue a frame for the given IP address."""
        device = self.get_device(ip_addr)
        device.enqueue_frame(rgb_data, width, height)

    def flush(self, ip_addr: str) -> bool:
        """Flush queued frames to the device."""
        device = self.get_device(ip_addr)
        return device.flush_from_queue()

    def shutdown_all(self) -> None:
        """Shutdown all managed devices."""
        for dev in self._devices.values():
            dev.shutdown()
