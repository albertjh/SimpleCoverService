# Simple Cover Service (SCS)

Ultra-simple automatic control for vertical blinds using sun + weather + indoor temperature.

Goals
- No mid‑day full closures unless you want them
- Night rule: from sunset to sunrise blinds go to your defined night position
- Day rule: predictable summer/winter behavior with minimal options

Key features
- Per-cover automation switch
- Manual override: any manual change disables automation for that cover
- Uses: `sun.sun`, `season.season`, `weather.home` (configurable), plus your indoor temperature sensor
- Quiet hours: sunset → sunrise
- Movement smoothing: min delta position and min delta time

Install (HACS)
1. HACS → Integrations → Custom repositories → URL: https://github.com/simple-cover-service/simple_cover_service, Category: Integration
2. Install “Simple Cover Service (SCS)”
3. Restart Home Assistant
4. Settings → Devices & Services → Add Integration → Simple Cover Service (SCS)
   - Pick `weather.home` (or another), offsets 0/0
   - After created, open “Configure” and add covers one by one:
     - Cover entity, temp sensor, window azimuth, FOV (70° default), day/night defaults, min/max clamps

Notes
- Season comes from `season.season` (auto hemisphere).
- If a cover doesn’t expose `current_position`, SCS falls back to open/closed; percentage control is recommended.
- Inversion: if a cover reports 100% = closed, enable “Invert position”.

License: MIT
