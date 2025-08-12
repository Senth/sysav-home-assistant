from __future__ import annotations
from datetime import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SENSOR_DESCRIPTIONS, CONF_LABELS
from .coordinator import SysavCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coord = SysavCoordinator(hass, entry)
    await coord.async_config_entry_first_refresh()

    labels = entry.data.get(CONF_LABELS, {})
    entities: list[SensorEntity] = []
    for key, desc in SENSOR_DESCRIPTIONS.items():
        entities.append(SysavNextSensor(coord, key, desc["name"], desc.get("icon"), labels.get(key, [])))

    async_add_entities(entities)


class SysavNextSensor(SensorEntity):
    _attr_native_unit_of_measurement = None

    def __init__(self, coordinator: SysavCoordinator, key: str, name: str, icon: str | None, aliases: list[str]):
        self._coordinator = coordinator
        self._key = key
        self._aliases = set(aliases)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        if icon:
            self._attr_icon = icon

    @property
    def available(self) -> bool:
        return self._coordinator.last_update_success

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def extra_state_attributes(self):
        data = self._coordinator.data or {}
        for label, payload in data.items():
            if self._match(label):
                return {
                    "label": payload.label,
                    "as_of": datetime.now().isoformat(timespec="seconds"),
                }
        return None

    def _match(self, label: str) -> bool:
        if not label:
            return False
        if label.lower().strip() in (a.lower() for a in self._aliases):
            return True
        # Även exakta nycklar (Kärl 1/Kärl 2)
        if self._key == "karl_1" and "1" in label:
            return True
        if self._key == "karl_2" and "2" in label:
            return True
        return False

    @property
    def native_value(self):
        data = self._coordinator.data or {}
        for label, payload in data.items():
            if self._match(label) and payload.date:
                # Visa som datumsträng YYYY-MM-DD
                return payload.date.date().isoformat()
        return None

    async def async_update(self):
        await self._coordinator.async_request_refresh()

    @property
    def should_poll(self) -> bool:  # type: ignore[override]
        return False

    @property
    def available(self) -> bool:  # type: ignore[override]
        return self._coordinator.last_update_success

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._coordinator.entry.entry_id)},
            "name": "SYSAV Nästa Tömning",
            "manufacturer": "SYSAV (inofficiell)",
        }
