from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DIRECT_SUN_STATES, DOMAIN
from .models import CoverConfig, EntryData
from .util.sun_math import angular_diff_deg

_LOGGER = logging.getLogger(__name__)


class SCSCoordinator(DataUpdateCoordinator[None]):
    """Drives the SCS logic periodically and on-demand."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, entry_data: EntryData) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{entry.entry_id}",
            update_interval=timedelta(minutes=1),
        )
        self.entry = entry
        self.entry_data = entry_data
        self.state_listener_remove = None  # set in __init__.py

    async def _async_update_data(self) -> None:
        """Periodic tick every minute: compute targets and move covers."""
        for cover_entity, cfg in self.entry_data.covers.items():
            runtime = self.entry_data.get_runtime(cover_entity)
            if not runtime.automation_enabled:
                continue

            is_night = self._is_quiet_hours()

            if is_night:
                target = self._clamp(cfg, cfg.default_night)
            else:
                target = await self._compute_day_target(cfg)

            cur = self._get_current_position(cover_entity, cfg)
            if cur is None:
                continue

            if runtime.last_move_ts:
                if (time.time() - runtime.last_move_ts) < cfg.min_delta_time:
                    continue
            if abs(int(target) - int(cur)) < cfg.min_delta_position:
                continue

            await self._set_cover_position(cover_entity, cfg, int(target))

    def _is_quiet_hours(self) -> bool:
        sun = self.hass.states.get("sun.sun")
        if not sun:
            return False
        return sun.state == "below_horizon"

    async def _compute_day_target(self, cfg: CoverConfig) -> int:
        sun = self.hass.states.get("sun.sun")
        if not sun:
            return cfg.default_day

        elev = sun.attributes.get("elevation", 0.0)
        az = sun.attributes.get("azimuth", 0.0)

        direct_sun = False
        if self.entry_data.global_cfg.weather_entity:
            w = self.hass.states.get(self.entry_data.global_cfg.weather_entity)
            if w:
                ws = (w.state or "").lower()
                direct_sun = ws in DIRECT_SUN_STATES
        else:
            direct_sun = True

        sun_in_front = elev > 0 and (angular_diff_deg(float(az), float(cfg.window_azimuth)) <= float(cfg.fov_half))
        if not direct_sun:
            sun_in_front = False

        season = (
            self.hass.states.get("season.season").state
            if self.hass.states.get("season.season")
            else "intermediate"
        )

        t = self.hass.states.get(cfg.temp_sensor)
        try:
            t_in = float(t.state) if t and t.state not in (None, "", "unknown", "unavailable") else None
        except Exception:
            t_in = None

        target = cfg.default_day

        if season == "winter":
            if sun_in_front and (t_in is not None and t_in < cfg.t_min):
                target = cfg.max_day
            else:
                if not direct_sun:
                    target = cfg.max_day
                else:
                    target = max(cfg.default_day, 70)
        else:
            if sun_in_front and (t_in is not None and t_in > cfg.t_max):
                target = cfg.min_day
            else:
                if not direct_sun:
                    target = max(cfg.default_day, 80)
                else:
                    target = cfg.default_day

        return self._clamp(cfg, target)

    def _clamp(self, cfg: CoverConfig, value: int) -> int:
        value = int(value)
        value = max(cfg.min_day, value)
        value = min(cfg.max_day, value)
        return value

    def _get_current_position(self, cover_entity: str, cfg: CoverConfig) -> int | None:
        st = self.hass.states.get(cover_entity)
        if not st:
            return None
        pos = st.attributes.get("current_position")
        if pos is None:
            if st.state in ("open", "opening"):
                pos = 100
            elif st.state in ("closed", "closing"):
                pos = 0
            else:
                return None
        if cfg.invert_position:
            pos = 100 - int(pos)
        return int(pos)

    async def _set_cover_position(self, cover_entity: str, cfg: CoverConfig, target: int) -> None:
        send_pos = 100 - target if cfg.invert_position else target

        ctx = Context()
        await self.hass.services.async_call(
            "cover",
            "set_cover_position",
            {"entity_id": cover_entity, "position": send_pos},
            blocking=False,
            context=ctx,
        )
        runtime = self.entry_data.get_runtime(cover_entity)
        runtime.last_move_ts = time.time()
        runtime.last_target = target
        runtime.last_context_id = ctx.id
        _LOGGER.debug("SCS: set %s -> %s (ctx=%s)", cover_entity, target, ctx.id)