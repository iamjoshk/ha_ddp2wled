"""DDP (Distributed Display Protocol) implementation for WLED."""
from __future__ import annotations

import asyncio
import logging
import socket
import struct
from typing import Any

_LOGGER = logging.getLogger(__name__)

# DDP Protocol Constants
DDP_PORT = 4048
DDP_FLAGS_VER1 = 0x40  # Version 1
DDP_FLAGS_PUSH = 0x01  # Push flag - data should be displayed immediately
DDP_ID_BROADCAST = 0x00  # Broadcast to all devices
DDP_ID_DEVICE = 0x01  # Single device
DDP_TYPE_RGB24 = 0x00  # RGB data type (24-bit)

# Maximum bytes of pixel data in a single DDP packet
# WLED recommends keeping packets under 1400 bytes to avoid fragmentation
# Header is 10 bytes, so max RGB data is ~1390 bytes = ~463 pixels
DDP_MAX_PIXELS_PER_PACKET = 463  # Conservative estimate


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
        self.socket = None

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
        
        The header is 10 bytes structured as follows:
        - Byte 0: Flags (version + push flag)
        - Byte 1: Sequence number
        - Byte 2: Data type (0 for RGB)
        - Byte 3: Destination ID
        - Bytes 4-5: Data offset (big-endian)
        - Bytes 6-7: Data length (big-endian)
        - Bytes 8-9: Timecode/unused (WLED ignores this)
        
        Args:
            flags: Flags byte (version + push flag)
            sequence: Sequence number for packet ordering
            data_type: Data type (0 for RGB24)
            dest_id: Destination ID (0=broadcast, 1=device)
            data_offset: Byte offset in the display buffer
            data_length: Length of RGB data in bytes
            
        Returns:
            10-byte header as bytes
        """
        # Pack header in big-endian format
        # Format: BBBB HH H H
        # B = unsigned char (1 byte)
        # H = unsigned short (2 bytes)
        header = struct.pack(
            ">BBBBHHH",
            flags,
            sequence,
            data_type,
            dest_id,
            data_offset,
            data_length,
            0,  # Timecode (unused by WLED)
        )
        return header

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
        timeout: int = 10,
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
            timeout: Socket timeout in seconds
            
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
                _LOGGER.debug("Sending single DDP packet")
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
                        "Sending packet %d/%d (pixels %d-%d, %d bytes)",
                        packet_idx + 1, num_packets, start_pixel, end_pixel - 1, len(packet_data)
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

    async def send_rgb_data(
        self,
        rgb_data: bytes,
        timeout: int = 10,
    ) -> bool:
        """
        Send raw RGB data to WLED via DDP protocol.
        
        This is a simpler method that doesn't require width/height.
        Use this when you already have the RGB data in the correct format.
        
        Args:
            rgb_data: RGB pixel data (R,G,B,R,G,B,...)
            timeout: Socket timeout in seconds
            
        Returns:
            True if successful
            
        Raises:
            OSError: For network errors
        """
        num_pixels = len(rgb_data) // 3
        
        _LOGGER.info(
            "Sending %d pixels (%d bytes) via DDP to %s:%d",
            num_pixels, len(rgb_data), self.host, self.port
        )
        
        # Open socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            # Split data into packets if needed
            if num_pixels <= DDP_MAX_PIXELS_PER_PACKET:
                # Single packet
                packet = self._create_ddp_packet(rgb_data, offset=0, sequence=0, push=True)
                sock.sendto(packet, (self.host, self.port))
            else:
                # Multiple packets
                num_packets = (num_pixels + DDP_MAX_PIXELS_PER_PACKET - 1) // DDP_MAX_PIXELS_PER_PACKET
                _LOGGER.info("Splitting into %d DDP packets", num_packets)
                
                for packet_idx in range(num_packets):
                    start_pixel = packet_idx * DDP_MAX_PIXELS_PER_PACKET
                    end_pixel = min((packet_idx + 1) * DDP_MAX_PIXELS_PER_PACKET, num_pixels)
                    
                    start_byte = start_pixel * 3
                    end_byte = end_pixel * 3
                    packet_data = rgb_data[start_byte:end_byte]
                    
                    push = (packet_idx == num_packets - 1)
                    
                    packet = self._create_ddp_packet(
                        packet_data,
                        offset=start_pixel,
                        sequence=packet_idx,
                        push=push,
                    )
                    
                    sock.sendto(packet, (self.host, self.port))
                    
                    if packet_idx < num_packets - 1:
                        await asyncio.sleep(0.001)
            
            _LOGGER.info("Successfully sent RGB data via DDP")
            return True
            
        except socket.timeout:
            _LOGGER.error("Socket timeout sending to %s:%d", self.host, self.port)
            raise OSError(f"Socket timeout sending to {self.host}:{self.port}")
        except OSError as err:
            _LOGGER.error("Network error sending DDP to %s:%d: %s", self.host, self.port, err)
            raise
        finally:
            sock.close()
