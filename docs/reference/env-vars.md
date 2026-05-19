# Environment Variables

Authoritative reference for every environment variable the simulator and the Fleet Dashboard read at container start. Both containers use [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - env vars are matched case-insensitively to the field name in the Settings class.

## Simulator env vars

Source: `backend/config.py`.

### Authentication

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `USERNAME` | string | `admin` | Login username. |
| `PASSWORD` | string | `changeme` | Login password. |
| `BYPASS_AUTH` | bool (`true`/`false`) | `false` | When `true`, skips the login screen and accepts every `/api/*` call without authentication. |

### Default position and ramp rates

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `DEFAULT_LAT` | float | `33.1283` | Initial latitude (decimal degrees, N positive). |
| `DEFAULT_LON` | float | `-117.2803` | Initial longitude (decimal degrees, E positive). |
| `DEFAULT_ALT_FT` | float | `0` | Initial altitude in feet MSL. |
| `DEFAULT_AIRSPEED_KTS` | float | `0` | Initial airspeed in knots. |
| `DEFAULT_HEADING` | float | `360` | Initial heading in degrees true (1-360). |
| `ALTITUDE_RATE_FT_PER_2SEC` | float | `1000` | Maximum altitude change per 2 s. Equivalent to 30,000 ft/min. |
| `AIRSPEED_RATE_KTS_PER_SEC` | float | `30` | Maximum airspeed change per s. |
| `HEADING_RATE_DEG_PER_SEC` | float | `3` | Maximum heading change per s. 3 °/s is a standard-rate turn. |

The defaults are deliberately aggressive (a real jet won't accelerate at 30 kts/s or change altitude at 30,000 ft/min) so demos don't bore the audience. Override to taste.

### Network

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `NETWORK_PORT` | int | `12000` | Currently unused at runtime - the listen port is set per-mode via the UI or via `AUTO_START_LISTEN_PORT`. Kept for backward compatibility. |

### Serial

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `SERIAL_BAUDRATE` | int | `115200` | Default baud rate for the serial picker. Operator can override per run in the UI. |

### EFB

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `FOREFLIGHT_SIM_NAME` | string | `""` | Placeholder simulator name shown in the EFB picker before the operator sets one. Functionally unused once the operator picks a name in the UI or via `AUTO_START_EFB_SIM_NAME`. |

### Auto-start

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `AUTO_START_MODE` | string \| `""` | unset | `rebroadcaster`, `sender`, `receiver`, `standalone`, or empty to disable. **Setting to `false` is NOT valid** - it will fail validation. |
| `AUTO_START_LISTEN_PORT` | int | `12000` | Port to bind for Receiver / Rebroadcaster. |
| `AUTO_START_PROTOCOL` | string | `udp` | `udp` or `tcp`. |
| `AUTO_START_EFB_ENABLED` | bool | `false` | Enable EFB output at boot. |
| `AUTO_START_EFB_BROADCAST` | bool | `false` | Send to broadcast (ForeFlight). |
| `AUTO_START_EFB_TARGET_IPS` | string | `""` | Comma-separated IPs / ranges (see [IP Range Parsing](../user-guides/ip-range-parsing.md)). |
| `AUTO_START_EFB_SIM_NAME` | string | `""` | Required when EFB enabled. |
| `AUTO_START_USB_ENABLED` | bool | `false` | Enable USB output at boot. |
| `AUTO_START_USB_DEVICE` | string | `""` | Path like `/dev/ttyUSB0`. Required when USB enabled. |
| `AUTO_START_UDP_RETRANSMIT` | bool | `false` | Enable UDP retransmit (Rebroadcaster only). |
| `AUTO_START_UDP_RETRANSMIT_IP` | string | `""` | Target IP - typically the Fleet Dashboard host. |
| `AUTO_START_UDP_RETRANSMIT_PORT` | int | `12001` | Target port - matches the dashboard's `SIM_N_PORT`. |
| `SIMULATOR_IP` | string | `""` | IP of the upstream flight simulator. The rebroadcaster pings this once per second; result lands in the heartbeat as `sim_reachable`. |

### Container-runtime

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `TZ` | string | host-default | Sets the container's timezone. Affects `GPZDA` and log timestamps. |

## Fleet Dashboard env vars

Source: `dashboard/backend/config.py`.

### Server

| Var | Type | Default | Description |
|-----|------|---------|-------------|
| `HOST` | string | `0.0.0.0` | Listen address for the FastAPI app. |
| `PORT` | int | `8080` | HTTP listen port. The example compose overrides to `80`. |

### Per-simulator (one block per simulator, `N` = 1..20)

| Var | Type | Required | Description |
|-----|------|----------|-------------|
| `SIM_N_NAME` | string | yes | Card title (e.g., `CJ3`, `Ultra`, `CL350`). Free text, spaces OK. |
| `SIM_N_PORT` | int | yes | UDP port the dashboard binds for this simulator. **Must match** the rebroadcaster's `AUTO_START_UDP_RETRANSMIT_PORT`. |
| `SIM_N_GPS_SYSTEM` | string | no | Label inserted into the GPS-segment failure message ("Restart GPSConnect on `<value>`"). |

The parser walks from 1 to 20 and stops on the first gap. So `SIM_1`, `SIM_3` (no `SIM_2`) registers only `SIM_1`.

### Compact alternative (no GPS-system label)

| Var | Type | Description |
|-----|------|-------------|
| `SIMULATORS` | string | `Name1:Port1,Name2:Port2,...`. When set, this is used and the `SIM_N_*` block is ignored. |

### Default fallback

If neither `SIMULATORS` nor any `SIM_N_NAME` is set, the dashboard falls back to a built-in list of six aircraft (`CL350`, `Ultra`, `CJ3`, `PC-12`, `King Air`, `Citation X` on ports 12001-12006). This is a safety net - nothing real is on those ports out of the box.

## Boolean parsing

Both apps use pydantic-settings' bool coercion. Accepted truthy values:

| Truthy | Falsy |
|--------|-------|
| `true`, `True`, `TRUE`, `1`, `yes`, `y`, `on` | `false`, `False`, `FALSE`, `0`, `no`, `n`, `off`, empty string |

For `AUTO_START_MODE` specifically, **this does not apply** - it's a string enum, not a bool. `false` is parsed as the literal string `"false"`, which fails the enum validation. Leave it blank or omit to disable.

## Reading env vars from a `.env` file

The simulator's `pydantic-settings` config has `env_file=".env"`. Drop a file named `.env` in the working directory and the container will read it (in addition to compose's `environment:` block). The compose block wins on conflicts.

This is mostly useful for local development outside Docker. Inside Docker, prefer the compose-file `environment:` block - it's easier to audit.

## Worked: a complete simulator compose env block

```yaml
environment:
  # Authentication
  - USERNAME=admin
  - PASSWORD=YourSecretPassword
  - BYPASS_AUTH=false

  # Default position + ramp rates
  - DEFAULT_LAT=33.1283
  - DEFAULT_LON=-117.2803
  - DEFAULT_ALT_FT=0
  - DEFAULT_AIRSPEED_KTS=0
  - DEFAULT_HEADING=360
  - ALTITUDE_RATE_FT_PER_2SEC=1000
  - AIRSPEED_RATE_KTS_PER_SEC=30
  - HEADING_RATE_DEG_PER_SEC=3

  # Serial default
  - SERIAL_BAUDRATE=115200

  # EFB display name placeholder
  - FOREFLIGHT_SIM_NAME=

  # Timezone (affects GPZDA + log timestamps)
  - TZ=America/Los_Angeles

  # Auto-start as Rebroadcaster
  - AUTO_START_MODE=rebroadcaster
  - AUTO_START_LISTEN_PORT=12000
  - AUTO_START_PROTOCOL=udp

  - AUTO_START_EFB_ENABLED=true
  - AUTO_START_EFB_BROADCAST=false
  - AUTO_START_EFB_TARGET_IPS=10.200.40.198
  - AUTO_START_EFB_SIM_NAME=CL350

  - AUTO_START_USB_ENABLED=false
  - AUTO_START_USB_DEVICE=

  - AUTO_START_UDP_RETRANSMIT=true
  - AUTO_START_UDP_RETRANSMIT_IP=10.200.40.3
  - AUTO_START_UDP_RETRANSMIT_PORT=12001

  - SIMULATOR_IP=10.200.50.11
```

## Worked: a complete dashboard compose env block

```yaml
environment:
  - HOST=0.0.0.0
  - PORT=80

  - SIM_1_NAME=CJ3
  - SIM_1_PORT=12001
  - SIM_1_GPS_SYSTEM=Avionics

  - SIM_2_NAME=Ultra
  - SIM_2_PORT=12002
  - SIM_2_GPS_SYSTEM=Avionics 2

  - SIM_3_NAME=CL350
  - SIM_3_PORT=12003
  - SIM_3_GPS_SYSTEM=rehost
```

## What's next

- [Auto-Start](../user-guides/auto-start.md) - validation rules for `AUTO_START_*` vars.
- [Configuration (Fleet Dashboard)](../dashboard-manual/configuration.md) - dashboard-side env-var walkthrough.
- [Fleet Monitoring](../user-guides/fleet-monitoring.md) - matching vars across rebroadcaster + dashboard.
- [Security](security.md) - hardening guidance, especially around `USERNAME` / `PASSWORD` / `BYPASS_AUTH`.
