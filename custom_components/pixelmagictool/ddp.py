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
        
        This method sends an HTTP API call to WLED to:
        - Disable live override mode (lor: 0)
        - Exit live mode (live: false)
        - Set segment to Solid effect (fx: 0) for individual LED control
        - Mark segment as selected/active (sel: true)
        - Turn segment on (on: true)
        
        This ensures DDP updates persist as the actual LED state rather than
        a temporary realtime buffer that reverts when streaming stops.
        
        Args:
            segment_id: WLED segment ID to prepare (default: 0)
            timeout: HTTP request timeout in seconds
            
        Returns:
            True if preparation was successful, False otherwise
        """
        url = f"http://{self.host}/json/state"
        
        # Prepare the WLED state for DDP streaming
        # This configuration ensures DDP data persists on the display
        payload = {
            "on": True,              # Turn segment on
            "lor": 0,                # Disable live override mode
            "live": False,           # Exit live mode
            "seg": [{
                "id": segment_id,    # Target segment
                "on": True,          # Turn this segment on
                "fx": 0,             # Set to Solid effect (allows individual LED control)
                "sel": True,         # Mark as selected/active
            }]
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
                            "Successfully prepared WLED at %s for DDP streaming",
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
        
        The header is 10 bytes structured as follows (total = 4 + 4 + 2 = 10 bytes):
        - Byte 0: Flags (version + push flag)
        - Byte 1: Sequence number
        - Byte 2: Data type (0x0B for RGB24)
        - Byte 3: Destination ID
        - Bytes 4-7: Data offset in bytes (big-endian, 32-bit)
        - Bytes 8-9: Data length (big-endian, 16-bit)
        
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
        # Format: !BBBBLH -> 4 bytes (BBBB) + 4 bytes (L) + 2 bytes (H) = 10 bytes total
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
        if prepare_device:
            _LOGGER.debug("Preparing WLED device before sending DDP packets")
            prep_success = await self.prepare_wled_for_ddp(segment_id, timeout=timeout)
            if not prep_success:
                _LOGGER.warning(
                    "Failed to prepare WLED device, continuing with DDP send anyway"
                )
        else:
            _LOGGER.debug(
                "Skipping HTTP API preparation - sending DDP packets directly "
                "(matching WLEDVideoSync web UI behavior)"
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
                        "Sending packet %d/%d to %s:%d (seq=%d offset=%d pixels %d-%d bytes=%d push=%s)",
                        packet_idx + 1,
                        num_packets,
                        self.host,
                        self.port,
                        packet_idx,
                        start_pixel * 3,
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
