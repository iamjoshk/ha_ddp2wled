"""API client for Pixel Magic Tool."""
from __future__ import annotations

import copy
import io
import json
import logging
import math
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


def hex_to_rgb(hex_color: int) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    r = (hex_color >> 16) & 0xFF
    g = (hex_color >> 8) & 0xFF
    b = hex_color & 0xFF
    return (r, g, b)


def rgb_to_hex(r: int, g: int, b: int) -> int:
    """Convert RGB to hex color."""
    return (r << 16) | (g << 8) | b


def color_similarity(color1: int, color2: int) -> float:
    """
    Calculate color similarity (0-100, 0 = identical).
    Based on Euclidean distance in RGB space.
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    dr = rgb1[0] - rgb2[0]
    dg = rgb1[1] - rgb2[1]
    db = rgb1[2] - rgb2[2]
    
    # Euclidean distance normalized to 0-100
    return math.sqrt(dr * dr + dg * dg + db * db) / 4.41


def average_colors(colors: list[int]) -> int:
    """Average a list of hex colors."""
    if not colors:
        return 0
    
    total_r = total_g = total_b = 0
    for color in colors:
        r, g, b = hex_to_rgb(color)
        total_r += r
        total_g += g
        total_b += b
    
    count = len(colors)
    avg_r = round(total_r / count)
    avg_g = round(total_g / count)
    avg_b = round(total_b / count)
    
    return rgb_to_hex(avg_r, avg_g, avg_b)


def compress_colors(colors: list[int], level: int) -> list[int]:
    """
    Compress color array by averaging similar adjacent colors.
    
    Args:
        colors: List of hex color integers
        level: Compression level (1-10)
               1 = gentlest (minimal compression)
               10 = strongest (more aggressive)
    
    Returns:
        Compressed list of colors
    """
    if level <= 0 or not colors:
        return colors
    
    # Level 1 = 98 threshold (gentlest), Level 10 = 75 threshold (more aggressive)
    threshold = 98 - ((level - 1) * 2.56)
    
    compressed_colors = []
    i = 0
    
    while i < len(colors):
        current_color = colors[i]
        group_size = 1
        
        # Look ahead to find similar colors
        max_look_ahead = min(i + level + 1, len(colors))
        for j in range(i + 1, max_look_ahead):
            if color_similarity(current_color, colors[j]) < threshold:
                group_size += 1
            else:
                break
        
        # Average the grouped colors
        if group_size > 1:
            avg_color = average_colors(colors[i:i + group_size])
            compressed_colors.extend([avg_color] * group_size)
        else:
            compressed_colors.append(current_color)
        
        i += group_size
    
    return compressed_colors


class PixelMagicToolAPI:
    """Client for Pixel Magic Tool API."""

    def __init__(self, api_url: str = "https://pixelmagictool.vercel.app/api/wled/image"):
        """Initialize the API client."""
        self.api_url = api_url

    def _set_segment_update_params(self, segment: dict[str, Any]) -> None:
        """
        Set required parameters on a segment for device update.
        
        Args:
            segment: The segment dictionary to modify in-place
        """
        segment["fx"] = 0  # Effect ID 0 = Solid (required for individual LED control)
        segment["sel"] = True  # Mark segment as selected/active

    def _ensure_wled_update_params(self, wled_json: dict[str, Any]) -> dict[str, Any]:
        """
        Ensure WLED JSON has the correct parameters for device update.
        
        This fixes the issue where JSON shows in WLED preview but device doesn't update.
        We need to:
        1. Set effect (fx) to 0 (Solid) for individual LED control
        2. Disable live override (liv) so updates are applied immediately
        3. Mark segment as selected (sel) to ensure it's active
        
        Args:
            wled_json: The WLED JSON payload from the API
            
        Returns:
            Modified WLED JSON with correct update parameters
        """
        # Use deep copy to avoid modifying the original object
        modified_json = copy.deepcopy(wled_json)
        
        # Ensure segment parameters for device update
        if "seg" in modified_json:
            # Handle both single segment (dict) and multiple segments (list)
            if isinstance(modified_json["seg"], dict):
                self._set_segment_update_params(modified_json["seg"])
            elif isinstance(modified_json["seg"], list):
                # Multiple segments - modify each one
                for segment in modified_json["seg"]:
                    if isinstance(segment, dict):
                        self._set_segment_update_params(segment)
        
        # Disable live override to ensure updates are applied immediately
        modified_json["liv"] = False
        
        return modified_json

    async def convert_image(
        self,
        image_url: str,
        segment_id: int = 0,
        output: str = "json",
        brightness: int = 128,
        pattern: str = "range",
        width: int | None = None,
        height: int | None = None,
        transparent_color: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> dict[str, Any]:
        """
        Convert an image using the Pixel Magic Tool API.
        
        Args:
            image_url: URL of the image to convert
            segment_id: WLED segment ID
            output: Output format (json, ha, curl)
            brightness: LED brightness (0-255)
            pattern: Pattern type (individual, index, range)
            width: Target width in pixels (optional)
            height: Target height in pixels (optional)
            transparent_color: Hex color for transparent pixels (optional)
            session: Optional aiohttp session
            
        Returns:
            Dictionary containing the WLED JSON
        """
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            # Download the image first
            _LOGGER.debug("Downloading image from: %s", image_url)
            async with session.get(image_url) as response:
                response.raise_for_status()
                image_data = await response.read()

            # Prepare the API request
            data = aiohttp.FormData()
            data.add_field(
                'image',
                image_data,
                filename='image.png',
                content_type='image/png'
            )

            # Build query parameters
            params = {
                'id': segment_id,
                'output': output,
                'brightness': brightness,
                'pattern': pattern,
            }

            if width is not None:
                params['width'] = width
                params['w'] = width

            if height is not None:
                params['height'] = height
                params['h'] = height

            if transparent_color:
                params['color'] = transparent_color.lstrip('#')
                params['c'] = transparent_color.lstrip('#')

            _LOGGER.debug("Sending to Pixel Magic Tool API with params: %s", params)

            # Call the API
            async with session.post(
                self.api_url,
                data=data,
                params=params,
            ) as response:
                response.raise_for_status()
                
                # The API returns JSON string, we need to parse it
                result_text = await response.text()
                
                _LOGGER.debug("API response received, length: %d", len(result_text))
                
                # Parse the JSON if it's a JSON output
                if output == "json":
                    # Check for empty or invalid response before parsing
                    if not result_text or not result_text.strip():
                        _LOGGER.error("Received empty response from API")
                        raise ValueError("API returned empty response")
                    
                    try:
                        result = json.loads(result_text)
                    except json.JSONDecodeError as json_err:
                        _LOGGER.error(
                            "Failed to parse JSON response: %s. Response text (first 500 chars): %s",
                            json_err,
                            result_text[:500]
                        )
                        raise ValueError(f"Invalid JSON response from API: {json_err}") from json_err
                    
                    # Ensure WLED JSON has the correct parameters for device update
                    result = self._ensure_wled_update_params(result)
                    return result
                else:
                    return {"result": result_text}

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error calling Pixel Magic Tool API: %s", err)
            raise
        except (json.JSONDecodeError, ValueError):
            # These are already logged in the inner try-catch blocks
            raise
        except Exception as err:
            _LOGGER.error("Error calling Pixel Magic Tool API: %s", err)
            raise
        finally:
            if close_session:
                await session.close()

    def compress_wled_json(
        self,
        wled_json: dict[str, Any],
        compression_level: int = 5,
    ) -> dict[str, Any]:
        """
        Compress WLED JSON by averaging similar adjacent colors.
        
        Args:
            wled_json: The WLED JSON payload
            compression_level: Compression level (1-10, 1=gentlest, 10=most aggressive)
            
        Returns:
            Compressed WLED JSON
        """
        if compression_level <= 0 or compression_level > 10:
            _LOGGER.warning("Invalid compression level %d, skipping compression", compression_level)
            return wled_json
        
        compressed_json = wled_json.copy()
        
        # Check if 'seg' exists and has color data
        if "seg" in compressed_json and "i" in compressed_json["seg"]:
            original_colors = compressed_json["seg"]["i"]
            
            # Handle different pattern formats
            if isinstance(original_colors, list):
                # For individual pattern (simple list of colors)
                if all(isinstance(x, int) for x in original_colors):
                    compressed_colors = compress_colors(original_colors, compression_level)
                    original_size = len(json.dumps(original_colors))
                    compressed_size = len(json.dumps(compressed_colors))
                    _LOGGER.info(
                        "Compressed color data: %d -> %d bytes (%.1f%% reduction)",
                        original_size,
                        compressed_size,
                        (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
                    )
                    compressed_json["seg"]["i"] = compressed_colors
                # For index or range patterns, extract colors and recompress
                elif len(original_colors) > 0:
                    # Extract just the color values for compression
                    colors_only = [x for x in original_colors if isinstance(x, int) and x >= 0]
                    if colors_only:
                        compressed_colors = compress_colors(colors_only, compression_level)
                        # Note: For range/index patterns, we'd need to rebuild the pattern
                        # For now, we'll just compress individual pattern
                        _LOGGER.debug("Pattern compression for range/index not yet implemented")
        
        return compressed_json

    async def send_to_wled(
        self,
        wled_host: str,
        wled_json: dict[str, Any],
        timeout: int = 10,
        session: aiohttp.ClientSession | None = None,
        use_chunks: bool = False,
        chunk_size: int = 512,
    ) -> bool:
        """
        Send WLED JSON to a WLED device.
        
        Args:
            wled_host: IP address or hostname of WLED device
            wled_json: The WLED JSON payload
            timeout: Request timeout in seconds
            session: Optional aiohttp session
            use_chunks: Split large payloads into multiple smaller requests
            chunk_size: Number of LEDs per chunk when using chunked sending
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If the payload is too large for WLED to handle
            aiohttp.ClientError: For network errors
        """
        close_session = False
        if session is None:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            session = aiohttp.ClientSession(timeout=timeout_config)
            close_session = True

        try:
            # Calculate payload size for logging
            payload_size = len(json.dumps(wled_json))
            _LOGGER.debug("Sending to WLED at %s (payload size: %d bytes)", f"http://{wled_host}/json/state", payload_size)
            
            # If chunked sending is enabled and payload is large, split it
            if use_chunks and payload_size > 15000:  # 15KB threshold for chunking
                _LOGGER.info("Using chunked sending due to large payload size (%d bytes)", payload_size)
                return await self._send_to_wled_chunked(
                    wled_host, wled_json, chunk_size, timeout, session
                )
            
            # Send as single request
            return await self._send_to_wled_single(
                wled_host, wled_json, timeout, session
            )

        finally:
            if close_session:
                await session.close()

    async def _send_to_wled_single(
        self,
        wled_host: str,
        wled_json: dict[str, Any],
        timeout: int,
        session: aiohttp.ClientSession,
    ) -> bool:
        """Send WLED JSON as a single request."""
        url = f"http://{wled_host}/json/state"
        
        # Calculate payload size for logging
        payload_size = len(json.dumps(wled_json))
        
        # Warn if payload is large (WLED typically has issues with payloads > 20-30KB)
        if payload_size > 20000:
            _LOGGER.warning(
                "Large payload size (%d bytes) may exceed WLED limits. "
                "Consider enabling use_chunks or using smaller images.",
                payload_size
            )
        
        async with session.post(
            url,
            json=wled_json,
            headers={"Content-Type": "application/json"},
        ) as response:
            # Check for 413 Payload Too Large specifically
            if response.status == 413:
                _LOGGER.error(
                    "WLED rejected payload as too large (%d bytes). "
                    "Try: 1) Enable use_chunks, 2) Reduce image dimensions, "
                    "3) Use a more efficient pattern type.",
                    payload_size
                )
                raise ValueError(
                    f"Payload too large for WLED ({payload_size} bytes). "
                    "Enable use_chunks or reduce image dimensions."
                )
            
            response.raise_for_status()
            
            # Parse JSON response with error handling
            try:
                response_data = await response.json()
            except aiohttp.ContentTypeError as json_err:
                response_text = await response.text()
                _LOGGER.error(
                    "Failed to parse WLED response as JSON: %s. Response text (first 200 chars): %s",
                    json_err,
                    response_text[:200] if response_text else "(empty)"
                )
                raise ValueError(f"WLED returned invalid JSON response: {json_err}") from json_err

            if not response_data.get("success", False):
                _LOGGER.error("WLED returned success=false: %s", response_data)
                return False

            _LOGGER.info("Successfully sent to WLED device")
            return True

    async def _send_to_wled_chunked(
        self,
        wled_host: str,
        wled_json: dict[str, Any],
        chunk_size: int,
        timeout: int,
        session: aiohttp.ClientSession,
    ) -> bool:
        """
        Send WLED JSON in chunks by splitting LED data into multiple requests.
        
        This splits the LED color data into smaller chunks and sends them sequentially
        using the index pattern format, allowing WLED to handle larger total payloads 
        that would otherwise exceed its limits.
        """
        url = f"http://{wled_host}/json/state"
        
        # Extract segment data
        if "seg" not in wled_json or "i" not in wled_json["seg"]:
            _LOGGER.warning("No segment data to chunk, sending as single request")
            return await self._send_to_wled_single(wled_host, wled_json, timeout, session)
        
        led_data = wled_json["seg"]["i"]
        segment_id = wled_json["seg"].get("id", 0)
        
        # Calculate how many LEDs we have based on the pattern type
        # For individual pattern: each entry is a color
        # For range pattern: entries are [start, end, color, start, end, color, ...]
        if isinstance(led_data, list) and len(led_data) > 0:
            # Determine if this is a range pattern or individual pattern
            is_range_pattern = False
            if len(led_data) >= 3 and isinstance(led_data[0], int) and isinstance(led_data[1], int):
                # Likely a range pattern
                is_range_pattern = True
            
            if is_range_pattern:
                # For range pattern, we need to expand it to individual colors first
                led_colors = self._expand_range_pattern(led_data)
            else:
                # Individual pattern - already a simple list of colors
                led_colors = led_data
            
            total_leds = len(led_colors)
            _LOGGER.info("Chunking %d LEDs into chunks of %d", total_leds, chunk_size)
            
            # Split into chunks
            chunks = []
            for i in range(0, total_leds, chunk_size):
                chunk = led_colors[i:i + chunk_size]
                chunks.append((i, chunk))
            
            _LOGGER.info("Sending %d chunks to WLED", len(chunks))
            
            # Send each chunk sequentially
            for chunk_idx, (start_led, chunk) in enumerate(chunks):
                # Build index pattern: [index, color, index, color, ...]
                # This tells WLED exactly which LEDs to update
                indexed_chunk = []
                for offset, color in enumerate(chunk):
                    indexed_chunk.append(start_led + offset)
                    indexed_chunk.append(color)
                
                chunk_payload = {
                    "seg": {
                        "id": segment_id,
                        "i": indexed_chunk,
                        "fx": 0,  # Effect ID 0 = Solid (required for individual LED control)
                        "sel": True,  # Mark segment as selected/active
                    },
                    "liv": False,  # Disable live override to ensure updates are applied
                }
                
                # Include other top-level settings only in the first chunk
                if chunk_idx == 0:
                    if "on" in wled_json:
                        chunk_payload["on"] = wled_json["on"]
                    if "bri" in wled_json:
                        chunk_payload["bri"] = wled_json["bri"]
                
                _LOGGER.debug("Sending chunk %d/%d (LEDs %d-%d)", 
                             chunk_idx + 1, len(chunks), start_led, start_led + len(chunk) - 1)
                
                async with session.post(
                    url,
                    json=chunk_payload,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status == 413:
                        _LOGGER.error(
                            "Chunk %d still too large. Try reducing chunk_size.",
                            chunk_idx + 1
                        )
                        raise ValueError(
                            f"Chunk {chunk_idx + 1} too large. Reduce chunk_size parameter."
                        )
                    
                    response.raise_for_status()
                    
                    # Parse JSON response with error handling
                    try:
                        response_data = await response.json()
                    except aiohttp.ContentTypeError as json_err:
                        response_text = await response.text()
                        _LOGGER.error(
                            "Chunk %d: Failed to parse WLED response as JSON: %s. Response text (first 200 chars): %s",
                            chunk_idx + 1,
                            json_err,
                            response_text[:200] if response_text else "(empty)"
                        )
                        raise ValueError(f"WLED returned invalid JSON for chunk {chunk_idx + 1}: {json_err}") from json_err
                    
                    if not response_data.get("success", False):
                        _LOGGER.error("WLED returned success=false for chunk %d: %s", 
                                     chunk_idx + 1, response_data)
                        return False
            
            _LOGGER.info("Successfully sent all %d chunks to WLED device", len(chunks))
            return True
        
        # Fallback to single request if we can't parse the data
        _LOGGER.warning("Could not parse LED data for chunking, sending as single request")
        return await self._send_to_wled_single(wled_host, wled_json, timeout, session)
    
    def _expand_range_pattern(self, range_data: list) -> list:
        """
        Expand a WLED range pattern into individual LED colors.
        
        Range pattern format: [start, end, color, start, end, color, ...]
        Returns: [color0, color1, color2, ...]
        """
        expanded = []
        i = 0
        
        while i <= len(range_data) - 3:
            start = range_data[i]
            end = range_data[i + 1]
            color = range_data[i + 2]
            
            # Add color for each LED in the range (more efficient using list multiplication)
            expanded.extend([color] * (end - start + 1))
            
            i += 3
        
        return expanded
