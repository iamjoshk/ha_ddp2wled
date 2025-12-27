"""Sensor platform for Pixel Magic Tool."""
from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_BRIGHTNESS,
    ATTR_DIMENSIONS,
    ATTR_LAST_CONVERSION,
    ATTR_LAST_IMAGE_URL,
    ATTR_SEGMENT_ID,
    ATTR_WLED_JSON,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pixel Magic Tool sensor."""
    async_add_entities([PixelMagicToolSensor(config_entry)], True)


class PixelMagicToolSensor(SensorEntity):
    """Sensor to store the last converted image data."""

    _attr_has_entity_name = True
    _attr_name = "Last Conversion"
    _attr_icon = "mdi:image-edit"

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}_last_conversion"
        self._state = "idle"
        self._last_image_url: str | None = None
        self._wled_json: dict | None = None
        self._segment_id: int | None = None
        self._brightness: int | None = None
        self._dimensions: str | None = None

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        
        # Listen for conversion events
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_conversion_complete",
                self._handle_conversion_complete,
            )
        )

    @property
    def device_info(self):
        """Return device information about this entity."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": self._config_entry.data.get("name", "Pixel Magic Tool"),
            "manufacturer": "Pixel Magic Tool",
            "model": "Image Converter",
            "sw_version": "1.0.0",
        }

    @property
    def state(self) -> str:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = {}
        
        if self._last_image_url:
            attrs[ATTR_LAST_IMAGE_URL] = self._last_image_url
            
        # Note: WLED JSON is no longer stored in sensor attributes to avoid database size issues
        # Users should access the conversion result via service response data instead
        # attrs[ATTR_WLED_JSON] is intentionally omitted
            
        if self._segment_id is not None:
            attrs[ATTR_SEGMENT_ID] = self._segment_id
            
        if self._brightness is not None:
            attrs[ATTR_BRIGHTNESS] = self._brightness
            
        if self._dimensions:
            attrs[ATTR_DIMENSIONS] = self._dimensions
            
        return attrs

    @callback
    def _handle_conversion_complete(self, event) -> None:
        """Handle conversion complete event."""
        data = event.data
        
        self._last_image_url = data.get("image_url")
        self._segment_id = data.get("segment_id")
        self._brightness = data.get("brightness")
        
        # Note: wled_json is no longer included in the event to avoid database size issues
        # Users should access the conversion result via service response data instead
        self._wled_json = None
        self._state = "converted"
            
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the sensor - not needed as we use events."""
        pass
