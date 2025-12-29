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
    CONF_HEIGHT,
    CONF_WLED_HOST,
    CONF_WIDTH,
    DEFAULT_BRIGHTNESS,
    DOMAIN,
    SERVICE_SEND_TO_WLED_DDP,
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
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.All(
            cv.positive_int, vol.Range(min=0, max=255)
        ),
        vol.Optional("segment_id", default=0): cv.positive_int,
        vol.Optional("timeout", default=10): cv.positive_int,
        vol.Optional("keepalive_seconds", default=60): vol.All(
            vol.Coerce(float), vol.Range(min=0)
        ),
        vol.Optional("keepalive_interval", default=1): vol.All(
            vol.Coerce(float), vol.Range(min=0.1)
        ),
        # Image processing parameters (WLEDVideoSync compatible)
        vol.Optional("saturation", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("contrast", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("sharpen", default=0.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=1.0)
        ),
        vol.Optional("balance_r", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("balance_g", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("balance_b", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=2.0)
        ),
        vol.Optional("gamma", default=0.5): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=2.0)
        ),
        vol.Optional("auto_bright", default=True): cv.boolean,
        vol.Optional("clip_hist_percent", default=25.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.0, max=50.0)
        ),
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
            brightness = call.data[CONF_BRIGHTNESS]
            segment_id = call.data["segment_id"]
            keepalive_seconds = call.data["keepalive_seconds"]
            keepalive_interval = call.data["keepalive_interval"]

            # Get image processing parameters
            saturation = call.data["saturation"]
            contrast = call.data["contrast"]
            sharpen = call.data["sharpen"]
            balance_r = call.data["balance_r"]
            balance_g = call.data["balance_g"]
            balance_b = call.data["balance_b"]
            gamma = call.data["gamma"]
            auto_bright = call.data["auto_bright"]
            clip_hist_percent = call.data["clip_hist_percent"]

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

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TO_WLED_DDP,
        handle_send_to_wled_ddp,
        schema=SEND_TO_WLED_DDP_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    # Ensure background tasks are cleaned up when Home Assistant stops
    async def _handle_shutdown(event) -> None:
        await api.async_close()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _handle_shutdown)

    _LOGGER.info("HA DDP2WLED services registered")