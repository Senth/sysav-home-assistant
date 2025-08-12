from __future__ import annotations
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from yarl import URL

from .const import (
    DOMAIN,
    SUPPORTED_MUNICIPALITIES,
    CONF_MUNICIPALITY,
    CONF_STREET,
    CONF_NUMBER,
    CONF_CITY,
    CONF_API_BASE,
    CONF_LABELS,
    DEFAULT_LABELS,
)
from .api import SysavClient, DiscoveryError, QueryError

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MUNICIPALITY): vol.In(SUPPORTED_MUNICIPALITIES),
        vol.Required(CONF_STREET): str,
        vol.Required(CONF_NUMBER): str,  # hantera även suffix (A, B etc.)
        vol.Required(CONF_CITY): str,
        vol.Optional(CONF_API_BASE, default=""): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

        # Normalisera api-base om angivet
        api_base = user_input.get(CONF_API_BASE, "").strip()
        if api_base:
            try:
                URL(api_base)
            except Exception:
                return self.async_show_form(
                    step_id="user",
                    data_schema=STEP_USER_DATA_SCHEMA,
                    errors={CONF_API_BASE: "invalid_url"},
                )

        # Prova att slå upp adressen en gång i flödet (validering)
        client = SysavClient(api_base=api_base or None)
        try:
            await client.async_validate(
                municipality=user_input[CONF_MUNICIPALITY],
                street=user_input[CONF_STREET],
                number=user_input[CONF_NUMBER],
                city=user_input[CONF_CITY],
            )
        except DiscoveryError:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={CONF_API_BASE: "discovery_failed"},
            )
        except QueryError:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={CONF_STREET: "address_not_found"},
            )
        except Exception:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors={"base": "unknown"},
            )

        # Skapa entry
        return self.async_create_entry(
            title=f"SYSAV – {user_input[CONF_STREET]} {user_input[CONF_NUMBER]}",
            data={
                CONF_MUNICIPALITY: user_input[CONF_MUNICIPALITY],
                CONF_STREET: user_input[CONF_STREET],
                CONF_NUMBER: user_input[CONF_NUMBER],
                CONF_CITY: user_input[CONF_CITY],
                CONF_API_BASE: api_base,
                CONF_LABELS: DEFAULT_LABELS,
            },
        )

    async def async_step_reconfigure(self, user_input=None) -> FlowResult:
        return await self.async_step_user(user_input)
