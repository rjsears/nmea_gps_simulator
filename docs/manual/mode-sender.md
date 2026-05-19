# Sender Mode

Sender mode does everything [Stand-Alone Mode](mode-standalone.md) does **plus** publishes the position over UDP or TCP to a downstream receiver. The receiver (or multiple receivers, for UDP) regenerates NMEA locally and drives its own outputs.

The canonical use case: one instructor station running Sender, one or more student stations running [Receiver Mode](mode-receiver.md) or [Rebroadcaster Mode](mode-rebroadcaster.md). The instructor drives the position; the students mirror it.

!!! info "What goes on the wire"
    The Sender protocol is **position only**, not full NMEA. The packet is a ~100-150-byte JSON object at 1 Hz. The receiver decides which NMEA sentences to synthesize. Bandwidth is minimal and the wire format is open - any tool that can `socket.send` JSON can act as a sender. See [Network Protocol](../reference/network-protocol.md) for the schema.

<!-- SCREENSHOT-PENDING: mode-sender-01-overview.png - Sender Settings panel with NMEA + EFB + USB blocks visible. -->

## When to use Sender

| Use case | Why Sender fits |
|----------|------------------|
| One instructor station drives many student stations | Each student runs Receiver / Rebroadcaster against the Sender's IP. |
| Standalone-style operation **and** a remote receiver | Sender does both - it can run a Bad Elf locally and ship to a network receiver simultaneously. |
| Sending position to a custom downstream consumer | Any JSON-over-UDP listener is a valid receiver. See the [Network Protocol](../reference/network-protocol.md) integration examples. |
| Replaying a recorded flight path to a fleet | Pair a Sender with a script driving the slider values; receivers see the result. |

If you want the simulator to *consume* position from somewhere else, you want [Receiver Mode](mode-receiver.md) or [Rebroadcaster Mode](mode-rebroadcaster.md) instead.

## Reaching Sender mode

| Step | Action |
|------|--------|
| 1 | Log in if `BYPASS_AUTH=false`. |
| 2 | In the mode selector at the top of the dashboard, choose **Sender**. |
| 3 | The **Sender Settings** panel appears with three independent output blocks - NMEA Output (the network publish), EFB Output, and USB Serial Output. |

You cannot switch into or out of Sender while the emulator is running. Press **Stop** first.

## Sender Settings panel

At least one output must be enabled before **Start** activates. Most setups enable two or more.

### NMEA Output (the network publish)

This is the block that makes Sender mode distinct from Stand-Alone.

| Control | Default | Valid values | What it does |
|---------|---------|--------------|--------------|
| **NMEA Output** toggle | off | on / off | Enables the network publish block. With this off, Sender behaves like Stand-Alone. |
| **Protocol** | `udp` | `udp`, `tcp` | Transport for the position packet. UDP is fire-and-forget at 1 Hz; TCP keeps a persistent connection open. |
| **Target IP** | (empty) | A single IPv4 address | Where the position packet goes. Typically the Receiver / Rebroadcaster's IP. |
| **Port** | `12000` | 1024-65535 | UDP/TCP port on the target. Must match the Receiver's listen port. |

!!! warning "UDP can fan out to broadcast; TCP cannot"
    If you point a UDP Sender at a broadcast address (`192.168.1.255`, `255.255.255.255`), every UDP receiver on the segment that's listening on the port will pick it up. Useful for one-to-many. TCP requires a specific peer and cannot broadcast.

#### When to pick UDP vs TCP

| Situation | Use UDP | Use TCP |
|-----------|---------|---------|
| Same Wi-Fi or wired LAN | **Yes** | Optional |
| Across the public internet over an unreliable link | Optional (1 Hz means one missed packet doesn't matter much) | **Yes** |
| Fan out to many receivers at once | **Yes** (point at broadcast or unicast each) | No (one peer per Sender) |
| Receiver behind NAT with no port-forward | Tricky | **Yes** (if Sender initiates from outside, TCP works with proper forwarding) |

### EFB Output (UDP 49002)

Identical to the EFB block in [Stand-Alone Mode](mode-standalone.md). Controls:

| Control | Default | What it does |
|---------|---------|--------------|
| **EFB Output (Port 49002)** master toggle | off | Enables the EFB block. |
| **Broadcast** | off | UDP broadcast to 49002. ForeFlight discovers via this. |
| **Garmin Pilot / ForeFlight (IP Address)** | off | Unicast to one or more iPad IPs. Required for Garmin Pilot. |
| **EFB target IPs** | (empty) | Comma-separated list / ranges. See [IP Range Parsing](../user-guides/ip-range-parsing.md). |
| **Simulator Name** | (empty) | Required when EFB enabled. Shown in the EFB's GPS-source list. |

See the [EFB section of Stand-Alone Mode](mode-standalone.md#efb-output-udp-49002-foreflight-and-garmin-pilot) for the broadcast-vs-IP-targeting decision matrix and [Connecting ForeFlight](../user-guides/connecting-foreflight.md) / [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md) for the iPad-side setup.

### USB Serial Output

Identical to the USB block in [Stand-Alone Mode](mode-standalone.md). The same NMEA engine that ships JSON to the network and XGPS to the EFB also runs serial bytes out the configured `/dev/ttyUSB*`.

| Control | Default | What it does |
|---------|---------|--------------|
| **USB Serial Output** toggle | off | Enables NMEA-0183 emission to a USB-serial device. |
| **Device** | (none) | One of `/dev/ttyUSB*`, `/dev/ttyACM*`, `/dev/tty.usbserial-*`, `/dev/tty.usbmodem-*`. The **Refresh** button rescans. |
| **Baud Rate** | `115200` | 1200 - 115200. |

See [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md) for end-to-end USB hardware guidance.

## Navigation, NMEA sentence selection, and starting

Position, altitude, speed, and heading inputs work identically to Stand-Alone - same panel, same compass dial, same airport picker. See [Navigation Controls](navigation-controls.md).

NMEA sentence selection works identically - `GPGGA` + `GPRMC` always on, others opt-in. See [NMEA Sentences](nmea-sentences.md).

Starting and stopping behavior is the same too - all enabled outputs open on **Start**, close on **Stop**, in-memory configuration survives Stop but not container restart.

## TCP connection semantics

When **Protocol = tcp**, the Sender opens a single persistent TCP connection at **Start** and reuses it for the lifetime of the run.

| Event | Behavior |
|-------|----------|
| **Start** with TCP, target reachable | Connection established, position packets begin streaming. |
| **Start** with TCP, target unreachable | Start fails; check the Status Display for the error. |
| TCP peer disappears mid-run | The next `send` fails. The Sender logs an error and *does not auto-reconnect*. **Stop** and **Start** to re-establish. |
| **Stop** | The TCP connection closes cleanly. |

UDP has no connection state, so none of the above applies - packets go on the wire whether anyone is listening or not.

## Persistent state

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| Mode (set to sender at boot) | Mode selector | `AUTO_START_MODE=sender` | Only if env var set |
| Default position / nav values | Sliders / picker | `DEFAULT_LAT`, `DEFAULT_LON`, `DEFAULT_ALT_FT`, `DEFAULT_AIRSPEED_KTS`, `DEFAULT_HEADING` | Yes (env var, used at boot) |
| Transition rates | (no UI) | `ALTITUDE_RATE_FT_PER_2SEC`, `AIRSPEED_RATE_KTS_PER_SEC`, `HEADING_RATE_DEG_PER_SEC` | Yes (env var) |
| NMEA output enabled | Sender Settings | (no boot var) | No - set via UI per run |
| Target IP / Port / Protocol | Sender Settings | (no boot var) | No - set via UI per run |
| EFB enabled, broadcast, IPs, sim name, USB | Sender Settings | `AUTO_START_EFB_*`, `AUTO_START_USB_*` | Only if env vars set |
| Serial baud | Serial picker | `SERIAL_BAUDRATE` | Yes (env var, host-wide default) |

!!! info "Why no boot-var path for the NMEA output target"
    Auto-start at the env-var level supports Stand-Alone, Receiver, and Rebroadcaster directly. **Sender's** NMEA output target is set via the UI per run, since most sender deployments are operator-driven (an instructor at the keyboard). If you do need to boot a Sender straight into a network publish, drive it via the REST API on startup - see [API Reference](../reference/api-reference.md).

## Worked scenarios

### Scenario 1 - Instructor station driving one student station

Instructor host at `10.200.40.10`, student host at `10.200.40.20`. UDP, port 12000. The student station runs [Receiver Mode](mode-receiver.md).

Sender configuration:

| Setting | Value |
|---------|-------|
| Mode | Sender |
| NMEA output | on |
| Protocol | udp |
| Target IP | `10.200.40.20` |
| Port | 12000 |
| EFB | off (the instructor doesn't need an iPad on this station) |
| USB | off |

The instructor adjusts position, altitude, speed, heading via the web UI. The student station, listening on UDP 12000, regenerates NMEA locally and drives its own Bad Elf + EFB.

### Scenario 2 - One Sender, three Receivers via broadcast

Instructor on `10.200.40.10`; three student hosts on the same `10.200.40.0/24` subnet. Broadcast address `10.200.40.255`.

| Setting | Value |
|---------|-------|
| Protocol | udp |
| Target IP | `10.200.40.255` |
| Port | 12000 |

All three student stations running Receiver / Rebroadcaster on UDP 12000 pick up the same packets. One sender, three downstream consumers.

### Scenario 3 - Sender that also drives a local EFB and Bad Elf

Same instructor host, but the instructor wants to corroborate position on their own iPad and serial test harness while still driving the student station.

| Setting | Value |
|---------|-------|
| NMEA output | on, UDP, `10.200.40.20:12000` |
| EFB output | on, broadcast on, simulator name `INSTR` |
| USB output | on, `/dev/ttyUSB0`, 115200 |

One NMEA engine, three outputs in parallel.

## What's next

- [Receiver Mode](mode-receiver.md) - what goes on the other end of the network protocol.
- [Rebroadcaster Mode](mode-rebroadcaster.md) - a receiver that additionally fans out to more downstream consumers.
- [Sender/Receiver Pair](../user-guides/sender-receiver-pair.md) - end-to-end two-station setup with screenshots.
- [Network Protocol](../reference/network-protocol.md) - the JSON wire format Sender publishes.
- [IP Range Parsing](../user-guides/ip-range-parsing.md) - syntax for EFB target IPs.
