"""Services for WLEDVideoSync integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, template
from homeassistant.helpers.service import SupportsResponse

from .const import (
    CONF_BRIGHTNESS,
    CONF_HEIGHT,
    CONF_WLED_HOST,
    CONF_WIDTH,
    DEFAULT_BRIGHTNESS,
    DOMAIN,
    SERVICE_SEND_TO_WLED_DDP,
    SERVICE_START_STREAMING,
    SERVICE_SEND_FRAME,
    SERVICE_STOP_STREAMING,
)
from .converter import PixelMagicToolAPI
from .ddp import DDPClient

_LOGGER = logging.getLogger(__name__)

SEND_TO_WLED_DDP_SCHEMA = vol.Schema(
    {
        vol.Optional("image_url"): cv.template,
        vol.Optional("image_path"): cv.template,
        vol.Required(CONF_WLED_HOST): cv.string,
        vol.Required(CONF_WIDTH): cv.positive_int,
        vol.Required(CONF_HEIGHT): cv.positive_int,
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.All(
            cv.positive_int, vol.Range(min=0, max=255)
        ),
        vol.Optional("segment_id", default=0): cv.positive_int,
        vol.Optional("timeout", default=10): cv.positive_int,
    }
)

START_STREAMING_SCHEMA = vol.Schema(
    {
        vol.Required("session_id"): cv.string,
        vol.Required(CONF_WLED_HOST): cv.string,
        vol.Optional("segment_id", default=0): cv.positive_int,
        vol.Optional("timeout", default=10): cv.positive_int,
        vol.Optional("prepare_device", default=True): cv.boolean,
    }
)

SEND_FRAME_SCHEMA = vol.Schema(
    {
        vol.Required("session_id"): cv.string,
        vol.Optional("image_url"): cv.template,
        vol.Optional("image_path"): cv.template,
        vol.Required(CONF_WIDTH): cv.positive_int,
        vol.Required(CONF_HEIGHT): cv.positive_int,
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.All(
            cv.positive_int, vol.Range(min=0, max=255)
        ),
    }
)

STOP_STREAMING_SCHEMA = vol.Schema(
    {
        vol.Required("session_id"): cv.string,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for WLEDVideoSync."""

    async def handle_send_to_wled_ddp(call: ServiceCall) -> dict[str, Any]:
        """Handle the send_to_wled_ddp service call."""
        try:
            # Check that either image_url or image_path is provided
            if "image_url" not in call.data and "image_path" not in call.data:
                raise ValueError("Either 'image_url' or 'image_path' must be provided")
            
            if "image_url" in call.data and "image_path" in call.data:
                raise ValueError("Cannot specify both 'image_url' and 'image_path'. Please provide only one.")
            
            # Get the image source (URL or path)
            if "image_url" in call.data:
                image_source_template = call.data["image_url"]
                source_type = "url"
            else:
                image_source_template = call.data["image_path"]
                source_type = "path"
            
            # Render template if needed
            if isinstance(image_source_template, template.Template):
                image_source = image_source_template.async_render(parse_result=False)
            else:
                image_source = image_source_template

            wled_host = call.data[CONF_WLED_HOST]
            timeout_seconds = call.data["timeout"]
            width = call.data[CONF_WIDTH]
            height = call.data[CONF_HEIGHT]
            brightness = call.data[CONF_BRIGHTNESS]
            segment_id = call.data["segment_id"]

            _LOGGER.info(
                "send_to_wled_ddp service called: host=%s, source_type=%s, "
                "dimensions=%dx%d, brightness=%d, segment=%d",
                wled_host, source_type, width, height, brightness, segment_id
            )
            _LOGGER.debug("Image source: %s", image_source)

            # Create API client
            api = PixelMagicToolAPI()

            # Send image via DDP
            try:
                success = await api.send_image_via_ddp(
                    image_source=image_source,
                    wled_host=wled_host,
                    width=width,
                    height=height,
                    brightness=brightness,
                    segment_id=segment_id,
                    timeout=timeout_seconds,
                )
            except ValueError as err:
                _LOGGER.error("Failed to process image: %s", err)
                return {
                    "success": False,
                    "image_source": image_source,
                    "source_type": source_type,
                    "wled_host": wled_host,
                    "error": str(err),
                }
            except FileNotFoundError as err:
                _LOGGER.error("Image file not found: %s", err)
                return {
                    "success": False,
                    "image_source": image_source,
                    "source_type": source_type,
                    "wled_host": wled_host,
                    "error": str(err),
                }
            except OSError as err:
                _LOGGER.error("Network error sending DDP: %s", err)
                return {
                    "success": False,
                    "image_source": image_source,
                    "source_type": source_type,
                    "wled_host": wled_host,
                    "error": str(err),
                }

            if success:
                _LOGGER.info("Successfully sent image via DDP to WLED")

                # Fire success event
                hass.bus.async_fire(
                    f"{DOMAIN}_sent_to_wled_ddp",
                    {
                        "image_source": image_source,
                        "source_type": source_type,
                        "wled_host": wled_host,
                        "width": width,
                        "height": height,
                        "brightness": brightness,
                        "segment_id": segment_id,
                    },
                )
                
                # Return result as service response
                return {
                    "success": True,
                    "image_source": image_source,
                    "source_type": source_type,
                    "wled_host": wled_host,
                    "protocol": "ddp",
                    "width": width,
                    "height": height,
                    "brightness": brightness,
                    "segment_id": segment_id,
                }
            else:
                _LOGGER.error("Failed to send to WLED via DDP")
                return {
                    "success": False,
                    "image_source": image_source,
                    "source_type": source_type,
                    "wled_host": wled_host,
                    "error": "Failed to send to WLED via DDP",
                }

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error downloading image: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error sending to WLED via DDP: %s", err)
            raise

    async def handle_start_streaming(call: ServiceCall) -> dict[str, Any]:
        """Handle the start_streaming service call."""
        try:
            session_id = call.data["session_id"]
            wled_host = call.data[CONF_WLED_HOST]
            segment_id = call.data["segment_id"]
            timeout = call.data["timeout"]
            prepare_device = call.data["prepare_device"]

            # Get streaming sessions from hass.data
            streaming_sessions = hass.data[DOMAIN].get("streaming_sessions", {})

            # Check if session already exists
            if session_id in streaming_sessions:
                _LOGGER.warning("Streaming session %s already exists", session_id)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "Streaming session already exists"
                }

            _LOGGER.info(
                "Starting streaming session %s to WLED at %s",
                session_id, wled_host
            )

            # Create DDP client and start streaming
            ddp_client = DDPClient(wled_host)
            
            try:
                success = await ddp_client.start_streaming(
                    segment_id=segment_id,
                    timeout=timeout,
                    prepare_device=prepare_device,
                )

                if success:
                    # Store session
                    streaming_sessions[session_id] = ddp_client
                    
                    _LOGGER.info("Successfully started streaming session %s", session_id)
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "wled_host": wled_host,
                        "segment_id": segment_id,
                    }
                else:
                    return {
                        "success": False,
                        "session_id": session_id,
                        "error": "Failed to start streaming session"
                    }

            except RuntimeError as err:
                _LOGGER.error("Failed to start streaming session: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }
            except OSError as err:
                _LOGGER.error("Network error starting streaming session: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }

        except Exception as err:
            _LOGGER.error("Error starting streaming session: %s", err)
            raise

    async def handle_send_frame(call: ServiceCall) -> dict[str, Any]:
        """Handle the send_frame service call."""
        try:
            session_id = call.data["session_id"]
            width = call.data[CONF_WIDTH]
            height = call.data[CONF_HEIGHT]
            brightness = call.data[CONF_BRIGHTNESS]

            # Check that either image_url or image_path is provided
            if "image_url" not in call.data and "image_path" not in call.data:
                raise ValueError("Either 'image_url' or 'image_path' must be provided")
            
            if "image_url" in call.data and "image_path" in call.data:
                raise ValueError("Cannot specify both 'image_url' and 'image_path'")
            
            # Get the image source
            if "image_url" in call.data:
                image_source_template = call.data["image_url"]
                source_type = "url"
            else:
                image_source_template = call.data["image_path"]
                source_type = "path"
            
            # Render template if needed
            if isinstance(image_source_template, template.Template):
                image_source = image_source_template.async_render(parse_result=False)
            else:
                image_source = image_source_template

            # Get streaming sessions
            streaming_sessions = hass.data[DOMAIN].get("streaming_sessions", {})

            # Check if session exists
            if session_id not in streaming_sessions:
                _LOGGER.error("Streaming session %s not found", session_id)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "Streaming session not found. Call start_streaming first."
                }

            ddp_client = streaming_sessions[session_id]

            _LOGGER.info(
                "Sending frame to streaming session %s (source: %s)",
                session_id, source_type
            )

            # Process image to RGB data
            api = PixelMagicToolAPI()
            
            try:
                rgb_data = await api.process_image_to_rgb(
                    image_source=image_source,
                    width=width,
                    height=height,
                    brightness=brightness,
                )

                # Send frame to streaming session
                success = await ddp_client.send_frame(
                    rgb_data=rgb_data,
                    width=width,
                    height=height,
                )

                if success:
                    _LOGGER.info("Successfully sent frame to streaming session %s", session_id)
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "image_source": image_source,
                        "source_type": source_type,
                        "width": width,
                        "height": height,
                        "brightness": brightness,
                    }
                else:
                    return {
                        "success": False,
                        "session_id": session_id,
                        "error": "Failed to send frame"
                    }

            except ValueError as err:
                _LOGGER.error("Failed to process image: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }
            except RuntimeError as err:
                _LOGGER.error("Streaming session error: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }
            except OSError as err:
                _LOGGER.error("Network error sending frame: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }

        except Exception as err:
            _LOGGER.error("Error sending frame: %s", err)
            raise

    async def handle_stop_streaming(call: ServiceCall) -> dict[str, Any]:
        """Handle the stop_streaming service call."""
        try:
            session_id = call.data["session_id"]

            # Get streaming sessions
            streaming_sessions = hass.data[DOMAIN].get("streaming_sessions", {})

            # Check if session exists
            if session_id not in streaming_sessions:
                _LOGGER.warning("Streaming session %s not found", session_id)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": "Streaming session not found"
                }

            ddp_client = streaming_sessions[session_id]

            _LOGGER.info("Stopping streaming session %s", session_id)

            try:
                success = await ddp_client.stop_streaming()

                # Remove session from dict
                streaming_sessions.pop(session_id, None)

                if success:
                    _LOGGER.info("Successfully stopped streaming session %s", session_id)
                    return {
                        "success": True,
                        "session_id": session_id,
                    }
                else:
                    return {
                        "success": False,
                        "session_id": session_id,
                        "error": "Failed to stop streaming session"
                    }

            except Exception as err:
                # Ensure cleanup even on error
                streaming_sessions.pop(session_id, None)
                _LOGGER.error("Error stopping streaming session: %s", err)
                return {
                    "success": False,
                    "session_id": session_id,
                    "error": str(err)
                }

        except Exception as err:
            _LOGGER.error("Error in stop_streaming handler: %s", err)
            raise

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TO_WLED_DDP,
        handle_send_to_wled_ddp,
        schema=SEND_TO_WLED_DDP_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_STREAMING,
        handle_start_streaming,
        schema=START_STREAMING_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_FRAME,
        handle_send_frame,
        schema=SEND_FRAME_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_STREAMING,
        handle_stop_streaming,
        schema=STOP_STREAMING_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    _LOGGER.info("WLEDVideoSync services registered")
