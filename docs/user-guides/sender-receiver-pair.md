# Sender/Receiver Pair

The Sender / Receiver protocol is the simulator's way to have one position source drive many downstream consumers. This guide walks through a two-station deployment end to end, with both the network-protocol decisions and the per-station configuration.

## The shape of the pair

```
+---------------------+                    +---------------------+
|  Instructor host    |                    |  Student host       |
|  (Sender mode)      |  UDP or TCP :12000 |  (Receiver mode)    |
|                     | -----------------> |                     |
|  Web UI :80         |                    |  Web UI :80         |
|  Drives position    |                    |  Drives Bad Elf,    |
|  via sliders        |                    |  iPad EFB           |
+---------------------+                    +---------------------+
```

The instructor station owns the position. The student station mirrors it locally - synthesizing fresh NMEA, driving its own serial device, optionally feeding its own EFB.

## Pick UDP or TCP first

This decision drives most of the rest of the configuration.

| Consideration | UDP | TCP |
|---------------|-----|-----|
| Same Wi-Fi or wired LAN | Good choice | Also fine, but more state |
| Across an unreliable link | Acceptable (1 missed packet per second is no big deal) | Better (reliable delivery) |
| Multiple receivers from one sender | Yes - point at broadcast or unicast each. | No - TCP is one-to-one. |
| Receiver behind NAT | Sender can punch through if Receiver initiates? No, UDP is fire-and-forget. | Yes (if Receiver-initiated; not the default direction) |
| Connection-state diagnostics | None - "connected" is meaningless for UDP. | The Status Display's network indicator reflects the TCP state. |

For a same-network instructor / student deployment, UDP is the right answer.

## Set up the Sender

### Network details

| Setting | Value |
|---------|-------|
| Mode | **Sender** |
| NMEA Output | on |
| Protocol | `udp` |
| Target IP | The Receiver's IP (e.g., `10.200.40.20`) |
| Port | `12000` |

For broadcast to multiple Receivers on the same subnet, use the subnet's broadcast address (e.g., `10.200.40.255`).

### Optionally also drive a local EFB and a local serial device

```
EFB Output -> on, broadcast on, simulator name "INSTR"
USB Serial Output -> on, /dev/ttyUSB0, 115200
```

A Sender can publish to the network and drive local USB / EFB simultaneously - one engine, many outputs.

### Driving from the UI

1. Pick an airport in the **Position** panel.
2. Set initial altitude, airspeed, heading in **Navigation**.
3. Press **Start**.

The Sender's **Output Viewer** scrolls NMEA locally; the JSON position packet ships to the Receiver in parallel (invisible to the viewer - check `tcpdump` on the Sender's network if you need to verify).

## Set up the Receiver

### Network details

| Setting | Value |
|---------|-------|
| Mode | **Receiver** |
| Protocol | `udp` |
| Port | `12000` (matching Sender) |

The Receiver doesn't need a target IP - it binds `0.0.0.0:12000` and accepts whatever arrives.

### Output

| Setting | Value |
|---------|-------|
| Serial Device | `/dev/ttyUSB0` (the student's Bad Elf) |
| Baud Rate | matching the student's avionics (often 9600 for legacy panels) |

A plain Receiver has exactly one output - USB serial. If you also want to drive an iPad EFB from the student station, switch the mode to **Rebroadcaster** (it's a Receiver + extra outputs). See [Rebroadcaster Mode](../manual/mode-rebroadcaster.md).

### Driving from the UI

1. Pick the serial device.
2. Press **Start**.

The Receiver binds the port and waits. As soon as the Sender starts, position packets arrive at 1 Hz and the student's Output Viewer scrolls.

## Verifying the link

| Check | Why it matters |
|-------|----------------|
| **Sender's Output Viewer** scrolling | Sender's NMEA engine is running. |
| **Sender's Status Display** Network row green (TCP) or present (UDP) | Sender's network publish is alive. |
| `tcpdump -i any 'udp port 12000'` on the Receiver host | Confirms packets are arriving at the host. |
| **Receiver's Output Viewer** scrolling | Receiver is parsing and synthesizing NMEA. |
| **Receiver's Status Display** Network row green | Receiver's listen socket is bound. |

If `tcpdump` shows packets but the Receiver's Output Viewer is empty, the Receiver process isn't binding the port. Common cause: a previous container instance lingering on the port.

## Worked scenarios

### Scenario 1 - Two stations, UDP unicast

Instructor `10.200.40.10`, student `10.200.40.20`.

| Sender | Receiver |
|--------|----------|
| Mode: Sender; NMEA on; UDP; `10.200.40.20:12000` | Mode: Receiver; UDP; port 12000; `/dev/ttyUSB0`; 9600 baud |

Instructor drives, student mirrors. Add a Bad Elf to the student and a panel; verify NMEA on the panel.

### Scenario 2 - One instructor, three students, UDP broadcast

All four hosts on `10.200.40.0/24`. Broadcast address `10.200.40.255`.

| Sender | Receivers (x3) |
|--------|---------------|
| Mode: Sender; NMEA on; UDP; `10.200.40.255:12000` | Mode: Receiver; UDP; port 12000; each with its own serial device |

Three receivers, one sender, no per-receiver setup on the sender side.

### Scenario 3 - Same as 2, but reliable (TCP)

TCP can't broadcast. Choose one student to be the primary or run three separate Sender instances (one per Receiver). The first option:

| Sender | Receiver |
|--------|----------|
| Mode: Sender; NMEA on; TCP; primary student's IP:12000 | Mode: Receiver; TCP; port 12000 |

The other two students don't receive in this configuration. For more, use UDP + broadcast or run separate Senders.

### Scenario 4 - Cross-site over Tailscale or WireGuard

Instructor in office, student at home. VPN already in place.

| Sender | Receiver |
|--------|----------|
| Mode: Sender; NMEA on; **TCP**; the student's VPN IP; 12000 | Mode: Receiver; TCP; port 12000 |

TCP because the link is variable and you'd rather have reliable delivery than fire-and-forget. UDP also works if you don't mind dropped packets.

## Common gotchas

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Sender starts, no traffic on the wire | UDP target IP is wrong, or the host's outbound route is broken. | `ping` the target from the Sender's host. |
| TCP Sender start fails with "Connection refused" | Receiver isn't running yet, or listening on a different port. | Start the Receiver first. |
| Packets visible in `tcpdump` but Receiver's Output Viewer empty | Receiver bound the wrong protocol (UDP vs TCP mismatch). | Match. Both sides need the same protocol. |
| Receiver shows weird CYGNUS-format-looking warnings | An upstream source is sending CYGNUS instead of the project's JSON. **This is OK** - the receiver auto-detects. The warning, if any, is informational. | Ignore unless you don't trust the source. |
| Both UI ports collide (both stations have `80:80` mapped) | When testing on the same host, you can't run two containers on the same port. | Remap one to `8080:80`. |
| "Bad UDP checksum" warnings in `tcpdump` on the Receiver host | TX checksum offload on the Sender NIC. | See [TX Checksum Offload Fix](tx-checksum-offload.md). |

## Going further

If you need both ends to drive their own iPad EFB and their own USB device, plus report to a Fleet Dashboard, switch the receiver side to **Rebroadcaster** - same listen-port semantics, more outputs. See [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) and [Fleet Monitoring](fleet-monitoring.md).

## What's next

- [Sender Mode](../manual/mode-sender.md) - Sender-side reference.
- [Receiver Mode](../manual/mode-receiver.md) - Receiver-side reference.
- [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) - Receiver + fan-out.
- [Network Protocol](../reference/network-protocol.md) - JSON / CYGNUS wire formats.
