"""API helpers for DDP operations."""
from __future__ import annotations

import logging
from typing import Callable, Dict

from ..net.ddp_queue import DDPDevice
from ..utl.utils import create_ddp_device

_LOGGER = logging.getLogger(__name__)


class DDPAPI:
    """Simple facade around DDPDevice for callback-based integrations."""

    def __init__(self, device_factory: Callable[[str], DDPDevice] | None = None) -> None:
        self._devices: Dict[str, DDPDevice] = {}
        self._factory = device_factory

    def _get_device(self, host: str) -> DDPDevice:
        if host not in self._devices:
            if self._factory:
                self._devices[host] = self._factory(host)
            else:
                self._devices[host] = create_ddp_device(host, self._devices)
        return self._devices[host]

    def send_rgb_callback(self, host: str, rgb_data: bytes, width: int | None = None, height: int | None = None) -> None:
        """Queue data for sending; useful as a callback target."""
        _LOGGER.debug("Queuing RGB data for host %s", host)
        device = self._get_device(host)
        device.enqueue_frame(rgb_data, width, height)

    def flush(self, host: str) -> bool:
        """Flush queued data to the specified host."""
        return self._get_device(host).flush_from_queue()

    def shutdown(self) -> None:
        """Shutdown all managed devices."""
        for dev in self._devices.values():
            dev.shutdown()
