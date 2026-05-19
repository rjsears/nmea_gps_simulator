# Appendix

This appendix collects the cross-cutting reference content that doesn't belong inside any single feature page. The deep reference pages (full env-var table, full troubleshooting matrix, security checklist) are linked from here rather than duplicated.

## Troubleshooting (simulator UI side)

For each common symptom, a likely cause and the fastest fix. For everything else, see [Troubleshooting](../reference/troubleshooting.md).

### Won't start, button is disabled

| Tooltip / error | Fix |
|-----------------|-----|
| Select an operating mode | Click one of the four mode tabs. |
| Select an airport | Open the airport picker in the Position panel and pick one. |
| Select at least one output | Toggle on USB and/or EFB in the active mode's panel. |
| Enter target IP address for NMEA output | Fill in the **Target IP** field in Sender Settings' NMEA block. |
| Select a USB device | Open the serial picker and pick a `/dev/...` path; press **Refresh** if the list looks empty. |
| Enter a simulator name for EFB output | The EFB block needs a Simulator Name when enabled. |
| Enter IP address(es) for EFB output | EFB IP targeting needs at least one IP in the target-IPs field. |
| Select Broadcast or Garmin Pilot/ForeFlight (IP Address) | EFB master is on but neither sub-option is checked. |
| Enter target IP for UDP retransmit | Rebroadcaster's UDP retransmit block needs a target IP. |

### Won't start, server error after pressing Start

| Banner | Cause | Fix |
|--------|-------|-----|
| `Failed to open serial port: [Errno 2] could not open port` | Selected device doesn't exist (was unplugged, never enumerated) | `docker compose exec gps-emulator ls /dev/tty*` to check. Restart the container after plugging the device. |
| `Failed to open serial port: [Errno 13] Permission denied` | Container lacks `/dev` access | Confirm `privileged: true` and `-v /dev:/dev` in compose. |
| `Address already in use` (Receiver / Rebroadcaster) | Listen port collided with another process or container | Pick a different port or stop the other process. |
| `Connection refused` (Sender, TCP) | Receiver isn't running at the target IP:port | Start the receiver first; verify the target IP/port. |

### Output appears but downstream doesn't see it

| Symptom | Likely cause |
|---------|--------------|
| Output Viewer scrolling, EFB silent | iPad not on the same L2 segment; AP isolation; Garmin Pilot configured with broadcast (it doesn't support that). See [Connecting ForeFlight](../user-guides/connecting-foreflight.md) / [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md). |
| Output Viewer scrolling, Bad Elf silent | Wrong baud, wrong cable, RX/TX swap. See [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md). |
| Output Viewer scrolling, Fleet Dashboard card stays gray | UDP retransmit not enabled, port mismatch with `SIM_N_PORT`, or firewall on the dashboard host. See [Fleet Monitoring](../user-guides/fleet-monitoring.md). |
| `tcpdump` shows "bad udp cksum" warnings on a Linux receiver | TX checksum offload on the sending NIC. See [TX Checksum Offload Fix](../user-guides/tx-checksum-offload.md). |

## Security flag index

Screenshots in this manual are captured from real running deployments and then redacted per the operator's screen-capture playbook. The fields that get blurred or replaced before publication:

| Field | What to redact | Why |
|-------|----------------|-----|
| Real EFB target IPs (e.g., `10.200.40.198`) | Replace with example-range IPs (`10.200.40.10`-style placeholders) or blur | These point at real iPads in a training facility. |
| Real simulator IPs (`SIMULATOR_IP` env var values) | Blur in screenshots; document with placeholders in prose | Same reason. |
| Real `USERNAME` / `PASSWORD` values | Never appear in screenshots if `BYPASS_AUTH=true`. If the Login screen is captured with credentials, blur them. | Obvious. |
| Real Fleet Dashboard IP (`AUTO_START_UDP_RETRANSMIT_IP`) | Same as EFB IPs - placeholder or blur. | Maps the lab network. |
| `docker-compose.yml` excerpts that include the above values | Replace with example values before screenshotting | Same reason. |

The capture playbook itself is in `project_docs/screen_capture.md` (operator-only, not published).

## Environment variables (summary)

The simulator reads these env vars at container start. For the authoritative reference with defaults, ranges, and side-effects, see [Environment Variables](../reference/env-vars.md).

### Authentication

| Var | Default |
|-----|---------|
| `USERNAME` | `admin` |
| `PASSWORD` | `changeme` |
| `BYPASS_AUTH` | `false` (example file ships with `true`) |

### Defaults

| Var | Default |
|-----|---------|
| `DEFAULT_LAT` | `33.1283` (KCRQ) |
| `DEFAULT_LON` | `-117.2803` |
| `DEFAULT_ALT_FT` | `0` |
| `DEFAULT_AIRSPEED_KTS` | `0` |
| `DEFAULT_HEADING` | `360` |

### Transition rates

| Var | Default |
|-----|---------|
| `ALTITUDE_RATE_FT_PER_2SEC` | `1000` |
| `AIRSPEED_RATE_KTS_PER_SEC` | `30` |
| `HEADING_RATE_DEG_PER_SEC` | `3` |

### Auto-start

| Var | Default | Notes |
|-----|---------|-------|
| `AUTO_START_MODE` | empty | `rebroadcaster`, `sender`, `receiver`, `standalone`, or empty/missing to disable |
| `AUTO_START_LISTEN_PORT` | `12000` | Receiver / Rebroadcaster only |
| `AUTO_START_PROTOCOL` | `udp` | Receiver / Rebroadcaster only |
| `AUTO_START_EFB_ENABLED` | `false` | |
| `AUTO_START_EFB_BROADCAST` | `false` | |
| `AUTO_START_EFB_TARGET_IPS` | empty | Comma-separated list / ranges |
| `AUTO_START_EFB_SIM_NAME` | empty | Required when EFB enabled |
| `AUTO_START_USB_ENABLED` | `false` | |
| `AUTO_START_USB_DEVICE` | empty | |
| `AUTO_START_UDP_RETRANSMIT` | `false` | Rebroadcaster only |
| `AUTO_START_UDP_RETRANSMIT_IP` | empty | |
| `AUTO_START_UDP_RETRANSMIT_PORT` | `12001` | |
| `SIMULATOR_IP` | empty | For health-monitoring ping; surfaces in Fleet Dashboard heartbeat |

### Serial

| Var | Default |
|-----|---------|
| `SERIAL_BAUDRATE` | `115200` |

### Other

| Var | Default |
|-----|---------|
| `FOREFLIGHT_SIM_NAME` | empty (placeholder shown in UI when empty) |
| `TZ` | `America/Los_Angeles` (set in the example compose file) |

## API endpoint summary

Live interactive docs (Swagger UI, ReDoc, raw OpenAPI JSON):

| URL | Description |
|-----|-------------|
| `http://<host>/api/docs` | Swagger UI - interactive "try it out" explorer |
| `http://<host>/api/redoc` | ReDoc - read-only structured reference |
| `http://<host>/api/openapi.json` | Raw OpenAPI 3.x spec |

Endpoints, grouped by tag:

| Tag | Endpoints |
|-----|-----------|
| Auth | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/check` |
| Control | `GET /api/status`, `POST /api/control`, `POST /api/position` |
| Configuration | `POST /api/config/modes`, `POST /api/config/network`, `POST /api/config/nmea`, `POST /api/config/serial` |
| Serial | `GET /api/serial/devices`, `POST /api/serial/select` |
| Airports | `GET /api/airports/lookup/{icao}`, `GET /api/airports/search`, `GET /api/airports/list` |
| WebSocket | `WS /ws` |
| Health | `GET /health` (unauthenticated; for Docker healthchecks) |

See [API Reference](../reference/api-reference.md) for the full reference, including request/response bodies.

## Glossary

| Term | Meaning |
|------|---------|
| **CYGNUS** | A `key=value` string position format used by some flight simulators. The Receiver auto-detects it alongside JSON. |
| **EFB** | Electronic Flight Bag. ForeFlight and Garmin Pilot are the two the simulator targets. |
| **Heartbeat** | A 1 Hz JSON packet a Rebroadcaster sends to the Fleet Dashboard, carrying `sim_reachable`, `receiving_udp`, and uptime. |
| **NMEA-0183** | The serial position protocol. Sentences are ASCII strings starting with `$` and ending with `*<checksum>\r\n`. |
| **Rebroadcaster** | Receiver + fan-out to multiple downstream outputs (USB, EFB, UDP retransmit). |
| **Sender** | A mode that generates position locally and publishes it over UDP or TCP. |
| **Sim_reachable** | A heartbeat field that's true when ICMP ping to `SIMULATOR_IP` from inside the container succeeds. |
| **Stand-Alone** | The simplest mode - generates locally, drives USB and/or EFB, no network ingest or publish. |
| **XGPS** | The EFB protocol on UDP 49002. One ASCII line per second: `XGPS{name},{lon},{lat},{alt_m},{track},{speed_ms}`. |

## What's next

- [Troubleshooting](../reference/troubleshooting.md) - the full symptom -> cause -> fix matrix.
- [Environment Variables](../reference/env-vars.md) - authoritative env-var reference.
- [API Reference](../reference/api-reference.md) - full API documentation with the three live doc URLs.
- [Security](../reference/security.md) - hardening checklist and authentication model.
