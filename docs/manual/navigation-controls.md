# Navigation Controls

The **Position** panel (airport picker) plus the **Navigation** panel (altitude / airspeed / heading) together drive the position the simulator publishes. They sit in the center column of the dashboard and apply to **every mode that originates position locally** - Stand-Alone, Sender, and the source-side of the engine in general. In Receiver mode they're disabled because position is inherited from the upstream packet.

<!-- SCREENSHOT-PENDING: navigation-01-overview.png - Position panel plus Navigation panel with sliders and compass dial. -->

## The Position panel (airport picker)

| Control | Default | What it does |
|---------|---------|--------------|
| **Airport ICAO** text input | empty (placeholder `KCRQ`) | Filters the airport database as you type. Search debounces at 200 ms and asks `/api/airports/search`. |
| **Dropdown of results** | hidden until typing | Up to 10 matches. Each row shows the ICAO + airport name. |
| **Selected airport card** | hidden until selected | Blue panel showing the picked ICAO, full name, and elevation. |

Picking an airport from the dropdown updates four values in one call:

| Field | Source |
|-------|--------|
| `lat` | From the airport record (decimal degrees, N positive) |
| `lon` | From the airport record (decimal degrees, E positive) |
| `altitude_ft` | Set to the **airport elevation** - so altitude starts at field elevation, not 0 |
| `airport_icao` | Set to the ICAO code (used later for display + server-side state) |

Once an airport is selected the Start button's "Select an airport" validation clears.

See [Airport Lookup](airport-lookup.md) for the underlying database and the search algorithm.

## The Navigation panel (altitude, airspeed, heading)

Three controls. Each one sets a **target value** that the NMEA engine ramps toward at a configurable rate.

| Control | Default | Range | Step | Unit |
|---------|---------|-------|------|------|
| **Altitude** slider | from `DEFAULT_ALT_FT` env var or the picked airport's elevation | 0 - 50,000 | 100 | ft MSL |
| **Airspeed** slider | from `DEFAULT_AIRSPEED_KTS` env var or 0 | 0 - 600 | 5 | kts |
| **Heading** dial **and** slider | from `DEFAULT_HEADING` env var or 360 | 1 - 360 | 1 | degrees true |

The heading control is unusual: a compass dial **and** a slider, both bound to the same value. Drag the dial OR move the slider - whichever feels better at that moment.

### The compass dial

A 120px SVG widget with:

| Element | Meaning |
|---------|---------|
| Outer circle | Reference ring. |
| Cardinal letters (N / E / S / W) | At 12 / 3 / 6 / 9 o'clock. |
| Tick marks | One every 10 degrees; thicker every 90 degrees. |
| Blue needle | Points to the current heading (true). |
| Center dot | Pivot. |
| Heading text below the dial | Numeric current value, e.g., `270°`. |

Click and drag anywhere inside the dial to rotate the needle. The math converts the click's angle relative to the center into a 1-360 heading (with 0 normalized to 360 so "North" reads as `360°` not `0°`).

!!! tip "Heading is true, not magnetic"
    The simulator emits true heading. If your downstream device wants magnetic, you'll need a magnetic-variation correction on its side. The simulator does not apply a variation - real-world variation for a given lat/lon is intentionally outside its scope.

## The ramp behavior

Sliding the altitude from 0 to 35,000 does **not** teleport. The engine sets a new *target* and ramps the *current* value at the rate configured by env vars:

| Quantity | Env var | Default | Meaning |
|----------|---------|---------|---------|
| Altitude rate | `ALTITUDE_RATE_FT_PER_2SEC` | `1000` | Feet per 2 seconds. The denominator is 2 because climbs are most intuitive in ft/min - 1000 ft / 2 s is 30,000 ft/min, the order of magnitude of a fast jet's climb rate. |
| Airspeed rate | `AIRSPEED_RATE_KTS_PER_SEC` | `30` | Knots per second. 30 kts/s is aggressive; real aircraft are closer to 5 kts/s. Tune it for the use case. |
| Heading rate | `HEADING_RATE_DEG_PER_SEC` | `3` | Degrees per second. 3°/s is a standard-rate turn (180° in a minute). |

The ramp logic lives in `backend/nmea/transitions.py`. It uses the *shortest* path for heading - so going from 350° to 10° turns 20° east, not 340° west.

### Worked example

Starting at altitude 0, airspeed 0, heading 360. You set altitude 35000, airspeed 250, heading 90.

| t = (s) | Altitude (ft) | Airspeed (kts) | Heading (°) |
|---------|---------------|----------------|-------------|
| 0 | 0 | 0 | 360 |
| 2 | 1,000 | 60 | 354 |
| 4 | 2,000 | 120 | 348 |
| ... | ... | ... | ... |
| 30 | 15,000 | 250 (capped) | 270 |
| 60 | 30,000 | 250 | 90 (capped) |
| 70 | 35,000 (capped) | 250 | 90 |

Each row is one NMEA tick. The Output Viewer reflects every step.

## When to change the transition rates

| Use case | Suggested rate set |
|----------|-------------------|
| Realistic airliner climb / cruise | `ALTITUDE_RATE_FT_PER_2SEC=200` (about 6000 ft/min - aggressive but believable), `AIRSPEED_RATE_KTS_PER_SEC=5`, `HEADING_RATE_DEG_PER_SEC=3` |
| Demo speed (audience won't wait for a real climb) | Defaults are intentionally fast - leave as-is. |
| Helicopter or low-speed prop demonstration | `ALTITUDE_RATE_FT_PER_2SEC=100`, `AIRSPEED_RATE_KTS_PER_SEC=2`, `HEADING_RATE_DEG_PER_SEC=5` |
| Snap to value (no ramp - for screenshots) | Set all three rates to large numbers and the engine reaches target within one tick. |

These are env vars only - no UI control - because they're a deployment-time decision.

## Receiver-mode behavior

In Receiver mode, the Position and Navigation panels are disabled (grayed out). Lat/lon, altitude, airspeed, and heading all come from the upstream packet on every tick. The local engine still smooths through `transitions.py` between successive packets, using the same rate env vars.

If the upstream Sender ships a teleport-level jump, the Receiver still ramps to the new value - so even an erratic source produces smooth NMEA downstream.

## What changes when sliding while running

| State | Slider behavior |
|-------|-----------------|
| Stopped | The slider updates immediate target. Pressing Start will emit using the new target. |
| Running, Stand-Alone or Sender | The new target takes effect on the next tick. The engine ramps toward it. The Output Viewer shows the progression. |
| Running, Receiver | Sliders are disabled (the panel is grayed out anyway). |

## Persistent state

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| Initial lat / lon | Airport picker / direct entry | `DEFAULT_LAT`, `DEFAULT_LON` | Yes (env var, used at boot) |
| Initial altitude | Slider | `DEFAULT_ALT_FT` | Yes (env var) |
| Initial airspeed | Slider | `DEFAULT_AIRSPEED_KTS` | Yes (env var) |
| Initial heading | Compass dial / slider | `DEFAULT_HEADING` | Yes (env var) |
| Altitude ramp rate | (no UI) | `ALTITUDE_RATE_FT_PER_2SEC` | Yes (env var, used at boot and after) |
| Airspeed ramp rate | (no UI) | `AIRSPEED_RATE_KTS_PER_SEC` | Yes (env var) |
| Heading ramp rate | (no UI) | `HEADING_RATE_DEG_PER_SEC` | Yes (env var) |

## What's next

- [Airport Lookup](airport-lookup.md) - the airport database and how to query it directly via the API.
- [Output Viewer](output-viewer.md) - watch the ramp behavior live.
- [Status Display](status-display.md) - current vs target values, side by side.
- [Environment Variables](../reference/env-vars.md) - authoritative reference for the rate and default env vars.
