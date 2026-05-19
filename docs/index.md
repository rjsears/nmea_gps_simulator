# NMEA GPS Simulator

A Dockerized NMEA-0183 GPS simulator with a modern web interface. Generate, receive, and rebroadcast realistic GPS position data over USB serial, UDP/TCP, and the XGPS protocol used by ForeFlight and Garmin Pilot. The repository also includes a companion **Fleet Dashboard** container that aggregates many simulators into a single live view.

This site is the complete operator and contributor documentation. The [project README](https://github.com/rjsears/nmea_gps_simulator/blob/main/README.md) is the storefront on GitHub; this site is where you live once you start running, configuring, or extending the system.

## Where to start

| You are... | Start here |
|------------|-----------|
| New to the project and trying to decide if it fits your use case | [Overview](getting-started/overview.md) |
| Ready to get a container running on a host you already have | [Quick Start](getting-started/quick-start.md) |
| Planning a deployment with EFBs, Bad Elf hardware, or multiple simulators | [Architecture](getting-started/architecture.md), then [Hardware Requirements](getting-started/hardware.md) |
| Operating the simulator day-to-day | [User Manual (Simulator)](manual/welcome.md) |
| Operating the Fleet Dashboard | [User Manual (Fleet Dashboard)](dashboard-manual/welcome.md) |
| Wiring the simulator into ForeFlight, Garmin Pilot, or a Bad Elf | [Connecting ForeFlight](user-guides/connecting-foreflight.md), [Connecting Garmin Pilot](user-guides/connecting-garmin-pilot.md), [USB Serial (Bad Elf)](user-guides/usb-serial-bad-elf.md) |
| Building against the HTTP / WebSocket API | [API Reference](reference/api-reference.md) |
| Configuring auto-start, env vars, or a multi-host fleet | [Auto-Start](user-guides/auto-start.md), [Environment Variables](reference/env-vars.md), [Fleet Monitoring](user-guides/fleet-monitoring.md) |
| Diagnosing a broken deployment | [Troubleshooting](reference/troubleshooting.md), [TX Checksum Offload Fix](user-guides/tx-checksum-offload.md) |

## What the site covers

| Section | What it documents |
|---------|-------------------|
| [Getting Started](getting-started/overview.md) | What the project is, how the pieces fit together, host and peripheral hardware, and the fastest path to a working container. |
| [User Manual (Simulator)](manual/welcome.md) | One page per UI tab of the simulator web interface. Walks through every control, what it does, when to change it, and when not to. |
| [User Manual (Fleet Dashboard)](dashboard-manual/welcome.md) | The companion fleet-monitoring UI, screen by screen. Includes the health chain and the per-simulator card layout. |
| [User Guides](user-guides/auto-start.md) | Topic-focused HOWTOs that span multiple UI tabs: auto-start, EFB integration, USB serial, sender/receiver pairs, IP range parsing, the TX checksum offload gotcha, and more. |
| [Reference](reference/api-reference.md) | Authoritative reference for the API, environment variables, NMEA wire format, network protocol, security model, and a troubleshooting matrix. |

## Live API documentation

The simulator and the Fleet Dashboard each expose their own OpenAPI specification on their own host:

- **Swagger UI** at `http://<host>/api/docs` (interactive "try it out" explorer)
- **ReDoc** at `http://<host>/api/redoc` (read-only structured reference)
- **Raw OpenAPI JSON** at `http://<host>/api/openapi.json` (machine-readable spec)

See the [API Reference](reference/api-reference.md) page for endpoint summaries and authentication notes.

## Conventions used across the site

| Convention | Meaning |
|------------|---------|
| `!!! tip`, `!!! warning`, `!!! danger`, `!!! info` admonitions | Used consistently across pages. `tip` is recommended-do, `warning` is unexpected behavior, `danger` is destructive, `info` is background context. |
| Code blocks with explicit language tags | All commands and configuration snippets specify the language for syntax highlighting and copy-to-clipboard support. |
| `<host>` and `<dashboard-host>` in URLs | Placeholder hostnames. Substitute the real address of the container running the relevant service. |
| References to env vars (`AUTO_START_MODE`, etc.) | The authoritative table is at [Environment Variables](reference/env-vars.md); other pages link there rather than re-listing the matrix. |

## Repository and license

The source repository is on GitHub at [rjsears/nmea_gps_simulator](https://github.com/rjsears/nmea_gps_simulator) and is published under the [MIT License](https://github.com/rjsears/nmea_gps_simulator/blob/main/LICENSE). Issues and feature requests live on the [GitHub issue tracker](https://github.com/rjsears/nmea_gps_simulator/issues).
