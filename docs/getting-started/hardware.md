# Hardware Requirements

The simulator is **software-only**: there is no specialty GPS receiver, antenna, or expansion card to buy. Real-world hardware requirements come from three places — the host that runs the container, the optional USB-serial peripheral, and the optional EFB device.

This page covers each in detail, with the minimum and recommended specs and the reasoning behind each one.

## Host machine

A single host runs the simulator container. The Fleet Dashboard runs on the same host or a separate host — both are light enough to coexist if you want them on one box.

### CPU, RAM, and disk

| Resource | Minimum | Recommended | Why |
|----------|---------|-------------|-----|
| **CPU** | 1 core at ~1 GHz | 2 cores at 1.5 GHz or better | NMEA generation runs at 1 Hz and the React UI is idle most of the time. Tested on a Raspberry Pi 4 (1.5 GHz Cortex-A72) with headroom to spare. |
| **RAM** | 256 MB free | 512 MB free | Python + the airport database is the bulk of resident memory. Headroom keeps lookups instant. |
| **Disk** | 500 MB free | 1 GB free | The image is ~250 MB; the rest is base layers, logs, and any volumes you mount. |

These numbers apply to the simulator container in isolation. If you run the Fleet Dashboard on the same host, add roughly the same headroom again.

### Operating system and architecture

| Host | Status | Image arch pulled |
|------|--------|-------------------|
| **Linux x86_64 (Ubuntu / Debian / RHEL / Arch)** | Routinely tested | `linux/amd64` |
| **Intel macOS** | Works | `linux/amd64` |
| **Apple Silicon macOS (M1 / M2 / M3 / M4)** | Routinely tested | `linux/arm64` |
| **Raspberry Pi 4 / 5 (64-bit Raspberry Pi OS)** | Routinely tested | `linux/arm64` |
| **Windows host** | Not directly tested; expected to work under WSL2 with Docker Desktop | `linux/amd64` |

The published image is a multi-arch manifest, so a single `docker pull rjsears/gps-emulator:latest` picks the correct architecture automatically.

### Docker

| Requirement | Notes |
|-------------|-------|
| Docker Engine **20.10+** or **Docker Desktop 4.x+** | The compose file uses Compose v2 syntax. |
| Buildx plugin (if building locally) | Required for multi-arch builds, but **not** required to run a pre-built image from Docker Hub. |
| Compose plugin | `docker compose up -d` is the canonical bring-up. Standalone `docker-compose` (legacy) works too. |

!!! warning "Privileged container"
    The simulator's compose file uses `privileged: true` and bind-mounts `/dev`. This is required for USB-serial access. Run the image you trust — `privileged` lets the container see all host devices.

## Optional USB-serial peripheral

The simulator can drive any USB-serial bridge that enumerates as a device the host kernel can open. The container needs the host's `/dev` tree bind-mounted so it can see the device.

### Verified devices

| Device | Connection on the host | Tested role |
|--------|------------------------|-------------|
| **Bad Elf SBK-2500** | USB-A &rarr; RJ-45 (RS-232) | Drop-in serial GPS replacement for avionics that expect NMEA-0183 in. The originally-targeted device for this project. |
| **Bad Elf Pro / Pro+** | USB-A &rarr; USB-C / Lightning to an iPad | Drives the host side of a Bad Elf-to-iPad pass-through. |
| **Generic FTDI / Prolific / CH340 USB-serial adapters** | USB-A &rarr; RS-232 or TTL | Generic NMEA-out for custom gear or test rigs. |

### Supported device-path patterns

The serial manager probes for any of these patterns at runtime:

| Platform | Patterns probed |
|----------|-----------------|
| Linux | `/dev/ttyUSB*`, `/dev/ttyACM*` |
| macOS | `/dev/tty.usbserial-*`, `/dev/cu.usbserial-*`, `/dev/tty.usbmodem-*`, `/dev/cu.usbmodem-*` |

The first device that matches is offered in the web UI's serial picker by default; multiple matches are all enumerated and selectable.

!!! tip "Confirming the device is reachable inside the container"
    After connecting the peripheral and starting the container, run `docker compose exec gps-emulator ls /dev/tty*`. The expected pattern must show up. If it doesn't, the device is hot-plugged but the container started before it was attached — either restart the container or rebuild the compose file with `restart: unless-stopped` and re-plug.

### Baud rates

| Baud | Common consumer |
|------|-----------------|
| 1200 | Legacy modems |
| 2400 | Low-speed printers, legacy avionics |
| 4800 | Many GPS modules (de facto NMEA default) |
| 9600 | Common default for embedded systems and many EFBs |
| 19200 | Industrial / PLC |
| 38400 | Instrumentation |
| 57600 | Higher-speed embedded |
| **115200** | USB-serial bridges — **recommended default** |

The default is `SERIAL_BAUDRATE=115200`. The web UI's serial selector exposes the full list above so you can match whatever the downstream device expects.

## Optional EFB device

The simulator can drive **ForeFlight** or **Garmin Pilot** running on an iPad over the XGPS protocol on UDP port 49002.

| EFB | Discovery model | What you configure on the simulator |
|-----|-----------------|--------------------------------------|
| **ForeFlight** | UDP broadcast on 49002 | Either broadcast (no IPs needed) or target IPs. |
| **Garmin Pilot** | Unicast on 49002 | Target IPs only — broadcast does not work for Garmin Pilot. |

### Network requirements for EFB

| Requirement | Why |
|-------------|-----|
| iPad and simulator host on the **same Layer-2 segment** (same Wi-Fi SSID, same VLAN) | UDP 49002 is link-local. Routed paths break discovery in practice. |
| **No AP isolation / "guest mode"** on the Wi-Fi | AP isolation drops broadcast and host-to-host traffic; you'll see no XGPS at all. |
| No host-side firewall blocking outbound UDP 49002 | Especially on macOS, where the firewall sometimes silently drops broadcast. |

!!! tip "Use a dedicated lab network for EFB delivery"
    The most reliable setup is a small, dedicated Wi-Fi (a $50 access point on its own SSID) shared only by the simulator host and the iPads it's driving. No NAT, no guest isolation, no captive portal. This eliminates whole classes of intermittent failure.

## Network requirements for multi-station deployments

Sender ↔ Receiver and Rebroadcaster → Fleet Dashboard traffic both ride normal UDP/TCP — no link-local restriction — so they can cross routers, switches, and even VPNs as long as the ports are reachable.

| Path | Default port | Direction | NAT / firewall notes |
|------|--------------|-----------|----------------------|
| Sender → Receiver (NMEA position) | UDP/TCP 12000 | Sender → Receiver | UDP: source-NAT works; UDP is stateless so the receiver doesn't need to send back. TCP: needs bidirectional reachability. |
| Rebroadcaster → Fleet Dashboard | UDP 12001..N (one port per simulator) | Rebroadcaster → Dashboard | UDP only. Each simulator picks a unique port; the dashboard listens on all of them. |
| Heartbeat (Rebroadcaster → Fleet Dashboard) | Same UDP port as above | Rebroadcaster → Dashboard | Same packet stream, distinguished by `"type": "heartbeat"` JSON field. |

!!! warning "TX checksum offload on some hosts"
    On certain Linux hosts with specific NICs, `tcpdump` on the receiving end shows "bad udp cksum" warnings even though the packet payload is intact. This is a transmit-side hardware-offload artifact, not real corruption. See [TX Checksum Offload Fix](../user-guides/tx-checksum-offload.md) for the `ethtool -K` recipe and how to make it persistent.

## What you do **not** need

| Item | Why you don't need it |
|------|----------------------|
| A GPS receiver or antenna | The simulator generates position from first principles. |
| Specialty serial cards (multi-port boards, ISA cards) | A USB-serial bridge is enough. |
| A dedicated server | The container fits comfortably on a Raspberry Pi 4. |
| External time source (PTP, GPSDO) | NMEA time fields are generated from the container's system clock. Container should have NTP, but no PTP needed. |
| A separate database | The simulator is stateless across restarts; the Fleet Dashboard keeps everything in memory. |

## What's next

- Got the hardware lined up? Head to [Quick Start](quick-start.md) for a working container in under five minutes.
- Designing a deployment? Read [Architecture](architecture.md) for the port matrix and data-flow specifics.
- Connecting an EFB? See [Connecting ForeFlight](../user-guides/connecting-foreflight.md) and [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md).
- Wiring USB serial to a Bad Elf? See [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md).
