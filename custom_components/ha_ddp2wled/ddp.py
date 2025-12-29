"""DDP (Distributed Display Protocol) implementation for WLED."""
from __future__ import annotations

import asyncio
import logging
import socket
import struct

import aiohttp

_LOGGER = logging.getLogger(__name__)

# DDP Protocol Constants
DDP_PORT = 4048
DDP_FLAGS_VER1 = 0x40  # Version 1
DDP_FLAGS_PUSH = 0x01  # Push flag - data should be displayed immediately
DDP_ID_BROADCAST = 0x00  # Broadcast to all devices
DDP_ID_DEVICE = 0x01  # Single device
DDP_TYPE_RGB24 = 0x0B  # RGB data type (24-bit) per DDP spec

# Maximum bytes of pixel data in a single DDP packet
# Upstream WLEDVideoSync uses 480 pixels per packet (~1450 bytes total with header).
# This matches upstream behavior but may exceed the ~1400-byte fragmentation guideline
# on some networks.
DDP_MAX_PIXELS_PER_PACKET = 480


class DDPClient:
    """Client for sending images to WLED via DDP protocol."""

    def __init__(self, host: str, port: int = DDP_PORT):
        """
        Initialize DDP client.
        
        Args:
            host: IP address or hostname of WLED device
            port: UDP port (default 4048 for DDP)
        """
        self.host = host
        self.port = port

    async def prepare_wled_for_ddp(
        self,
        segment_id: int = 0,
        timeout: int = 5,
    ) -> bool:
        """
        Prepare WLED device to receive DDP data by configuring it via HTTP API.
        
        This method sends an HTTP API call to WLED to enable live/realtime mode
        for DDP streaming. This is critical for DDP data persistence.
        
        Args:
            segment_id: WLED segment ID to prepare (default: 0)
            timeout: HTTP request timeout in seconds
            
        Returns:
            True if preparation was successful, False otherwise
        """
        url = f"http://{self.host}/json/state"
        
        # Enable live mode for DDP streaming - this is critical for persistence
        # Based on WLEDVideoSync implementation
        payload = {
            "on": True,              # Turn device on
            "live": True,            # Enable live/realtime mode for DDP
        }
        
        _LOGGER.debug(
            "Preparing WLED at %s for DDP streaming (segment %d) via POST %s payload=%s timeout=%s",
            self.host, segment_id, url, payload, timeout
        )
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "Successfully prepared WLED at %s for DDP streaming (live mode enabled)",
                            self.host
                        )
                        return True
                    else:
                        _LOGGER.warning(
                            "Failed to prepare WLED at %s: HTTP %d",
                            self.host, response.status
                        )
                        return False
        except aiohttp.ClientError as err:
            _LOGGER.warning(
                "Network error preparing WLED at %s: %s",
                self.host, err
            )
            return False
        except Exception as err:
            _LOGGER.warning(
                "Unexpected error preparing WLED at %s: %s",
                self.host, err
            )
            return False

    async def apply_frame_state(
        self,
        rgb_data: bytes,
        segment_id: int = 0,
        timeout: int = 5,
    ) -> bool:
        """
        Persist a final frame to WLED state via HTTP.

        This writes per-pixel colors to the target segment so the image
        remains after realtime DDP packets stop. This is critical for
        ensuring the image persists on the device.
        
        Based on WLEDVideoSync approach for proper state persistence.
        """
        if len(rgb_data) % 3 != 0:
            raise ValueError(
                f"RGB data length must be a multiple of 3 (got {len(rgb_data)} bytes)"
            )

        led_count = len(rgb_data) // 3
        
        # Convert RGB data to WLED individual LED format
        # WLED expects format: [index, [r, g, b]]
        led_data = []
        for idx in range(led_count):
            r = rgb_data[idx * 3]
            g = rgb_data[idx * 3 + 1] 
            b = rgb_data[idx * 3 + 2]
            led_data.append([idx, [r, g, b]])

        payload = {
            "on": True,
            "seg": [
                {
                    "id": segment_id,
                    "i": led_data,  # Individual LED colors
                    "fx": 0,        # Solid effect for individual LED control
                }
            ],
        }

        url = f"http://{self.host}/json/state"
        _LOGGER.debug(
            "Persisting final frame to %s segment %d via POST %s (leds=%d)",
            self.host,
            segment_id,
            url,
            led_count,
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                ) as response:
                    if response.status == 200:
                        _LOGGER.debug("Persisted final frame to WLED state")
                        return True
                    _LOGGER.debug(
                        "Failed to persist final frame to WLED: HTTP %d %s",
                        response.status,
                        response.reason,
                    )
                    return False
        except aiohttp.ClientError as err:
            _LOGGER.debug(
                "Network error persisting final frame to %s: %s", self.host, err
            )
            return False
        except Exception as err:
            _LOGGER.debug(
                "Unexpected error persisting final frame to %s: %s", self.host, err
            )
            return False

    def _create_ddp_header(
        self,
        flags: int,
        sequence: int,
        data_type: int,
        dest_id: int,
        data_offset: int,
        data_length: int,
    ) -> bytes:
        """
        Create a DDP packet header.
        
        The header is 10 bytes structured as follows (network order, no padding):
        - Bytes 0-3: Flags, sequence, data type (0x0B), destination (1 byte each; total 4 bytes)
        - Bytes 4-7: Data offset in bytes (big-endian, 32-bit; total header bytes so far: 8)
        - Bytes 8-9: Data length in bytes (big-endian, 16-bit; total header bytes: 10)
        
        Args:
            flags: Flags byte (version + push flag)
            sequence: Sequence number for packet ordering
            data_type: Data type (0x0B for RGB24)
            dest_id: Destination ID (0=broadcast, 1=device)
            data_offset: Byte offset in the display buffer
            data_length: Length of RGB data in bytes
            
        Returns:
            10-byte header as bytes
        """
        # Pack header in network (big-endian) format matching upstream WLEDVideoSync.
        # Format: !BBBBLH -> bytes0-3 (BBBB, 1 byte each), bytes4-7 (L: offset, 4 bytes), bytes8-9 (H: length, 2 bytes); 10 bytes total with '!' (no padding)
        return struct.pack("!BBBBLH", flags, sequence, data_type, dest_id, data_offset, data_length)

    def _create_ddp_packet(
        self,
        rgb_data: bytes,
        offset: int = 0,
        sequence: int = 0,
        push: bool = True,
    ) -> bytes:
        """
        Create a complete DDP packet with header and RGB data.
        
        Args:
            rgb_data: RGB pixel data (R,G,B,R,G,B,...)
            offset: Pixel offset in the display buffer
            sequence: Sequence number for packet ordering
            push: Whether to push data to display immediately
            
        Returns:
            Complete DDP packet (header + data)
        """
        flags = DDP_FLAGS_VER1
        if push:
            flags |= DDP_FLAGS_PUSH
        
        # Calculate byte offset (3 bytes per RGB pixel)
        byte_offset = offset * 3
        
        header = self._create_ddp_header(
            flags=flags,
            sequence=sequence,
            data_type=DDP_TYPE_RGB24,
            dest_id=DDP_ID_DEVICE,
            data_offset=byte_offset,
            data_length=len(rgb_data),
        )
        
        return header + rgb_data

    async def send_image(
        self,
        rgb_data: bytes,
        width: int,
        height: int,
        segment_id: int = 0,
        timeout: int = 10,
        prepare_device: bool = False,
    ) -> bool:
        """
        Send an image to WLED via DDP protocol.
        
        This method handles packet fragmentation for large images.
        Images are split into multiple packets if they exceed the
        maximum packet size.
        
        Args:
            rgb_data: RGB pixel data (R,G,B,R,G,B,...) in row-major order
            width: Image width in pixels
            height: Image height in pixels
            segment_id: WLED segment ID (default: 0)
            timeout: Socket timeout in seconds
            prepare_device: Whether to prepare WLED via HTTP API before sending (default: False).
                          Set to True only if you need to explicitly set WLED state before DDP.
                          Most users should leave this as False to match WLEDVideoSync behavior.
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If RGB data size doesn't match width*height*3
            OSError: For network errors
        """
        total_pixels = width * height
        expected_size = total_pixels * 3
        
        if len(rgb_data) != expected_size:
            raise ValueError(
                f"RGB data size mismatch: expected {expected_size} bytes "
                f"for {width}x{height} image, got {len(rgb_data)} bytes"
            )
        
        # Prepare WLED device via HTTP API to ensure DDP data persists
        # Always prepare the device to ensure proper live mode is enabled
        _LOGGER.debug("Preparing WLED device for DDP streaming to ensure persistence")
        prep_success = await self.prepare_wled_for_ddp(segment_id, timeout=timeout)
        if not prep_success:
            _LOGGER.warning(
                "Failed to prepare WLED device for live mode, continuing with DDP send anyway"
            )
        
        _LOGGER.info(
            "Sending %dx%d image (%d pixels, %d bytes) via DDP to %s:%d",
            width, height, total_pixels, len(rgb_data), self.host, self.port
        )
        
        # Open socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            # Split data into packets if needed
            if total_pixels <= DDP_MAX_PIXELS_PER_PACKET:
                # Single packet - send entire image at once
                _LOGGER.debug(
                    "Sending single DDP packet to %s:%d (seq=0 offset=0 bytes=%d push=True)",
                    self.host, self.port, len(rgb_data)
                )
                packet = self._create_ddp_packet(rgb_data, offset=0, sequence=0, push=True)
                sock.sendto(packet, (self.host, self.port))
            else:
                # Multiple packets needed
                num_packets = (total_pixels + DDP_MAX_PIXELS_PER_PACKET - 1) // DDP_MAX_PIXELS_PER_PACKET
                _LOGGER.info("Splitting into %d DDP packets", num_packets)
                
                for packet_idx in range(num_packets):
                    # Calculate pixel range for this packet
                    start_pixel = packet_idx * DDP_MAX_PIXELS_PER_PACKET
                    end_pixel = min((packet_idx + 1) * DDP_MAX_PIXELS_PER_PACKET, total_pixels)
                    
                    # Extract RGB data for this packet
                    start_byte = start_pixel * 3
                    end_byte = end_pixel * 3
                    packet_data = rgb_data[start_byte:end_byte]
                    
                    # Push flag only on last packet
                    push = (packet_idx == num_packets - 1)
                    
                    packet = self._create_ddp_packet(
                        packet_data,
                        offset=start_pixel,
                        sequence=packet_idx,
                        push=push,
                    )
                    
                    _LOGGER.debug(
                        "Sending packet %d/%d to %s:%d (seq=%d pixel_offset=%d byte_offset=%d pixels %d-%d bytes=%d push=%s)",
                        packet_idx + 1,
                        num_packets,
                        self.host,
                        self.port,
                        packet_idx,
                        start_pixel,
                        start_byte,
                        start_pixel,
                        end_pixel - 1,
                        len(packet_data),
                        push,
                    )
                    
                    sock.sendto(packet, (self.host, self.port))
                    
                    # Small delay between packets to avoid overwhelming the device
                    if packet_idx < num_packets - 1:
                        await asyncio.sleep(0.001)  # 1ms delay
            
            _LOGGER.info("Successfully sent image via DDP")
            return True
            
        except socket.timeout:
            _LOGGER.error("Socket timeout sending to %s:%d", self.host, self.port)
            raise OSError(f"Socket timeout sending to {self.host}:{self.port}")
        except OSError as err:
            _LOGGER.error("Network error sending DDP to %s:%d: %s", self.host, self.port, err)
            raise
        finally:
            sock.close()