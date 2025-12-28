"""Image processing and DDP client for WLEDVideoSync."""
from __future__ import annotations

import asyncio
import io
import logging
import os

import aiohttp
from PIL import Image

try:
    # Prefer package-relative import when available (Home Assistant)
    from .ddp import DDPClient
except ImportError as err:
    # Only fall back when the ddp module itself is missing (e.g., direct test execution)
    missing = getattr(err, "name", None)
    if missing not in (None, "ddp", "pixelmagictool.ddp"):
        raise
    from ddp import DDPClient

_LOGGER = logging.getLogger(__name__)

MIN_KEEPALIVE_INTERVAL = 0.1


class PixelMagicToolAPI:
    """Client for sending images to WLED via DDP protocol."""

    def __init__(self, api_url: str = None):
        """
        Initialize the DDP client.
        
        Args:
            api_url: Ignored parameter kept for backwards compatibility.
                    This class only uses DDP protocol and doesn't need an API URL.
        """
        self._keepalive_task: asyncio.Task | None = None

    async def async_close(self) -> None:
        """Cancel any running keepalive task."""
        await self._cancel_keepalive_task()

    async def _cancel_keepalive_task(self) -> None:
        """Cancel and await any running keepalive task."""
        if self._keepalive_task and not self._keepalive_task.done():
            self._keepalive_task.cancel()
            _LOGGER.debug("Cancelled previous DDP keepalive task")
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
        self._keepalive_task = None

    def _validate_image_data(self, image_data: bytes, source: str) -> None:
        """
        Validate that image data is not empty and is a valid image.
        
        Args:
            image_data: The image data bytes to validate
            source: Description of the image source (for error messages)
            
        Raises:
            ValueError: If the image data is empty or invalid
        """
        # Check if data is empty
        if not image_data or len(image_data) == 0:
            _LOGGER.error("Image data is empty from source: %s", source)
            raise ValueError(f"Image data is empty from {source}. Please check the image source.")
        
        # Validate that it's a valid image by trying to open it
        try:
            img = Image.open(io.BytesIO(image_data))
            img.load()  # Force loading to validate the image data
            _LOGGER.debug("Successfully validated image from %s: format=%s, size=%dx%d, mode=%s", 
                         source, img.format, img.width, img.height, img.mode)
        except Exception as img_err:
            _LOGGER.error("Data from %s is not a valid image: %s", source, img_err)
            raise ValueError(f"Data from {source} is not a valid image: {img_err}") from img_err

    async def _load_image_data(
        self,
        image_source: str,
        session: aiohttp.ClientSession | None = None,
    ) -> bytes:
        """
        Load image data from either a URL or local file path.
        
        Args:
            image_source: URL (http:// or https://) or local file path
            session: Optional aiohttp session (only used for URLs)
            
        Returns:
            Image data as bytes (validated to be a valid image)
            
        Raises:
            ValueError: If image source is invalid or cannot be loaded
            FileNotFoundError: If local file doesn't exist
        """
        # Check if it's a URL or local file path
        if image_source.startswith(('http://', 'https://')):
            # Load from URL
            _LOGGER.debug("Loading image from URL: %s", image_source)
            
            close_session = False
            if session is None:
                session = aiohttp.ClientSession()
                close_session = True
            
            try:
                async with session.get(image_source) as response:
                    response.raise_for_status()
                    image_data = await response.read()
                    
                # Validate the downloaded image data
                self._validate_image_data(image_data, f"URL: {image_source}")
                return image_data
            finally:
                if close_session:
                    await session.close()
        else:
            # Load from local file path
            _LOGGER.debug("Loading image from local file: %s", image_source)
            
            try:
                # Check if file exists
                if not os.path.exists(image_source):
                    _LOGGER.error("Local image file not found: %s", image_source)
                    raise FileNotFoundError(f"Image file not found: {image_source}")
                
                # Read file asynchronously using context manager
                def read_file():
                    with open(image_source, 'rb') as f:
                        return f.read()
                
                loop = asyncio.get_event_loop()
                image_data = await loop.run_in_executor(None, read_file)
                
                # Validate the loaded image data
                self._validate_image_data(image_data, f"local file: {image_source}")
                return image_data
            except FileNotFoundError:
                raise
            except Exception as err:
                _LOGGER.error("Failed to read local image file: %s", err)
                raise ValueError(f"Failed to read local image file: {err}") from err

    async def send_image_via_ddp(
        self,
        image_source: str,
        wled_host: str,
        width: int,
        height: int,
        brightness: int = 255,
        segment_id: int = 0,
        timeout: int = 10,
        session: aiohttp.ClientSession | None = None,
        keepalive_seconds: float = 60.0,
        keepalive_interval: float = 1.0,
    ) -> bool:
        """
        Send an image to WLED via DDP protocol.
        
        This method loads an image from a URL or local file path, resizes it to 
        the specified dimensions, converts it to RGB24 format, and sends it via 
        DDP protocol.
        
        By default this matches the WLEDVideoSync behavior: DDP packets are sent
        directly without any HTTP preparation. A `prepare_device` option is available
        on lower-level calls for rare cases where you need WLED configured via HTTP
        first, but it is off by default.
        
        Args:
            image_source: URL (http://, https://) or local file path of the image
            wled_host: IP address or hostname of WLED device
            width: Target width in pixels
            height: Target height in pixels
            brightness: Brightness multiplier (0-255)
            segment_id: WLED segment ID (default: 0)
            timeout: Request timeout in seconds
            session: Optional aiohttp session (only used for URL downloads)
            keepalive_seconds: How long to keep re-sending the frame to avoid
                WLED reverting after its realtime timeout (0 disables keepalive)
            keepalive_interval: Seconds between keepalive sends
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If image processing fails
            FileNotFoundError: If local file doesn't exist
            OSError: For network errors
        """
        close_session = False
        if session is None:
            session = aiohttp.ClientSession()
            close_session = True

        try:
            # Load and validate image from URL or local file
            # The _load_image_data method handles downloading from URLs or reading 
            # from local files, and validates that the data is a valid image
            image_data = await self._load_image_data(image_source, session)

            # Open image with PIL for processing
            try:
                img = Image.open(io.BytesIO(image_data))
                # Note: Validation already done in _load_image_data, this is just for processing
                _LOGGER.debug("Processing image: format=%s, size=%dx%d, mode=%s", 
                             img.format, img.width, img.height, img.mode)
            except Exception as err:
                _LOGGER.error("Failed to open image for processing: %s", err)
                raise ValueError(f"Failed to open image for processing: {err}") from err

            # Resize image to target dimensions
            _LOGGER.debug("Resizing image to %dx%d", width, height)
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Convert to RGB mode (remove alpha channel if present)
            if img.mode != "RGB":
                _LOGGER.debug("Converting image from %s to RGB mode", img.mode)
                img = img.convert("RGB")
            
            # Apply brightness
            if brightness < 255:
                brightness_factor = brightness / 255.0
                _LOGGER.debug("Applying brightness factor: %.2f", brightness_factor)
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        pixels[x, y] = (
                            int(r * brightness_factor),
                            int(g * brightness_factor),
                            int(b * brightness_factor),
                        )
            
            # Convert image to RGB byte array
            rgb_data = img.tobytes()
            
            _LOGGER.info(
                "Converted image to RGB24: %d bytes for %dx%d image",
                len(rgb_data), width, height
            )
            
            # Send processed image via DDP protocol
            # The DDPClient will prepare WLED via HTTP API before sending DDP packets
            ddp_client = DDPClient(wled_host)
            success = await ddp_client.send_image(
                rgb_data, 
                width, 
                height, 
                segment_id=segment_id,
                timeout=timeout,
                prepare_device=True,
            )
            
            if success:
                _LOGGER.info("Successfully sent image via DDP to %s", wled_host)

                # Keep sending the frame periodically to avoid WLED reverting
                # after the realtime timeout. This mirrors the upstream
                # CASTMedia behavior of keeping the stream alive.
                if keepalive_seconds > 0 and keepalive_interval > 0 and keepalive_interval >= MIN_KEEPALIVE_INTERVAL:
                    loop = asyncio.get_running_loop()
                    await self._cancel_keepalive_task()

                    async def _keepalive() -> None:
                        end_time = loop.time() + keepalive_seconds
                        sends = 0
                        finished_normally = False
                        try:
                            while loop.time() < end_time:
                                try:
                                    await ddp_client.send_image(
                                        rgb_data,
                                        width,
                                        height,
                                        segment_id=segment_id,
                                        timeout=timeout,
                                        prepare_device=False,
                                    )
                                    sends += 1
                                except (OSError, asyncio.TimeoutError) as err:
                                    _LOGGER.debug("DDP keepalive stopped after error: %s", err)
                                    break

                                remaining = end_time - loop.time()
                                if remaining <= 0:
                                    break
                                await asyncio.sleep(min(keepalive_interval, remaining))
                            finished_normally = True
                        except asyncio.CancelledError:
                            _LOGGER.debug("DDP keepalive task cancelled")
                            raise
                        finally:
                            if finished_normally:
                                try:
                                    await ddp_client.apply_frame_state(
                                        rgb_data,
                                        segment_id=segment_id,
                                        timeout=timeout,
                                    )
                                    _LOGGER.debug("Persisted final DDP frame after keepalive window")
                                except Exception as err:
                                    _LOGGER.debug(
                                        "Failed to persist final frame after keepalive: %s",
                                        err,
                                    )
                            _LOGGER.debug(
                                "DDP keepalive finished after %d refreshes (%.1fs window)",
                                sends,
                                keepalive_seconds,
                            )

                    task = asyncio.create_task(_keepalive())

                    def _on_keepalive_done(completed: asyncio.Task) -> None:
                        exc = completed.exception()
                        if exc:
                            _LOGGER.debug("DDP keepalive task finished with error: %s", exc)
                        else:
                            _LOGGER.debug("DDP keepalive task finished cleanly")
                        self._keepalive_task = None

                    task.add_done_callback(_on_keepalive_done)
                    self._keepalive_task = task
                    _LOGGER.info(
                        "Keeping DDP frame alive for %.1f seconds (interval %.2f)",
                        keepalive_seconds,
                        keepalive_interval,
                    )
                else:
                    try:
                        await ddp_client.apply_frame_state(
                            rgb_data,
                            segment_id=segment_id,
                            timeout=timeout,
                        )
                        _LOGGER.debug("Persisted final DDP frame without keepalive")
                    except Exception as err:
                        _LOGGER.debug("Failed to persist final frame without keepalive: %s", err)
            else:
                _LOGGER.error("Failed to send image via DDP to %s", wled_host)
            
            return success

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error downloading image: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error sending image via DDP: %s", err)
            raise
        finally:
            if close_session:
                await session.close()
