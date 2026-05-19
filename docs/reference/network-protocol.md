# Network Protocol

The simulator uses three distinct network protocols. This page is the wire-level reference for each.

| Protocol | Direction | Port | What it carries |
|----------|-----------|------|-----------------|
| **JSON position** | Sender -> Receiver | UDP/TCP 12000 | The simulator's own position-publish format. Open: any client that can build the JSON can act as a sender. |
| **CYGNUS position** | Sender -> Receiver | UDP/TCP 12000 | Compatibility format used by some flight simulators. The Receiver auto-detects vs JSON. |
| **XGPS** | Simulator -> EFB | UDP 49002 | The ForeFlight / Garmin Pilot EFB integration format. |
| **Heartbeat** | Rebroadcaster -> Fleet Dashboard | UDP per-sim port | 1 Hz health packet. Same port as UDP retransmit; distinguished by `"type": "heartbeat"`. |

## 1. JSON position protocol

The simulator's native protocol. Sent by Sender mode and the Rebroadcaster's UDP retransmit.

### Wire format

Single JSON object per packet. UTF-8. Sent at 1 Hz.

```json
{
  "lat": 33.1283,
  "lon": -117.2803,
  "alt_ft": 45000,
  "speed_kts": 420,
  "heading": 270,
  "timestamp": "2026-05-18T15:30:45.123456+00:00"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `lat` | float | yes | Decimal degrees, N positive. |
| `lon` | float | yes | Decimal degrees, E positive. |
| `alt_ft` | float \| int | yes | Altitude in feet MSL. |
| `speed_kts` | float \| int | yes | Ground speed in knots. |
| `heading` | float \| int | yes | True heading in degrees. The simulator normalizes 0 to 360. |
| `timestamp` | string | no | ISO 8601 timestamp. Receiver uses its own clock if missing. |

Typical packet size: 100-150 bytes UTF-8 encoded.

### Transport

| Detail | UDP | TCP |
|--------|-----|-----|
| Connection state | None | One connection per Sender; reused for the run. |
| Packet boundary | Implicit (one packet per UDP datagram) | Newline-terminated. Sender sends `<json>\n`. |
| Retry on failure | None | None - Sender does not auto-reconnect. |
| Multiple receivers from one sender | Yes (broadcast or unicast each) | No (one peer). |

### Producing the packet from a script

```python
import socket, json
from datetime import datetime, timezone

packet = {
    "lat": 33.1283,
    "lon": -117.2803,
    "alt_ft": 45000,
    "speed_kts": 420,
    "heading": 270,
    "timestamp": datetime.now(timezone.utc).isoformat(),
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(packet).encode(), ("10.200.40.20", 12000))
```

Any code that can build that JSON over UDP is a valid sender. This is the "open protocol" property.

## 2. CYGNUS position protocol

A `key=value` ampersand-separated string. Auto-detected by the Receiver via the leading `$` character.

```
$CYGNUS:lat=39.828314&lon=-104.660550&heading=0.5&magvar=-6.0&alt=5431.6&airspeed=125.3
```

| Field | Type | Description |
|-------|------|-------------|
| `lat` | float | Decimal degrees. |
| `lon` | float | Decimal degrees. |
| `heading` | float | Track over ground in degrees true. |
| `magvar` | float | Magnetic variation. **Not used by the simulator** - included for compatibility but ignored. |
| `alt` | float | Altitude in feet MSL. |
| `airspeed` | float | True airspeed in knots. |

The Receiver maps these to its internal state same as the JSON path. Auto-detection logic: if the first byte of the UDP / TCP payload is `{`, parse as JSON; if `$`, parse as CYGNUS; anything else is a warning log.

## 3. XGPS - the EFB protocol

A single ASCII line per second on UDP 49002. Used by ForeFlight (broadcast or unicast) and Garmin Pilot (unicast only).

### Wire format

```
XGPS{SimName},{lon},{lat},{alt_m},{track},{speed_ms}
```

Concrete example:

```
XGPSCL350,-117.280300,33.128300,1524.0,270.50,61.7
```

| Field | Type | Description |
|-------|------|-------------|
| `SimName` | string | The simulator name. Appears in the EFB's GPS source list. No spaces in the canonical form. |
| `lon` | float (6 decimals) | Decimal degrees, E positive. |
| `lat` | float (6 decimals) | Decimal degrees, N positive. |
| `alt_m` | float (1 decimal) | Altitude in meters MSL. |
| `track` | float (2 decimals) | Track over ground in degrees true. |
| `speed_ms` | float (1 decimal) | Ground speed in meters per second. |

The unit conversions (ft -> m, kts -> m/s) happen inside the simulator's EFB sender; the rest of the system uses ft and knots.

### Cadence

1 Hz, regardless of the upstream source's rate. The simulator's NMEA engine drives the XGPS sender on the same 1-second tick as everything else.

### Delivery

| EFB | Delivery |
|-----|----------|
| **ForeFlight** | Accepts broadcast on UDP 49002 (auto-discovery), or unicast to the iPad's IP. |
| **Garmin Pilot** | Unicast only on UDP 49002. Does NOT accept broadcast. |

For the deployment-level decision matrix, see [Connecting ForeFlight](../user-guides/connecting-foreflight.md) and [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md).

## 4. Heartbeat protocol (Rebroadcaster -> Fleet Dashboard)

A 1 Hz JSON packet that the Rebroadcaster sends to the same UDP port as its position retransmit. The Fleet Dashboard distinguishes the two by the `type` field.

### Wire format

```json
{
  "type": "heartbeat",
  "sim_ip": "10.200.50.12",
  "sim_reachable": true,
  "receiving_udp": true,
  "uptime_seconds": 3712
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"heartbeat"`. Position packets omit this field. |
| `sim_ip` | string | The configured `SIMULATOR_IP`, or empty if unset. |
| `sim_reachable` | bool | Result of the rebroadcaster's most recent `ping -c 1 -W 1 <sim_ip>`. False if no `sim_ip` is set. |
| `receiving_udp` | bool | True if a position packet has been received in the last 5 s. |
| `uptime_seconds` | int | Seconds since the rebroadcaster started (this run; reset on restart). |

The dashboard uses these fields to drive the [Health Chain](../dashboard-manual/health-chain.md) view.

### Cadence

Strictly once per second. The heartbeat thread (`backend/rebroadcaster_runner.py:_send_heartbeat`) runs an internal `time.sleep(1.0)` loop and is independent of incoming position packets - so the dashboard sees a heartbeat even when the upstream sender is silent.

### Position packets sharing the same UDP port

In addition to the heartbeat, the rebroadcaster also retransmits the **original incoming position packet** to the same UDP port. These packets are the JSON or CYGNUS format originally received - the rebroadcaster does **not** re-encode or canonicalize.

The dashboard distinguishes them at parse time:

```python
data = json.loads(udp_payload)
if data.get("type") == "heartbeat":
    handle_heartbeat(data)
else:
    handle_position(data)
```

## Port summary

| Port | Direction | Protocol | Purpose |
|------|-----------|----------|---------|
| TCP 80 | Inbound | HTTP | Simulator web UI |
| TCP 80 | Inbound | HTTP | Fleet Dashboard web UI |
| UDP 12000 | Inbound (Receiver / Rebroadcaster) and Outbound (Sender) | JSON or CYGNUS position | The simulator's own publish-subscribe protocol |
| TCP 12000 | Inbound (Receiver / Rebroadcaster) and Outbound (Sender) | Same | Reliable variant |
| UDP 49002 | Outbound | XGPS | EFB integration |
| UDP 12001..12020 | Inbound on dashboard | JSON position + JSON heartbeat | One port per simulator |

## Why split position-publish and NMEA generation?

The protocol has a property worth calling out: **the network only carries position**, not full NMEA. NMEA sentence selection is a receiver decision.

This means:

- Bandwidth on the wire is ~100-150 bytes/sec, not the ~600+ bytes/sec full NMEA would cost.
- Each receiver decides which NMEA sentences to enable. One receiver can drive a panel with just `GPGGA` + `GPRMC`; another can drive a satellite-view widget with `GPGSV`. Same source.
- Any tool that can build the JSON / CYGNUS schema can be a sender. The simulator is not the only valid source.

The trade-off: receivers must include NMEA generation logic. The simulator handles this; if you write a custom receiver, you'll need to too (or just take the position and skip NMEA entirely).

## What's next

- [NMEA Protocol](nmea-protocol.md) - the serial-line protocol the receiver synthesizes on the other side.
- [Connecting ForeFlight](../user-guides/connecting-foreflight.md) and [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md) - XGPS in deployment.
- [Sender/Receiver Pair](../user-guides/sender-receiver-pair.md) - JSON / CYGNUS in deployment.
- [Fleet Monitoring](../user-guides/fleet-monitoring.md) - heartbeats in deployment.
