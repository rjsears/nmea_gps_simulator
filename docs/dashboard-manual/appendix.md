# Appendix (Fleet Dashboard)

Cross-cutting reference for the dashboard side. The simulator appendix has its own counterpart at [User Manual (Simulator) Appendix](../manual/appendix.md).

## Troubleshooting (dashboard side)

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Dashboard UI loads, all cards show OFFLINE | No rebroadcaster is sending position packets to any of the configured ports, **or** the ports in the dashboard don't match the rebroadcasters. | Confirm `SIM_N_PORT` (dashboard) == `AUTO_START_UDP_RETRANSMIT_PORT` (rebroadcaster). `tcpdump -i any 'udp port <port>'` on the dashboard host to confirm arrival. |
| Some cards are online, some are gray | Specific rebroadcasters aren't connected. | Check each rebroadcaster's container status, UDP retransmit settings, and Status Display. |
| Card is green but data is wrong (wrong simulator, wrong heading, etc.) | Two rebroadcasters retransmitting to the same dashboard port. The dashboard accepts whatever arrives last. | Audit `AUTO_START_UDP_RETRANSMIT_PORT` across all rebroadcasters - each must be unique. |
| Dashboard UI itself won't load | Container isn't running, port collision, or you're hitting the wrong host. | `docker compose ps`; verify no other process on the host port; check the host firewall. |
| Browser says "Disconnected" in the header | WebSocket dropped. | The reconnect runs on a 2 s timer; should re-establish on its own. If it persists, the container is down or the WebSocket path is blocked by a reverse proxy. |
| Health view shows the GPS segment red but the rebroadcaster's Output Viewer shows NMEA scrolling | Rebroadcaster's UDP retransmit is off, or pointed at the wrong host. The dashboard sees heartbeats but no position. | Set `AUTO_START_UDP_RETRANSMIT=true` and verify the target IP. |
| Health view says "Is the simulator powered on?" but the sim is on | `SIMULATOR_IP` is wrong, or ICMP is filtered between the rebroadcaster's host and the simulator host. | Set the right IP; allow ICMP echo across the path. |
| All `sim_reachable` are false in health view | None of the rebroadcasters have `SIMULATOR_IP` set, **or** ping is unavailable inside the rebroadcaster container (it shouldn't be - `iputils-ping` is in the image). | Set `SIMULATOR_IP` per rebroadcaster. If still failing, `docker compose exec gps-emulator ping <SIMULATOR_IP>` to confirm from inside. |

## Environment variables (dashboard side, summary)

For the authoritative reference see [Environment Variables](../reference/env-vars.md).

### Server

| Var | Default |
|-----|---------|
| `HOST` | `0.0.0.0` |
| `PORT` | `8080` (overridden to `80` in the example compose file) |

### Per-simulator (one block per simulator, N = 1..20)

| Var | Required | Default |
|-----|----------|---------|
| `SIM_N_NAME` | yes | (none) |
| `SIM_N_PORT` | yes | (none) |
| `SIM_N_GPS_SYSTEM` | no | empty |

### Compact alternative

| Var | Format |
|-----|--------|
| `SIMULATORS` | `Name1:Port1,Name2:Port2,...` |

## API endpoints (dashboard)

Live interactive docs:

| URL | Description |
|-----|-------------|
| `http://<dashboard-host>/api/docs` | Swagger UI |
| `http://<dashboard-host>/api/redoc` | ReDoc |
| `http://<dashboard-host>/api/openapi.json` | OpenAPI JSON |

Endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/status` | Returns the same `fleet_state` payload the WebSocket pushes, in one HTTP call. Useful for scripts / integrations. |
| `WS /ws` | Live WebSocket. Broadcasts a `fleet_state` message every second, plus a `fleet_state` message immediately on connect. |

The dashboard intentionally has a much smaller API than the simulator - everything that's not "read the current state" is operator-private, configured via env vars at deployment time.

## Glossary

| Term | Meaning |
|------|---------|
| **Card** | One simulator's tile in the dashboard grid. |
| **Health view** | The mode where every card's body is replaced with the four-node diagnostic chain. Toggled via the stethoscope icon in the header. |
| **Position view** | The default mode. Cards show lat/lon/altitude/airspeed/heading and the nearest airport. |
| **`sim_reachable`** | Heartbeat field. True if the rebroadcaster's last ICMP ping to `SIMULATOR_IP` succeeded. |
| **`receiving_udp`** | Heartbeat field. True if the rebroadcaster has received a position packet in the last 5 seconds. |
| **`is_online`** | Dashboard-side derived field. True if the dashboard has received a position packet (not a heartbeat) for this card in the last 5 seconds. |
| **`emulator_online`** | Dashboard-side derived field. True if the dashboard has received a heartbeat in the last 3 seconds. |
| **GPS system** | The label inserted into the GPS-segment failure message (e.g., `Avionics 2`). Comes from `SIM_N_GPS_SYSTEM`. |

## What's next

- [Welcome](welcome.md) - manual orientation.
- [Configuration](configuration.md) - env-var reference for the dashboard.
- [Fleet Monitoring](../user-guides/fleet-monitoring.md) - end-to-end multi-simulator deployment walk-through.
- [Troubleshooting](../reference/troubleshooting.md) - the full project-wide troubleshooting matrix.
