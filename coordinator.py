from __future__ import annotations
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.config_entries import ConfigEntry

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    CONF_MUNICIPALITY,
    CONF_STREET,
    CONF_NUMBER,
    CONF_CITY,
    CONF_API_BASE,
)
from .api import SysavClient

_LOGGER = logging.getLogger(__name__)


class SysavCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.client = SysavClient(api_base=entry.data.get(CONF_API_BASE) or None)

        super().__init__(
            hass,
            _LOGGER,
            name=f"SYSAV {entry.data.get(CONF_STREET)} {entry.data.get(CONF_NUMBER)}",
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )

    async def _async_update_data(self):
        return await self.client.fetch_next(
            municipality=self.entry.data[CONF_MUNICIPALITY],
            street=self.entry.data[CONF_STREET],
            number=self.entry.data[CONF_NUMBER],
            city=self.entry.data[CONF_CITY],
        )
