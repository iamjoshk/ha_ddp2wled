"""Services for HA DDP2WLED integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv, template
from homeassistant.helpers.service import SupportsResponse

from .const import (
    CONF_BRIGHTNESS,
    CONF_CLEAR_DISPLAY,
    CONF_HEIGHT,
    CONF_SEGMENT_ID,
    CONF_WLED_HOST,
    CONF_WIDTH,
    DEFAULT_BRIGHTNESS,
    DEFAULT_CLEAR_DISPLAY,
    DEFAULT_HEIGHT,
    DEFAULT_SEGMENT_ID,
    DEFAULT_WIDTH,
    DOMAIN,
    SERVICE_SEND_TO_WLED_DDP,
    SERVICE_STOP_DDP_STREAM,
)
from .converter import DDP2WLEDAPI

_LOGGER = logging.getLogger(__name__)

SEND_TO_WLED_DDP_SCHEMA = vol.Schema(
    {
        vol.Optional("image_url"): cv.template,
        vol.Optional("image_path"): cv.template,
        vol.Required(CONF_WLED_HOST): cv.string,
        vol.Required(CONF_WIDTH): cv.positive_int,
        vol.Required(CONF_HEIGHT): cv.positive_int,
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.Any(
            cv.template, vol.All(cv.positive_int, vol.Range(min=0, max=255))
        ),
        vol.Optional("segment_id", default=0): cv.positive_int,
        vol.Optional("timeout", default=10): cv.positive_int,
        vol.Optional("keepalive_seconds", default=0): vol.All(
            vol.Coerce(float), vol.Range(min=0)
        ),
        vol.Optional("keepalive_interval", default=1): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
        # Image processing parameters (WLEDVideoSync compatible)
        vol.Optional("saturation"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("contrast"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("sharpen"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional("balance_r"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("balance_g"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("balance_b"): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("gamma"): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=2.0)
        ),
        vol.Optional("auto_bright", default=True): cv.boolean,
        vol.Optional("clip_hist_percent", default=0.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=50.0)
        ),
    }
)

# Stop stream service schema
STOP_DDP_STREAM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WLED_HOST): cv.string,
        vol.Optional(CONF_SEGMENT_ID, default=DEFAULT_SEGMENT_ID): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=31)
        ),
        vol.Optional(CONF_CLEAR_DISPLAY, default=DEFAULT_CLEAR_DISPLAY): cv.boolean,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for HA DDP2WLED."""

    api = DDP2WLEDAPI()

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
            
            # Handle brightness template rendering
            brightness_template = call.data[CONF_BRIGHTNESS]
            if isinstance(brightness_template, template.Template):
                brightness_str = brightness_template.async_render(parse_result=False)
                try:
                    brightness = int(float(brightness_str))
                    # Clamp brightness to valid range
                    brightness = max(0, min(255, brightness))
                except (ValueError, TypeError):
                    _LOGGER.error("Invalid brightness value from template: %s", brightness_str)
                    brightness = DEFAULT_BRIGHTNESS
            else:
                brightness = brightness_template
            
            segment_id = call.data["segment_id"]
            keepalive_seconds = call.data["keepalive_seconds"]
            keepalive_interval = call.data["keepalive_interval"]

            # Get image processing parameters (use defaults only if not specified)
            saturation = call.data.get("saturation", 1.0)
            contrast = call.data.get("contrast", 1.0)
            sharpen = call.data.get("sharpen", 0.0)
            balance_r = call.data.get("balance_r", 1.0)
            balance_g = call.data.get("balance_g", 1.0)
            balance_b = call.data.get("balance_b", 1.0)
            gamma = call.data.get("gamma", 0.5)
            auto_bright = call.data["auto_bright"]
            clip_hist_percent = call.data.get("clip_hist_percent", 25.0)

            _LOGGER.info(
                "send_to_wled_ddp service called: host=%s, source_type=%s, "
                "dimensions=%dx%d, brightness=%d, segment=%d, keepalive=%.1fs/%.2fs, "
                "auto_bright=%s, gamma=%.2f",
                wled_host,
                source_type,
                width,
                height,
                brightness,
                segment_id,
                keepalive_seconds,
                keepalive_interval,
                auto_bright,
                gamma,
            )
            _LOGGER.debug("Image source: %s", image_source)

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
                    keepalive_seconds=keepalive_seconds,
                    keepalive_interval=keepalive_interval,
                    # Image processing parameters
                    saturation=saturation,
                    contrast=contrast,
                    sharpen=sharpen,
                    balance_r=balance_r,
                    balance_g=balance_g,
                    balance_b=balance_b,
                    gamma=gamma,
                    auto_bright=auto_bright,
                    clip_hist_percent=clip_hist_percent,
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

    async def handle_stop_ddp_stream(call: ServiceCall) -> dict[str, Any]:
        """Handle the stop_ddp_stream service call."""
        try:
            wled_host = call.data[CONF_WLED_HOST]
            segment_id = call.data[CONF_SEGMENT_ID]
            clear_display = call.data[CONF_CLEAR_DISPLAY]
            
            _LOGGER.info(
                "stop_ddp_stream service called: host=%s, segment=%d, clear_display=%s",
                wled_host,
                segment_id,
                clear_display,
            )
            
            # Stop the stream
            success = await api.stop_stream(
                wled_host=wled_host,
                segment_id=segment_id,
                clear_display=clear_display,
            )
            
            if success:
                _LOGGER.info("Successfully stopped stream to %s", wled_host)
                
                # Fire success event
                hass.bus.async_fire(
                    f"{DOMAIN}_stopped_ddp_stream",
                    {
                        "wled_host": wled_host,
                        "segment_id": segment_id,
                        "clear_display": clear_display,
                    },
                )
                
                return {
                    "success": True,
                    "wled_host": wled_host,
                    "segment_id": segment_id,
                    "clear_display": clear_display,
                }
            else:
                _LOGGER.error("Failed to stop stream to %s", wled_host)
                return {
                    "success": False,
                    "wled_host": wled_host,
                    "error": "Failed to stop stream",
                }
                
        except Exception as err:
            _LOGGER.error("Error stopping stream: %s", err)
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
        SERVICE_STOP_DDP_STREAM,
        handle_stop_ddp_stream,
        schema=STOP_DDP_STREAM_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    # Ensure background tasks are cleaned up when Home Assistant stops
    async def _handle_shutdown(event) -> None:
        await api.async_close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _handle_shutdown)

    _LOGGER.info("HA DDP2WLED services registered")