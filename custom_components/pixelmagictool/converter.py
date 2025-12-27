"""API client for Pixel Magic Tool."""
from __future__ import annotations

import io
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


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
                    import json
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
            import json
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
