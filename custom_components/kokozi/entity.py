"""Base entities for Kokozi."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KokoziDataUpdateCoordinator


class KokoziEntity(CoordinatorEntity[KokoziDataUpdateCoordinator]):
    """Base Kokozi entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KokoziDataUpdateCoordinator,
        unique_id: str,
        device_info: DeviceInfo,
        entity_domain: str | None = None,
        object_id: str | None = None,
    ) -> None:
        """Initialize the entity.

        entity_id is left for Home Assistant to auto-generate from the
        device/entity name (its slugify() romanizes Korean text fine, e.g.
        "코코지 하우스" -> "kokoji_hauseu"). entity_domain/object_id are kept
        as accepted-but-unused parameters for call-site compatibility.
        """
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info


def house_device_info(house: dict[str, Any]) -> DeviceInfo:
    """Return device info for a Kokozi House."""
    house_id = house["_id"]
    firmware = house.get("firmware") or {}
    return DeviceInfo(
        identifiers={(DOMAIN, f"house_{house_id}")},
        name=house.get("name") or "Kokozi House",
        manufacturer="Kokozi",
        model=house.get("device_type") or "kokozi-house",
        sw_version=firmware.get("version"),
    )


def arti_group_device_info() -> DeviceInfo:
    """Return the shared device info grouping all Arti binary sensors."""
    return DeviceInfo(
        identifiers={(DOMAIN, "arti_group")},
        name="아띠",
        manufacturer="Kokozi",
        model="아띠",
    )
