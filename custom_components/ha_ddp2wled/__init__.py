"""The HA DDP2WLED integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the HA DDP2WLED component."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("HA DDP2WLED component initialized with DDP persistence fixes")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA DDP2WLED from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Register services
    from .services import async_setup_services
    await async_setup_services(hass)

    _LOGGER.info("HA DDP2WLED services registered with enhanced DDP persistence")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True