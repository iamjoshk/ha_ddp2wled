"""DDP queue implementation for streaming pixel data to WLED."""
from __future__ import annotations

import logging
import queue
import socket
import struct
import threading
import time
from typing import Callable, Iterable, Tuple

_LOGGER = logging.getLogger(__name__)

# DDP protocol constants
DDP_PORT = 4048
DDP_FLAGS_VER1 = 0x40
DDP_FLAGS_PUSH = 0x01
DDP_ID_DEVICE = 0x01
DDP_TYPE_RGB24 = 0x00
DDP_MAX_PIXELS_PER_PACKET = 463  # ~1390 bytes of RGB data (<1500 MTU)

# Type aliases
Packet = Tuple[int, bytes, bool]
SocketFactory = Callable[[], socket.socket]


class DDPDevice:
    """Handle queued DDP transmission to a WLED device."""

    def __init__(
        self,
        host: str,
        port: int = DDP_PORT,
        *,
        max_pixels_per_packet: int = DDP_MAX_PIXELS_PER_PACKET,
        retry_attempts: int = 3,
        retry_delay: float = 0.05,
        socket_factory: SocketFactory | None = None,
        start_thread: bool = True,
        socket_timeout: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.max_pixels_per_packet = max_pixels_per_packet
        self.retry_attempts = max(1, retry_attempts)
        self.retry_delay = retry_delay
        self._socket_factory = socket_factory or self._default_socket_factory
        self._socket_timeout = socket_timeout

        self._queue: "queue.Queue[Tuple[bytes, int | None, int | None]]" = queue.Queue()
        self._socket: socket.socket | None = None
        self._sequence = 0
        self._running = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        if start_thread:
            self.start()

    # ------------------------------------------------------------------ #
    # Socket helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _default_socket_factory() -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2.0)
        return sock

    def _ensure_socket(self) -> socket.socket:
        if self._socket is None:
            self._socket = self._socket_factory()
            try:
                self._socket.settimeout(self._socket_timeout)
            except Exception:
                pass
        return self._socket

    def _reset_socket(self) -> None:
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        self._socket = None

    # ------------------------------------------------------------------ #
    # Packet creation
    # ------------------------------------------------------------------ #
    def _create_header(self, sequence: int, offset_pixels: int, data_len: int, push: bool) -> bytes:
        flags = DDP_FLAGS_VER1 | (DDP_FLAGS_PUSH if push else 0)
        return struct.pack(
            ">BBBBHHH",
            flags,
            sequence & 0xFF,
            DDP_TYPE_RGB24,
            DDP_ID_DEVICE,
            offset_pixels * 3,
            data_len,
            0,
        )

    def _packetize(self, rgb_data: bytes) -> Iterable[Packet]:
        num_pixels = len(rgb_data) // 3
        if num_pixels == 0:
            return []

        max_pixels = max(1, self.max_pixels_per_packet)
        num_packets = (num_pixels + max_pixels - 1) // max_pixels

        for packet_idx in range(num_packets):
            start_pixel = packet_idx * max_pixels
            end_pixel = min((packet_idx + 1) * max_pixels, num_pixels)

            start_byte = start_pixel * 3
            end_byte = end_pixel * 3
            chunk = rgb_data[start_byte:end_byte]
            push = packet_idx == num_packets - 1
            yield packet_idx, chunk, push

    # ------------------------------------------------------------------ #
    # Queue + worker
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        """Start the background worker thread."""
        if self._running.is_set():
            return

        self._running.set()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def shutdown(self) -> None:
        """Stop the worker thread and close the socket."""
        self._running.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._reset_socket()

    def enqueue_frame(self, rgb_data: bytes, width: int | None = None, height: int | None = None) -> None:
        """Place pixel data on the queue for async sending."""
        self._queue.put((rgb_data, width, height))

    def flush_from_queue(self) -> bool:
        """Send all queued frames immediately."""
        flushed = False
        while True:
            try:
                rgb_data, width, height = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                self._send_frame(rgb_data, width, height)
            finally:
                self._queue.task_done()
            flushed = True
        return flushed

    def _worker(self) -> None:
        """Background worker: pull from queue and send via UDP."""
        while self._running.is_set():
            try:
                rgb_data, width, height = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                self._send_frame(rgb_data, width, height)
            finally:
                self._queue.task_done()

    # ------------------------------------------------------------------ #
    # Sending
    # ------------------------------------------------------------------ #
    def _send_frame(self, rgb_data: bytes, width: int | None, height: int | None) -> None:
        sequence_base = self._next_sequence()
        if width and height:
            _LOGGER.debug(
                "Sending frame to %s:%d (%dx%d, %d bytes)",
                self.host,
                self.port,
                width,
                height,
                len(rgb_data),
            )

        for idx, chunk, push in self._packetize(rgb_data):
            header = self._create_header(sequence_base + idx, idx * self.max_pixels_per_packet, len(chunk), push)
            packet = header + chunk
            self._send_with_retry(packet)

    def _send_with_retry(self, packet: bytes) -> None:
        for attempt in range(1, self.retry_attempts + 1):
            try:
                sock = self._ensure_socket()
                sock.sendto(packet, (self.host, self.port))
                return
            except OSError as err:
                _LOGGER.warning(
                    "DDP send failed to %s:%d (attempt %d/%d): %s",
                    self.host,
                    self.port,
                    attempt,
                    self.retry_attempts,
                    err,
                )
                self._reset_socket()
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
                else:
                    raise

    def _next_sequence(self) -> int:
        with self._lock:
            seq = self._sequence
            self._sequence = (self._sequence + 1) & 0xFF
            return seq

