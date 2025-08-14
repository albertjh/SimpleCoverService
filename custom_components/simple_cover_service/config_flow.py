from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_COVERS,
    CONF_COVER_ENTITY,
    CONF_DEBUG,
    CONF_DEFAULT_DAY,
    CONF_DEFAULT_NIGHT,
    CONF_FOV_HALF,
    CONF_GLOBAL,
    CONF_INVERT,
    CONF_MAX_DAY,
    CONF_MIN_DAY,
    CONF_MIN_DELTA_POS,
    CONF_MIN_DELTA_TIME,
    CONF_SUNRISE_OFFSET,
    CONF_SUNSET_OFFSET,
    CONF_T_MAX,
    CONF_T_MIN,
    CONF_TEMP_SENSOR,
    CONF_WEATHER_ENTITY,
    CONF_WINDOW_AZIMUTH,
    DEF_DEFAULT_DAY,
    DEF_DEFAULT_NIGHT,
    DEF_FOV_HALF,
    DEF_MAX_DAY,
    DEF_MIN_DAY,
    DEF_MIN_DELTA_POS,
    DEF_MIN_DELTA_TIME,
    DEF_T_MAX,
    DEF_T_MIN,
    DOMAIN,
)


def _global_schema(hass: HomeAssistant):
    return vol.Schema(
        {
            vol.Optional(
                CONF_WEATHER_ENTITY, default="weather.home"
            ): selector.EntitySelector(selector.EntitySelectorConfig(domain=["weather"])),
            vol.Optional(CONF_SUNRISE_OFFSET, default=0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-120, max=120, step=1, unit_of_measurement="min", mode="box")
            ),
            vol.Optional(CONF_SUNSET_OFFSET, default=0): selector.NumberSelector(
                selector.NumberSelectorConfig(min=-120, max=120, step=1, unit_of_measurement="min", mode="box")
            ),
        }
    )


def _cover_schema(hass: HomeAssistant):
    return vol.Schema(
        {
            vol.Required(CONF_COVER_ENTITY): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["cover"])
            ),
            vol.Required(CONF_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor"])
            ),
            vol.Required(CONF_WINDOW_AZIMUTH): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=359, step=1, mode="box", unit_of_measurement="°")
            ),
            vol.Optional(CONF_FOV_HALF, default=DEF_FOV_HALF): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=90, step=1, mode="slider", unit_of_measurement="°")
            ),
            vol.Optional(CONF_DEFAULT_DAY, default=DEF_DEFAULT_DAY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="slider", unit_of_measurement="%")
            ),
            vol.Optional(CONF_MIN_DAY, default=DEF_MIN_DAY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=99, step=1, mode="slider", unit_of_measurement="%")
            ),
            vol.Optional(CONF_MAX_DAY, default=DEF_MAX_DAY): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=100, step=1, mode="slider", unit_of_measurement="%")
            ),
            vol.Optional(CONF_DEFAULT_NIGHT, default=DEF_DEFAULT_NIGHT): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=100, step=1, mode="slider", unit_of_measurement="%")
            ),
            vol.Optional(CONF_T_MIN, default=DEF_T_MIN): selector.NumberSelector(
                selector.NumberSelectorConfig(min=0, max=40, step=0.5, mode="box", unit_of_measurement="°C")
            ),
            vol.Optional(CONF_T_MAX, default=DEF_T_MAX): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=40, step=0.5, mode="box", unit_of_measurement="°C")
            ),
            vol.Optional(CONF_MIN_DELTA_POS, default=DEF_MIN_DELTA_POS): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=50, step=1, mode="box", unit_of_measurement="%")
            ),
            vol.Optional(CONF_MIN_DELTA_TIME, default=DEF_MIN_DELTA_TIME): selector.NumberSelector(
                selector.NumberSelectorConfig(min=30, max=3600, step=10, mode="box", unit_of_measurement="s")
            ),
            vol.Optional(CONF_INVERT, default=False): selector.BooleanSelector(),
            vol.Optional(CONF_DEBUG, default=False): selector.BooleanSelector(),
        }
    )


class SCSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_global_schema(self.hass))
        options = {
            CONF_GLOBAL: {
                CONF_WEATHER_ENTITY: user_input.get(CONF_WEATHER_ENTITY),
                CONF_SUNRISE_OFFSET: user_input.get(CONF_SUNRISE_OFFSET, 0),
                CONF_SUNSET_OFFSET: user_input.get(CONF_SUNSET_OFFSET, 0),
            },
            CONF_COVERS: [],
        }
        return self.async_create_entry(title="Simple Cover Service (SCS)", data={}, options=options)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SCSOptionsFlowHandler(config_entry)


class SCSOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        return await self.async_step_menu()

    async def async_step_menu(self, user_input=None):
        return self.async_show_menu(
            step_id="menu",
            menu_options=[
                "add_cover",
                "remove_cover",
                "edit_global",
            ],
        )

    async def async_step_add_cover(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="add_cover", data_schema=_cover_schema(self.hass))
        covers = list(self.config_entry.options.get(CONF_COVERS, []))
        covers.append(user_input)
        new_options = dict(self.config_entry.options)
        new_options[CONF_COVERS] = covers
        return self.async_create_entry(title="", data=new_options)

    async def async_step_remove_cover(self, user_input=None):
        covers = list(self.config_entry.options.get(CONF_COVERS, []))
        if not covers:
            return self.async_create_entry(title="", data=self.config_entry.options)
        schema = vol.Schema(
            {
                vol.Required(CONF_COVER_ENTITY): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[c[CONF_COVER_ENTITY] for c in covers],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }
        )
        if user_input is None:
            return self.async_show_form(step_id="remove_cover", data_schema=schema)
        rem = user_input[CONF_COVER_ENTITY]
        covers = [c for c in covers if c[CONF_COVER_ENTITY] != rem]
        new_options = dict(self.config_entry.options)
        new_options[CONF_COVERS] = covers
        return self.async_create_entry(title="", data=new_options)

    async def async_step_edit_global(self, user_input=None):
        if user_input is None:
            schema = _global_schema(self.hass)
            return self.async_show_form(step_id="edit_global", data_schema=schema)
        new_options = dict(self.config_entry.options)
        new_options[CONF_GLOBAL] = user_input
        return self.async_create_entry(title="", data=new_options)
