# Configuration

The Fleet Dashboard is configured entirely through environment variables in its `docker-compose.yml`. There is no per-card UI configuration - the card grid is built from whatever the env-var parser finds at container start.

This page documents the configuration surface end to end. For the deployment-side walkthrough (wiring rebroadcasters to the dashboard), see [Fleet Monitoring](../user-guides/fleet-monitoring.md).

## Server configuration

| Var | Default | What it does |
|-----|---------|--------------|
| `HOST` | `0.0.0.0` | Listen address for the FastAPI app. Almost always `0.0.0.0`. |
| `PORT` | `8080` | The HTTP listen port. The example compose file overrides to `80`. Note: the dashboard's compose uses `network_mode: host`, so this is the **host port** directly. |

## Per-simulator configuration

The dashboard supports up to 20 simulators. For each, define three env vars (one of them optional):

| Var pattern | Required? | What it does |
|-------------|-----------|--------------|
| `SIM_N_NAME` | Yes | The display name on the card (e.g., `CJ3`, `Ultra`, `CL350`). Free text; spaces are fine. |
| `SIM_N_PORT` | Yes | The UDP port the dashboard listens on for this simulator. **Must match** the rebroadcaster's `AUTO_START_UDP_RETRANSMIT_PORT`. |
| `SIM_N_GPS_SYSTEM` | No (default empty) | The label inserted into the failure message in [Health Chain](health-chain.md) (e.g., `Avionics`, `Avionics 2`, `rehost`). |

`N` is `1`-`20`. The parser walks from 1 to 20 and stops as soon as it sees a gap, so you can't skip - `SIM_1`, `SIM_3` without `SIM_2` means only `SIM_1` gets registered.

### Worked example

```yaml
services:
  dashboard:
    image: rjsears/fleet-dashboard:latest
    pull_policy: always
    container_name: fleet-dashboard
    restart: unless-stopped
    network_mode: host
    environment:
      - HOST=0.0.0.0
      - PORT=80

      - SIM_1_NAME=CJ3
      - SIM_1_PORT=12001
      - SIM_1_GPS_SYSTEM=Avionics

      - SIM_2_NAME=Ultra
      - SIM_2_PORT=12002
      - SIM_2_GPS_SYSTEM=Avionics 2

      - SIM_3_NAME=CJ1
      - SIM_3_PORT=12003
      - SIM_3_GPS_SYSTEM=Avionics

      - SIM_4_NAME=CE560XL
      - SIM_4_PORT=12004
      - SIM_4_GPS_SYSTEM=Avionics 2

      - SIM_5_NAME=Classic CJ1
      - SIM_5_PORT=12005
      - SIM_5_GPS_SYSTEM=Avionics

      - SIM_6_NAME=CL350
      - SIM_6_PORT=12006
      - SIM_6_GPS_SYSTEM=rehost
```

After `docker compose up -d`, the dashboard renders six cards in that order. Each card listens on the corresponding UDP port. The footer shows "6 simulators configured" regardless of how many are currently online.

## Alternative format: single `SIMULATORS` env var

If you don't need per-simulator GPS-system labels, you can compress the configuration into a single `SIMULATORS` variable:

```yaml
environment:
  - SIMULATORS=CJ3:12001,Ultra:12002,CL350:12003
```

Format: `Name:Port` separated by commas. This is mainly for ad-hoc deployments. Anything production-grade should use the full per-simulator block above so you get the GPS-system label.

If both `SIMULATORS` and `SIM_N_*` are set, `SIMULATORS` is used and the `SIM_N_*` block is ignored.

### Default

If neither `SIMULATORS` nor any `SIM_N_*` are set, the dashboard falls back to a default six-simulator list (`CL350`, `Ultra`, `CJ3`, `PC-12`, `King Air`, `Citation X` on ports 12001-12006). This is primarily a "you forgot to configure" safety net - nothing real listens on those ports out of the box, so every card will be gray.

## Compose file conventions

| Setting | Value | Why |
|---------|-------|-----|
| `network_mode: host` | required | The dashboard binds N UDP ports (one per simulator). Host networking avoids mapping every port individually. |
| `restart: unless-stopped` | recommended | The dashboard is meant to live forever; this restart policy survives host reboots without restarting on operator stop. |
| `pull_policy: always` | optional | Pulls the latest tag on every `docker compose up`. Convenient for ongoing deployments; switch to manual pull for stricter environments. |
| `image: rjsears/fleet-dashboard:latest` | the canonical image | Multi-arch (linux/amd64, linux/arm64). |
| `container_name: fleet-dashboard` | optional | Makes `docker compose logs fleet-dashboard` predictable. |

The dashboard does **not** need `/dev` access and is **not** privileged. It also doesn't need access to any persistent volume - state is in-memory.

## Matching the rebroadcasters

For each simulator in the dashboard's compose file, the corresponding rebroadcaster needs these env vars to agree:

| Dashboard | Rebroadcaster |
|-----------|---------------|
| `SIM_N_PORT` | `AUTO_START_UDP_RETRANSMIT_PORT` |
| `SIM_N_NAME` | `AUTO_START_EFB_SIM_NAME` (so the EFB shows the same name as the dashboard card - **optional** but operationally helpful) |
| (no dashboard side) | `AUTO_START_UDP_RETRANSMIT_IP` (set to the dashboard host's IP) |
| `SIM_N_GPS_SYSTEM` | (no rebroadcaster side - this label is dashboard-only) |
| (no dashboard side) | `SIMULATOR_IP` (set to the flight simulator's IP for the `sim_reachable` ping) |

See [Fleet Monitoring](../user-guides/fleet-monitoring.md) for the matching rebroadcaster compose alongside.

## Changing configuration

The dashboard reads all env vars at container start. There is no runtime API to add or rename simulators. To change anything:

1. Edit `docker-compose.yml`.
2. `docker compose up -d` (Compose recreates the container, picking up the new env vars).
3. The dashboard restarts with the new card list. Active browsers reconnect via the WebSocket reconnect logic.

This is intentional - configuration is a deployment-time decision, not a runtime one.

## Time zone

The dashboard does not use the host time zone for anything user-visible (it's a real-time view, not a historical log). There is no `TZ` env var to configure.

## Network ports the dashboard binds

| Port | Bind | Why |
|------|------|-----|
| `PORT` (TCP, default `80`) | The web UI + REST + WebSocket | The whole user-facing surface. |
| `SIM_N_PORT` (UDP, one per simulator, typically `12001`-`12020`) | The per-simulator listener thread | Receives both heartbeats and position packets on the same port; distinguished by JSON payload. |

Because the container uses `network_mode: host`, every one of these binds the **host's** port directly - there's no Docker port-publish step. Confirm nothing else on the host is on those ports before bringing the container up.

## When configuration goes wrong

| Symptom | Likely cause |
|---------|--------------|
| Dashboard shows the default six simulators (CL350, Ultra, CJ3, PC-12, King Air, Citation X) | None of the `SIM_N_*` or `SIMULATORS` env vars made it to the container. Verify the compose file. |
| Some simulators show up but not all | A gap in the `SIM_N_*` numbering (e.g., `SIM_1`, `SIM_3` with no `SIM_2`). The parser stops at the gap. |
| `Address already in use` errors at startup | One of `PORT` or `SIM_N_PORT` is bound by another process on the host. With `network_mode: host`, the dashboard cannot share these ports with anyone else. |
| Failure message says "the simulator" not "on Avionics 2" | `SIM_N_GPS_SYSTEM` is unset for that simulator. Set it. |

## Persistent state

The dashboard has **no persistent state**. Every container restart begins from scratch:

| Thing | Persists? |
|-------|-----------|
| Card configuration | Reads env vars on every start (so persists in `docker-compose.yml`, not in the container's filesystem). |
| Per-card packet counts | Reset to 0 on every container restart. |
| Health states | Computed fresh from the most recent heartbeat / position - no history. |

This is by design - the dashboard is a live view, not a log aggregator. If you need historical data, ingest the heartbeats and position packets into your own time-series store separately.

## What's next

- [Welcome](welcome.md) - manual orientation.
- [Health Chain](health-chain.md) - how `SIM_N_GPS_SYSTEM` shows up in failure messages.
- [Fleet Monitoring](../user-guides/fleet-monitoring.md) - end-to-end deployment with matching rebroadcaster config.
- [Environment Variables](../reference/env-vars.md) - dashboard env-var reference alongside the simulator's.
