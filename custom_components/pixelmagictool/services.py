"""Services for Pixel Magic Tool integration."""
from __future__ import annotations

import json
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv, template
from homeassistant.helpers.service import SupportsResponse

from .const import (
    CONF_BRIGHTNESS,
    CONF_COMPRESSION,
    CONF_COMPRESSION_LEVEL,
    CONF_HEIGHT,
    CONF_PATTERN,
    CONF_SEGMENT_ID,
    CONF_TRANSPARENT_COLOR,
    CONF_WLED_HOST,
    CONF_WIDTH,
    CONF_API_URL,
    CONF_USE_CHUNKS,
    CONF_CHUNK_SIZE,
    DEFAULT_BRIGHTNESS,
    DEFAULT_COMPRESSION,
    DEFAULT_COMPRESSION_LEVEL,
    DEFAULT_HEIGHT,
    DEFAULT_PATTERN,
    DEFAULT_SEGMENT_ID,
    DEFAULT_WIDTH,
    DEFAULT_API_URL,
    DEFAULT_USE_CHUNKS,
    DEFAULT_CHUNK_SIZE,
    DOMAIN,
    PATTERNS,
    SERVICE_CONVERT_IMAGE,
    SERVICE_SEND_TO_WLED,
)
from .converter import PixelMagicToolAPI

_LOGGER = logging.getLogger(__name__)

CONVERT_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("image_url"): cv.template,
        vol.Optional(CONF_WIDTH): cv.positive_int,
        vol.Optional(CONF_HEIGHT): cv.positive_int,
        vol.Optional(CONF_BRIGHTNESS, default=DEFAULT_BRIGHTNESS): vol.All(
            cv.positive_int, vol.Range(min=0, max=255)
        ),
        vol.Optional(CONF_PATTERN, default=DEFAULT_PATTERN): vol.In(PATTERNS),
        vol.Optional(CONF_SEGMENT_ID, default=DEFAULT_SEGMENT_ID): cv.positive_int,
        vol.Optional(CONF_TRANSPARENT_COLOR): cv.string,
        vol.Optional(CONF_API_URL, default=DEFAULT_API_URL): cv.string,
        vol.Optional(CONF_COMPRESSION, default=DEFAULT_COMPRESSION): cv.boolean,
        vol.Optional(CONF_COMPRESSION_LEVEL, default=DEFAULT_COMPRESSION_LEVEL): vol.All(
            cv.positive_int, vol.Range(min=1, max=10)
        ),
    }
)

SEND_TO_WLED_SCHEMA = CONVERT_IMAGE_SCHEMA.extend(
    {
        vol.Required(CONF_WLED_HOST): cv.string,
        vol.Optional("timeout", default=10): cv.positive_int,
        vol.Optional(CONF_USE_CHUNKS, default=DEFAULT_USE_CHUNKS): cv.boolean,
        vol.Optional(CONF_CHUNK_SIZE, default=DEFAULT_CHUNK_SIZE): cv.positive_int,
    }
)


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Pixel Magic Tool."""

    async def handle_convert_image(call: ServiceCall) -> dict[str, Any]:
        """Handle the convert_image service call."""
        try:
            # Render template if needed
            image_url_template = call.data["image_url"]
            if isinstance(image_url_template, template.Template):
                image_url = image_url_template.async_render(parse_result=False)
            else:
                image_url = image_url_template

            _LOGGER.info("Converting image from: %s", image_url)

            # Create API client
            api = PixelMagicToolAPI(call.data.get(CONF_API_URL, DEFAULT_API_URL))

            # Convert image using the API
            result = await api.convert_image(
                image_url=image_url,
                segment_id=call.data[CONF_SEGMENT_ID],
                output="json",
                brightness=call.data[CONF_BRIGHTNESS],
                pattern=call.data[CONF_PATTERN],
                width=call.data.get(CONF_WIDTH),
                height=call.data.get(CONF_HEIGHT),
                transparent_color=call.data.get(CONF_TRANSPARENT_COLOR),
            )

            _LOGGER.info("Image conversion successful")

            # Apply compression if enabled
            if call.data.get(CONF_COMPRESSION, DEFAULT_COMPRESSION):
                compression_level = call.data.get(CONF_COMPRESSION_LEVEL, DEFAULT_COMPRESSION_LEVEL)
                _LOGGER.info("Applying compression (level %d)", compression_level)
                result = api.compress_wled_json(result, compression_level)

            # Fire lightweight event for sensor (without large result data)
            hass.bus.async_fire(
                f"{DOMAIN}_conversion_complete",
                {
                    "image_url": image_url,
                    "segment_id": call.data[CONF_SEGMENT_ID],
                    "brightness": call.data[CONF_BRIGHTNESS],
                    "pattern": call.data[CONF_PATTERN],
                },
            )
            
            # Return result as service response
            return {
                "image_url": image_url,
                "wled_json": result,
                "segment_id": call.data[CONF_SEGMENT_ID],
                "brightness": call.data[CONF_BRIGHTNESS],
                "pattern": call.data[CONF_PATTERN],
            }

        except Exception as err:
            _LOGGER.error("Error converting image: %s", err)
            raise

    async def handle_send_to_wled(call: ServiceCall) -> dict[str, Any]:
        """Handle the send_to_wled service call."""
        try:
            # Render template if needed
            image_url_template = call.data["image_url"]
            if isinstance(image_url_template, template.Template):
                image_url = image_url_template.async_render(parse_result=False)
            else:
                image_url = image_url_template

            wled_host = call.data[CONF_WLED_HOST]
            timeout_seconds = call.data["timeout"]

            _LOGGER.info("Converting and sending image to WLED at %s", wled_host)

            # Create API client
            api = PixelMagicToolAPI(call.data.get(CONF_API_URL, DEFAULT_API_URL))

            # Convert image using the API
            result = await api.convert_image(
                image_url=image_url,
                segment_id=call.data[CONF_SEGMENT_ID],
                output="json",
                brightness=call.data[CONF_BRIGHTNESS],
                pattern=call.data[CONF_PATTERN],
                width=call.data.get(CONF_WIDTH),
                height=call.data.get(CONF_HEIGHT),
                transparent_color=call.data.get(CONF_TRANSPARENT_COLOR),
            )

            # Apply compression if enabled
            if call.data.get(CONF_COMPRESSION, DEFAULT_COMPRESSION):
                compression_level = call.data.get(CONF_COMPRESSION_LEVEL, DEFAULT_COMPRESSION_LEVEL)
                _LOGGER.info("Applying compression (level %d)", compression_level)
                result = api.compress_wled_json(result, compression_level)

            # Fire lightweight event for sensor (without large result data)
            hass.bus.async_fire(
                f"{DOMAIN}_conversion_complete",
                {
                    "image_url": image_url,
                    "segment_id": call.data[CONF_SEGMENT_ID],
                    "brightness": call.data[CONF_BRIGHTNESS],
                    "pattern": call.data[CONF_PATTERN],
                },
            )

            # Send to WLED
            try:
                success = await api.send_to_wled(
                    wled_host=wled_host,
                    wled_json=result,
                    timeout=timeout_seconds,
                    use_chunks=call.data.get(CONF_USE_CHUNKS, DEFAULT_USE_CHUNKS),
                    chunk_size=call.data.get(CONF_CHUNK_SIZE, DEFAULT_CHUNK_SIZE),
                )
            except ValueError as err:
                # Payload too large error
                _LOGGER.error("Payload too large for WLED: %s", err)
                return {
                    "success": False,
                    "image_url": image_url,
                    "wled_host": wled_host,
                    "error": str(err),
                    "wled_json": result,  # Still return the JSON in case user wants to handle it
                }

            if success:
                _LOGGER.info("Successfully sent image to WLED")

                # Fire success event
                hass.bus.async_fire(
                    f"{DOMAIN}_sent_to_wled",
                    {
                        "image_url": image_url,
                        "wled_host": wled_host,
                        "segment_id": call.data[CONF_SEGMENT_ID],
                    },
                )
                
                # Return result as service response
                return {
                    "success": True,
                    "image_url": image_url,
                    "wled_host": wled_host,
                    "wled_json": result,
                    "segment_id": call.data[CONF_SEGMENT_ID],
                    "brightness": call.data[CONF_BRIGHTNESS],
                    "pattern": call.data[CONF_PATTERN],
                }
            else:
                _LOGGER.error("Failed to send to WLED")
                return {
                    "success": False,
                    "image_url": image_url,
                    "wled_host": wled_host,
                    "error": "Failed to send to WLED",
                }

        except aiohttp.ClientError as err:
            _LOGGER.error("Network error sending to WLED: %s", err)
            raise
        except Exception as err:
            _LOGGER.error("Error sending to WLED: %s", err)
            raise

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_CONVERT_IMAGE,
        handle_convert_image,
        schema=CONVERT_IMAGE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TO_WLED,
        handle_send_to_wled,
        schema=SEND_TO_WLED_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    _LOGGER.info("Pixel Magic Tool services registered")
