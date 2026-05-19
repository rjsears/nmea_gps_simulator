# Overview

The NMEA GPS Simulator is a **software-only**, **container-packaged** source of NMEA-0183 GPS data. It produces the same wire formats that real GPS hardware emits, drives external devices over USB serial and UDP, and presents a web UI for live control.

This page is the conceptual entry point: what the system is, who it is for, and how the pieces fit together at the level you need before reading anything else.

## What the system is

The repository ships two related applications:

| Application | Container image | Role |
|-------------|-----------------|------|
| **NMEA GPS Simulator** | `rjsears/gps-emulator:latest` | The product. Generates / receives / rebroadcasts NMEA position data; serves the operator web UI on port 80. |
| **Fleet Dashboard** (optional) | `rjsears/fleet-dashboard:latest` | Aggregates UDP telemetry + heartbeats from many simulators into one live view, with end-to-end health diagnostics. |

Both are deployed via Docker Compose. Both expose their own REST + WebSocket API and their own OpenAPI documentation (see [API Reference](../reference/api-reference.md)).

The simulator runs on **`linux/amd64`** and **`linux/arm64`** — the same multi-arch image installs cleanly on a server, a desktop, an Apple Silicon laptop, or a Raspberry Pi 4/5.

## What problem it solves

Realistic GPS data is essential for training, development, and integration testing — but real GPS hardware is inconvenient:

- It needs antenna placement that's rarely practical indoors.
- It can't produce the long, smooth tracks needed for training scenarios.
- Specific hardware is sometimes discontinued (the original Bad Elf Pro line, the Cygnus boxes).
- You usually only have one of them, when you need data flowing to several devices at once.

The simulator replaces the hardware piece entirely. You get smooth, deterministic, controllable position data over the same wire formats real hardware uses, and you can fan it out to as many downstream receivers as you want.

## Who it is for

| Audience | What they typically do with it |
|----------|------------------------------|
| **Flight training facilities** | Drive iPads running ForeFlight or Garmin Pilot from the instructor station; show realistic position to the EFB during cross-country lessons. |
| **Simulator integrators** | Replace discontinued GPS hardware in existing simulator stacks; feed legacy avionics that expect serial NMEA-0183 in. |
| **Software developers** | Generate test inputs for any GPS-consuming application: navigation libraries, mapping tools, fleet trackers, log parsers. |
| **Amateur radio operators** | Inject position data into TNCs and APRS mapping software for testing and demonstrations. |
| **Educators** | Run classroom exercises that involve "tracking" simulated aircraft across actual airspace charts. |

## The four operating modes

The simulator operates in one of four modes at a time. Three are mutually exclusive; the fourth is a sub-option of one of them. Each is covered in detail on its own manual page.

| Mode | What it does | When to use it | Manual page |
|------|--------------|----------------|-------------|
| **Stand-Alone** | Generates NMEA locally from manual input. Sends to USB serial and/or EFB. No network ingest. | Single-station training, classroom demos, single-iPad EFB testing. | [Stand-Alone Mode](../manual/mode-standalone.md) |
| **Sender** | Generates NMEA locally **and** publishes position to one or more network receivers. Can also send to USB / EFB. | Multi-station deployments where one instance is the "source of truth" and others mirror it. | [Sender Mode](../manual/mode-sender.md) |
| **Receiver** | Listens for position packets from a Sender (or any compatible producer) and emits NMEA locally to USB serial. | Mirror station, hardware-replacement station, classroom client. | [Receiver Mode](../manual/mode-receiver.md) |
| **Rebroadcaster** | A Receiver that additionally re-emits the received position to EFB targets, the Fleet Dashboard, and/or a downstream UDP target. | Central fan-out point for a multi-target deployment; the canonical setup for feeding a fleet of EFB iPads from one position source. | [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) |

## The wire formats it speaks

| Format | Direction | Purpose |
|--------|-----------|---------|
| **NMEA-0183** (GPGGA, GPRMC, optionally GPGLL, GPGSA, GPGSV, GPHDT, GPVTG, GPZDA) | Out, over USB serial | Drive avionics, Bad Elf devices, any NMEA-listening application. |
| **JSON position packet** (1 Hz, ~100-150 bytes) | In or out, over UDP/TCP | Sender↔Receiver protocol. Open: any code that can send JSON over a socket can act as a sender. |
| **CYGNUS** (key=value string) | In, over UDP/TCP | Compatibility with simulators that produce CYGNUS-format streams. Auto-detected by the receiver. |
| **XGPS** (single line per second) | Out, over UDP 49002 | ForeFlight and Garmin Pilot EFB integration. Broadcast for ForeFlight, unicast for Garmin Pilot. |
| **Heartbeat packet** (1 Hz) | Out, over UDP | Sent by rebroadcasters to the Fleet Dashboard. Carries `sim_reachable`, `receiving_udp`, and uptime. |

The [Network Protocol](../reference/network-protocol.md) reference documents each format's schema; [NMEA Protocol](../reference/nmea-protocol.md) covers the wire-level NMEA-0183 framing.

## How a typical deployment looks

The smallest useful deployment is one container plus one EFB:

1. Run the simulator container on a host on the same Wi-Fi as the iPad.
2. Pick Stand-Alone mode.
3. Configure EFB output to the iPad's IP (Garmin Pilot) or broadcast (ForeFlight).
4. Start. The EFB picks up `XGPS` data immediately on UDP 49002.

A multi-station training deployment scales up:

1. One **Sender** on the instructor station; the instructor adjusts position there.
2. One or more **Rebroadcasters** at each student station, each driving its own Bad Elf SBK-2500 over USB and a paired iPad over EFB.
3. A **Fleet Dashboard** container on a third host watching every rebroadcaster's UDP retransmit + heartbeat, so the instructor can see at a glance which stations are healthy.

The [Architecture](architecture.md) page covers the component layout, port matrix, and data flow in depth; [Hardware Requirements](hardware.md) covers what physical equipment supports each role.

## What's next

- If you're brand new, jump to the [Quick Start](quick-start.md) and get a single container running first.
- If you're planning a multi-station deployment, read [Architecture](architecture.md) and [Hardware Requirements](hardware.md) before you wire anything together.
- If you're a developer who'd rather read the API surface than the UI, head to the [API Reference](../reference/api-reference.md).
