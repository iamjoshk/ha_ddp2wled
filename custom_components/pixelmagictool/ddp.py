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
DDP_TYPE_RGB24 = 0x00  # RGB data type (24-bit)

# Maximum bytes of pixel data in a single DDP packet
# WLED recommends keeping packets under 1400 bytes to avoid fragmentation
# Header is 10 bytes, so max RGB data is ~1390 bytes = ~463 pixels
DDP_MAX_PIXELS_PER_PACKET = 463  # Conservative estimate


class DDPClient:
    """Client for sending images to WLED via DDP protocol.
    
    Supports both one-shot mode (send and close) and continuous streaming mode
    (keep connection open for multiple frames).
    """

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
        self._streaming = False
        self._sequence_num = 0
        self._lock = asyncio.Lock()

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
            "Preparing WLED at %s for DDP streaming (segment %d)",
            self.host, segment_id
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
        # Format: >BBBBHHH
        # B = unsigned char (1 byte) x4
        # H = unsigned short (2 bytes) x3
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
        segment_id: int = 0,
        timeout: int = 10,
        prepare_device: bool = True,
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
            prepare_device: Whether to prepare WLED via HTTP API before sending (default: True)
            
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
        segment_id: int = 0,
        timeout: int = 10,
        prepare_device: bool = True,
    ) -> bool:
        """
        Send raw RGB data to WLED via DDP protocol.
        
        This is a simpler method that doesn't require width/height.
        Use this when you already have the RGB data in the correct format.
        
        Args:
            rgb_data: RGB pixel data (R,G,B,R,G,B,...)
            segment_id: WLED segment ID (default: 0)
            timeout: Socket timeout in seconds
            prepare_device: Whether to prepare WLED via HTTP API before sending (default: True)
            
        Returns:
            True if successful
            
        Raises:
            OSError: For network errors
        """
        num_pixels = len(rgb_data) // 3
        
        # Prepare WLED device via HTTP API to ensure DDP data persists
        if prepare_device:
            _LOGGER.debug("Preparing WLED device before sending DDP packets")
            prep_success = await self.prepare_wled_for_ddp(segment_id, timeout=timeout)
            if not prep_success:
                _LOGGER.warning(
                    "Failed to prepare WLED device, continuing with DDP send anyway"
                )
        
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

    async def start_streaming(
        self,
        segment_id: int = 0,
        timeout: int = 10,
        prepare_device: bool = True,
    ) -> bool:
        """
        Start a continuous streaming session to WLED.
        
        Opens a persistent UDP socket that remains open for sending multiple frames.
        This implements the WLEDVideoSync continuous streaming model.
        
        Args:
            segment_id: WLED segment ID (default: 0)
            timeout: Socket timeout in seconds
            prepare_device: Whether to prepare WLED via HTTP API before streaming
            
        Returns:
            True if streaming session started successfully
            
        Raises:
            RuntimeError: If a streaming session is already active
            OSError: For network errors
        """
        async with self._lock:
            if self._streaming:
                raise RuntimeError(f"Streaming session already active for {self.host}:{self.port}")
            
            # Prepare WLED device if requested
            if prepare_device:
                _LOGGER.debug("Preparing WLED device for streaming session")
                prep_success = await self.prepare_wled_for_ddp(segment_id, timeout=timeout)
                if not prep_success:
                    _LOGGER.warning(
                        "Failed to prepare WLED device, continuing with streaming anyway"
                    )
            
            # Open persistent UDP socket
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.socket.settimeout(timeout)
                self._streaming = True
                self._sequence_num = 0
                
                _LOGGER.info(
                    "Started continuous streaming session to %s:%d",
                    self.host, self.port
                )
                return True
                
            except OSError as err:
                _LOGGER.error(
                    "Failed to start streaming session to %s:%d: %s",
                    self.host, self.port, err
                )
                if self.socket:
                    self.socket.close()
                    self.socket = None
                raise

    async def send_frame(
        self,
        rgb_data: bytes,
        width: int | None = None,
        height: int | None = None,
    ) -> bool:
        """
        Send a single frame to an active streaming session.
        
        Must be called after start_streaming(). The socket remains open after sending.
        This implements the WLEDVideoSync continuous streaming model.
        
        Args:
            rgb_data: RGB pixel data (R,G,B,R,G,B,...)
            width: Optional image width (for logging)
            height: Optional image height (for logging)
            
        Returns:
            True if frame sent successfully
            
        Raises:
            RuntimeError: If no streaming session is active
            OSError: For network errors
        """
        async with self._lock:
            if not self._streaming or self.socket is None:
                raise RuntimeError(
                    f"No active streaming session for {self.host}:{self.port}. "
                    "Call start_streaming() first."
                )
            
            num_pixels = len(rgb_data) // 3
            
            if width and height:
                _LOGGER.debug(
                    "Sending frame %d (%dx%d, %d pixels) to streaming session",
                    self._sequence_num, width, height, num_pixels
                )
            else:
                _LOGGER.debug(
                    "Sending frame %d (%d pixels) to streaming session",
                    self._sequence_num, num_pixels
                )
            
            try:
                # Split data into packets if needed
                if num_pixels <= DDP_MAX_PIXELS_PER_PACKET:
                    # Single packet
                    packet = self._create_ddp_packet(
                        rgb_data,
                        offset=0,
                        sequence=self._sequence_num & 0xFF,  # Wrap at 255
                        push=True
                    )
                    self.socket.sendto(packet, (self.host, self.port))
                else:
                    # Multiple packets
                    num_packets = (num_pixels + DDP_MAX_PIXELS_PER_PACKET - 1) // DDP_MAX_PIXELS_PER_PACKET
                    
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
                            sequence=(self._sequence_num + packet_idx) & 0xFF,
                            push=push,
                        )
                        
                        self.socket.sendto(packet, (self.host, self.port))
                        
                        if packet_idx < num_packets - 1:
                            await asyncio.sleep(0.001)
                
                # Increment sequence number for next frame
                self._sequence_num += 1
                return True
                
            except socket.timeout:
                _LOGGER.error("Socket timeout sending frame to %s:%d", self.host, self.port)
                raise OSError(f"Socket timeout sending frame to {self.host}:{self.port}")
            except OSError as err:
                _LOGGER.error(
                    "Network error sending frame to %s:%d: %s",
                    self.host, self.port, err
                )
                raise

    async def stop_streaming(self) -> bool:
        """
        Stop the continuous streaming session and close the socket.
        
        This implements the WLEDVideoSync continuous streaming model.
        After calling this, start_streaming() must be called again to resume.
        
        Returns:
            True if streaming session stopped successfully
        """
        async with self._lock:
            if not self._streaming:
                _LOGGER.warning(
                    "No active streaming session to stop for %s:%d",
                    self.host, self.port
                )
                return False
            
            try:
                if self.socket:
                    self.socket.close()
                    self.socket = None
                
                self._streaming = False
                self._sequence_num = 0
                
                _LOGGER.info(
                    "Stopped continuous streaming session to %s:%d",
                    self.host, self.port
                )
                return True
                
            except Exception as err:
                _LOGGER.error(
                    "Error stopping streaming session to %s:%d: %s",
                    self.host, self.port, err
                )
                # Ensure cleanup even on error
                self.socket = None
                self._streaming = False
                self._sequence_num = 0
                raise

    def is_streaming(self) -> bool:
        """
        Check if a streaming session is currently active.
        
        Returns:
            True if streaming session is active
        """
        return self._streaming
