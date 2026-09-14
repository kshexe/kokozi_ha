"""The Kokozi integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import KokoziConfigEntry, KokoziDataUpdateCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.MEDIA_PLAYER,
    Platform.NUMBER,
    Platform.SENSOR,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: KokoziConfigEntry
) -> bool:
    """Set up Kokozi from a config entry."""
    coordinator = KokoziDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: KokoziConfigEntry
) -> bool:
    """Unload a Kokozi config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
