"""The WLEDVideoSync integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .ddp import DDPClient

_LOGGER = logging.getLogger(__name__)

# Global dictionary to track active streaming sessions
# Format: {session_id: DDPClient}
STREAMING_SESSIONS: dict[str, DDPClient] = {}


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the WLEDVideoSync component."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["streaming_sessions"] = STREAMING_SESSIONS
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WLEDVideoSync from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    hass.data[DOMAIN]["streaming_sessions"] = STREAMING_SESSIONS

    # Register services
    from .services import async_setup_services
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop all active streaming sessions
    sessions = hass.data[DOMAIN].get("streaming_sessions", {})
    for session_id, ddp_client in list(sessions.items()):
        try:
            _LOGGER.info("Stopping streaming session %s on unload", session_id)
            await ddp_client.stop_streaming()
        except Exception as err:
            _LOGGER.warning("Error stopping streaming session %s: %s", session_id, err)
        finally:
            sessions.pop(session_id, None)
    
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
