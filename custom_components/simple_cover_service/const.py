from __future__ import annotations

DOMAIN = "simple_cover_service"
PLATFORMS = ["switch"]

CONF_GLOBAL = "global"
CONF_COVERS = "covers"

# Global config keys
CONF_WEATHER_ENTITY = "weather_entity"
CONF_SUNRISE_OFFSET = "sunrise_offset"
CONF_SUNSET_OFFSET = "sunset_offset"

# Per-cover keys
CONF_COVER_ENTITY = "cover_entity"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_WINDOW_AZIMUTH = "window_azimuth"
CONF_FOV_HALF = "fov_half"
CONF_DEFAULT_DAY = "default_position_day"
CONF_MIN_DAY = "min_position_day"
CONF_MAX_DAY = "max_position_day"
CONF_DEFAULT_NIGHT = "default_position_night"
CONF_T_MIN = "t_min"
CONF_T_MAX = "t_max"
CONF_MIN_DELTA_POS = "min_delta_position"
CONF_MIN_DELTA_TIME = "min_delta_time"
CONF_INVERT = "invert_position"
CONF_DEBUG = "debug"

# Defaults (confirmed by you)
DEF_T_MIN = 20.0
DEF_T_MAX = 24.0
DEF_DEFAULT_DAY = 60
DEF_MIN_DAY = 20
DEF_MAX_DAY = 100
DEF_DEFAULT_NIGHT = 0
DEF_SUNRISE_OFFSET = 0
DEF_SUNSET_OFFSET = 0
DEF_FOV_HALF = 70
DEF_MIN_DELTA_POS = 10
DEF_MIN_DELTA_TIME = 300
DEF_INVERT = False
DEF_DEBUG = False

# Weather states treated as direct sun
DIRECT_SUN_STATES = {"sunny", "partlycloudy"}

# Dispatcher signals
SIGNAL_AUTOMATION_STATE_CHANGED = "scs_automation_state_changed"
