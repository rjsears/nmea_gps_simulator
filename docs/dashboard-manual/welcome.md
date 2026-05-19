# Welcome to the Fleet Dashboard Manual

The **Fleet Dashboard** is the companion container to the NMEA GPS Simulator. It aggregates per-simulator position telemetry and heartbeats from many rebroadcasters into a single screen, with click-through to Google Maps for any online aircraft and an optional health view that distinguishes "emulator is down" from "the simulator behind the emulator is unreachable."

This manual is organized per-feature, just like the simulator manual. If you've already read [User Manual (Simulator)](../manual/welcome.md), the format will be familiar.

<!-- SCREENSHOT-PENDING: dashboard-welcome-01-grid.png - dashboard with 6 cards in a grid, 5 online, 1 offline. -->

## How this manual is organized

| Section | When to read it |
|---------|-----------------|
| **[Overview](overview.md)** | Layout orientation - header, theme toggle, health toggle, the grid of simulator cards. |
| **[Simulator Card](simulator-card.md)** | Per-card reference - every field shown, when it's populated, what each color means. |
| **[Health Chain](health-chain.md)** | The four-node diagnostic chain that appears when you toggle the health view on. |
| **[Configuration](configuration.md)** | Env vars (`SIM_N_NAME`, `SIM_N_PORT`, `SIM_N_GPS_SYSTEM`), compose-file setup, and how to wire emulators to the dashboard. |
| **[Appendix](appendix.md)** | Troubleshooting, glossary, env-var reference for the dashboard side. |

## How the dashboard fits with the simulator

The dashboard is **read-only** with respect to each simulator - it watches UDP traffic that the simulator's [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) is already producing. It does not push anything back. So the operator-facing workflow is:

1. Each simulator container runs in [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) with **UDP Retransmit** enabled, targeting the dashboard's IP and a per-simulator port.
2. The dashboard container is configured (via env vars) with the matching list of `SIM_N_NAME` / `SIM_N_PORT` entries.
3. Each simulator additionally sets `SIMULATOR_IP` so the rebroadcaster can ping the upstream sim host and report `sim_reachable` in the heartbeat.
4. The dashboard renders one card per configured simulator and updates it whenever a packet arrives.

See [Fleet Monitoring](../user-guides/fleet-monitoring.md) for the end-to-end setup walkthrough.

## When you get stuck

| Symptom | Where to look |
|---------|---------------|
| Card stays gray after the emulator is configured | [Configuration](configuration.md) and [Fleet Monitoring](../user-guides/fleet-monitoring.md) |
| Card is green but the position values look wrong | Check the rebroadcaster's UDP retransmit target IP and port match `SIM_N_PORT`. |
| Health view shows red on the GPS chain segment | [Health Chain](health-chain.md) walks through what each failed segment means. |
| `tcpdump` shows packets at the dashboard host but no card updates | Dashboard port mapping. The dashboard uses `network_mode: host`, so the listener binds host ports directly - confirm there's no host firewall and the env vars list the right ports. |

## What's next

- [Overview](overview.md) - the layout at a glance.
- [Simulator Card](simulator-card.md) - field-by-field reference.
- [Health Chain](health-chain.md) - the diagnostic view.
