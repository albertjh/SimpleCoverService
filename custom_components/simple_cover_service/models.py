from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GlobalConfig:
    weather_entity: str | None = None
    sunrise_offset: int = 0
    sunset_offset: int = 0


@dataclass
class CoverConfig:
    cover_entity: str
    temp_sensor: str
    window_azimuth: float
    fov_half: float = 70.0
    default_day: int = 60
    min_day: int = 20
    max_day: int = 100
    default_night: int = 0
    t_min: float = 20.0
    t_max: float = 24.0
    min_delta_position: int = 10
    min_delta_time: int = 300
    invert_position: bool = False
    debug: bool = False


@dataclass
class RuntimeCoverState:
    automation_enabled: bool = True
    last_move_ts: float = 0.0
    last_target: int | None = None
    last_context_id: str | None = None  # for manual override detection


@dataclass
class EntryData:
    global_cfg: GlobalConfig
    covers: dict[str, CoverConfig] = field(default_factory=dict)
    runtime: dict[str, RuntimeCoverState] = field(default_factory=dict)

    def get_runtime(self, cover_entity: str) -> RuntimeCoverState:
        if cover_entity not in self.runtime:
            self.runtime[cover_entity] = RuntimeCoverState()
        return self.runtime[cover_entity]
