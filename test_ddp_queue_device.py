"""Tests for DDPDevice queue and packetization."""
import struct

from src.net.ddp_queue import DDPDevice, DDP_FLAGS_PUSH, DDP_FLAGS_VER1


class _FakeSocket:
    def __init__(self, fail_first: bool = False):
        self.sent = []
        self._closed = False
        self._fail_first = fail_first
        self._attempts = 0

    def settimeout(self, _timeout):
        return None

    def sendto(self, data, addr):
        self._attempts += 1
        if self._fail_first and self._attempts == 1:
            raise OSError("fake failure")
        self.sent.append((data, addr))

    def close(self):
        self._closed = True


def test_packetization_and_flush():
    fake = _FakeSocket()
    device = DDPDevice(
        "127.0.0.1",
        max_pixels_per_packet=2,
        socket_factory=lambda: fake,
        start_thread=False,
    )

    # 5 pixels -> 3 packets (2,2,1)
    rgb = bytes([1, 2, 3] * 5)
    device.enqueue_frame(rgb, width=5, height=1)
    flushed = device.flush_from_queue()
    assert flushed is True
    assert len(fake.sent) == 3

    # Validate headers
    first_packet = fake.sent[0][0]
    header = first_packet[:10]
    flags, seq, _dtype, _dest, offset, length, _tc = struct.unpack(">BBBBHHH", header)
    assert flags == DDP_FLAGS_VER1
    assert seq == 0
    assert offset == 0
    assert length == 6  # 2 pixels * 3 bytes

    last_packet = fake.sent[-1][0]
    flags_last = last_packet[0]
    assert flags_last == DDP_FLAGS_VER1 | DDP_FLAGS_PUSH


def test_retry_on_failure():
    fake = _FakeSocket(fail_first=True)
    device = DDPDevice(
        "127.0.0.1",
        max_pixels_per_packet=1,
        retry_attempts=2,
        socket_factory=lambda: fake,
        start_thread=False,
    )

    rgb = bytes([9, 9, 9])
    device.enqueue_frame(rgb)
    device.flush_from_queue()

    # Two attempts: first fails, second succeeds
    assert len(fake.sent) == 1
    assert fake._attempts == 2


if __name__ == "__main__":
    test_packetization_and_flush()
    test_retry_on_failure()
    print("✓ DDPDevice queue tests passed")
