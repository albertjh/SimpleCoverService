from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, SIGNAL_AUTOMATION_STATE_CHANGED
from .models import EntryData
from .coordinator import SCSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coord: SCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SCSAutomationSwitch] = []
    for cover_entity, cfg in coord.entry_data.covers.items():
        entities.append(SCSAutomationSwitch(coord, cover_entity))
    async_add_entities(entities)


class SCSAutomationSwitch(SwitchEntity, RestoreEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SCSCoordinator, cover_entity: str) -> None:
        self.coordinator = coordinator
        self._cover = cover_entity
        self._attr_unique_id = f"{coordinator.entry.entry_id}-{cover_entity}-automation"
        self._attr_name = f"Automation {cover_entity}"
        self._is_on = True
        self._unsub = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator.entry.entry_id)},
            "name": "Simple Cover Service (SCS)",
            "manufacturer": "SCS",
            "model": "SCS Controller",
        }

    @property
    def is_on(self) -> bool:
        rt = self.coordinator.entry_data.get_runtime(self._cover)
        return rt.automation_enabled

    async def async_turn_on(self, **kwargs):
        rt = self.coordinator.entry_data.get_runtime(self._cover)
        rt.automation_enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        rt = self.coordinator.entry_data.get_runtime(self._cover)
        rt.automation_enabled = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Restore last state
        if (state := await self.async_get_last_state()) is not None:
            self.coordinator.entry_data.get_runtime(self._cover).automation_enabled = state.state == "on"

        # Listen for dispatcher updates (manual override)
        self._unsub = async_dispatcher_connect(
            self.hass,
            SIGNAL_AUTOMATION_STATE_CHANGED,
            self._handle_automation_signal,
        )

    @callback
    def _handle_automation_signal(self, entry_id: str, cover_entity: str, enabled: bool) -> None:
        if entry_id != self.coordinator.entry.entry_id or cover_entity != self._cover:
            return
        self.coordinator.entry_data.get_runtime(self._cover).automation_enabled = enabled
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
