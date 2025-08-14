from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event, callback, Context
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    PLATFORMS,
    SIGNAL_AUTOMATION_STATE_CHANGED,
    CONF_GLOBAL,
    CONF_COVERS,
)
from .models import EntryData, GlobalConfig, CoverConfig, RuntimeCoverState
from .coordinator import SCSCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data or {}
    options = entry.options or {}

    global_raw = options.get(CONF_GLOBAL, {})
    covers_raw = options.get(CONF_COVERS, [])

    global_cfg = GlobalConfig(
        weather_entity=global_raw.get("weather_entity"),
        sunrise_offset=int(global_raw.get("sunrise_offset", 0)),
        sunset_offset=int(global_raw.get("sunset_offset", 0)),
    )

    covers: dict[str, CoverConfig] = {}
    for c in covers_raw:
        cc = CoverConfig(
            cover_entity=c["cover_entity"],
            temp_sensor=c["temp_sensor"],
            window_azimuth=float(c["window_azimuth"]),
            fov_half=float(c.get("fov_half", 70)),
            default_day=int(c.get("default_position_day", 60)),
            min_day=int(c.get("min_position_day", 20)),
            max_day=int(c.get("max_position_day", 100)),
            default_night=int(c.get("default_position_night", 0)),
            t_min=float(c.get("t_min", 20)),
            t_max=float(c.get("t_max", 24)),
            min_delta_position=int(c.get("min_delta_position", 10)),
            min_delta_time=int(c.get("min_delta_time", 300)),
            invert_position=bool(c.get("invert_position", False)),
            debug=bool(c.get("debug", False)),
        )
        covers[cc.cover_entity] = cc

    ed = EntryData(global_cfg=global_cfg, covers=covers)

    coord = SCSCoordinator(hass, entry, ed)
    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coord

    # Global state_changed listener for manual override detection
    @callback
    def _handle_state_changed(event: Event) -> None:
        entity_id: str | None = event.data.get("entity_id")
        if not entity_id or entity_id not in coord.entry_data.covers:
            return

        new_state = event.data.get("new_state")
        old_state = event.data.get("old_state")
        if new_state is None or old_state is None:
            return

        # Try to detect a position change
        new_pos = new_state.attributes.get("current_position")
        old_pos = old_state.attributes.get("current_position")
        if new_pos is None or old_pos is None or new_pos == old_pos:
            return

        runtime = coord.entry_data.get_runtime(entity_id)
        last_ctx = runtime.last_context_id
        evt_ctx = event.context.id if event.context else None

        if last_ctx and evt_ctx == last_ctx:
            # Our own move; ignore
            return

        # Manual override detected -> disable automation for this cover
        runtime.automation_enabled = False
        async_dispatcher_send(
            hass, SIGNAL_AUTOMATION_STATE_CHANGED, entry.entry_id, entity_id, False
        )
        _LOGGER.info("SCS: Manual override detected on %s -> automation OFF", entity_id)

    coord.state_listener_remove = hass.bus.async_listen("state_changed", _handle_state_changed)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coord: SCSCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coord.state_listener_remove:
        coord.state_listener_remove()
        coord.state_listener_remove = None
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
