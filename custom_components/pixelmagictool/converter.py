"""API client for Pixel Magic Tool."""
from __future__ import annotations

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
                    result = json.loads(result_text)
                    return result
                else:
                    return {"result": result_text}

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error calling Pixel Magic Tool API: %s", err)
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
    ) -> bool:
        """
        Send WLED JSON to a WLED device.
        
        Args:
            wled_host: IP address or hostname of WLED device
            wled_json: The WLED JSON payload
            timeout: Request timeout in seconds
            session: Optional aiohttp session
            
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
            url = f"http://{wled_host}/json/state"
            
            # Calculate payload size for logging
            payload_size = len(json.dumps(wled_json))
            _LOGGER.debug("Sending to WLED at %s (payload size: %d bytes)", url, payload_size)
            
            # Warn if payload is large (WLED typically has issues with payloads > 20-30KB)
            if payload_size > 20000:
                _LOGGER.warning(
                    "Large payload size (%d bytes) may exceed WLED limits. "
                    "Consider using smaller images or lower resolution.",
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
                        "Try: 1) Reduce image dimensions, 2) Use a more efficient pattern type, "
                        "3) Consider alternative WLED upload methods for large images.",
                        payload_size
                    )
                    raise ValueError(
                        f"Payload too large for WLED ({payload_size} bytes). "
                        "Reduce image dimensions or use a more efficient pattern."
                    )
                
                response.raise_for_status()
                response_data = await response.json()

                if not response_data.get("success", False):
                    _LOGGER.error("WLED returned success=false: %s", response_data)
                    return False

                _LOGGER.info("Successfully sent to WLED device")
                return True

        except aiohttp.ClientResponseError as err:
            if err.status == 413:
                # Already handled above, but catch here in case
                raise ValueError(
                    f"Payload too large for WLED. Try reducing image dimensions."
                ) from err
            _LOGGER.error("HTTP error sending to WLED: %s", err)
            raise
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error sending to WLED: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error sending to WLED: %s", err)
            raise
        finally:
            if close_session:
                await session.close()
