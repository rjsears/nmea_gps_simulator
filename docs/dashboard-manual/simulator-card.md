# Simulator Card

A simulator card is the per-simulator rectangle in the dashboard grid. Each card shows one simulator's live position and metadata. There are three visual states: **online**, **offline**, and **health view** (which is its own thing - see [Health Chain](health-chain.md)).

This page documents the position view (online + offline). The health view shares the card frame but replaces the body with the chain diagram.

<!-- SCREENSHOT-PENDING: simulator-card-01-online.png - single online card with all fields populated. -->
<!-- SCREENSHOT-PENDING: simulator-card-02-offline.png - single offline card with --- placeholders. -->

## Card header

| Element | Online | Offline |
|---------|--------|---------|
| Background | Green gradient | Gray gradient |
| Title text | The simulator's `SIM_N_NAME` (e.g., `CJ3`, `CL350`, `Ultra`). White text. | Same name, same white text. |
| Status pill (right side) | White pill with green text: **ONLINE** | Gray pill with gray text: **OFFLINE** |

The card name is whatever you set as `SIM_N_NAME` in the dashboard's compose file. Names with spaces work fine (`Classic CJ1`, `King Air`, etc.).

## Card body - online state

The body has four sections, top to bottom.

### 1. Position (Lat / Lon)

| Field | Format |
|-------|--------|
| Latitude | Four decimal places + hemisphere letter, e.g., `33.1283° N` or `33.1283° S` |
| Longitude | Same, with `E` / `W` letter |

If a real lat/lon hasn't been received yet (the rebroadcaster has connected but no position packet has come through), this still shows the last known value or zeros - the dashboard does not distinguish "we have stale data" from "we just connected."

### 2. Flight data (Altitude / Airspeed / Heading)

A row of three colored cells:

| Field | Color | Format |
|-------|-------|--------|
| Altitude | Blue cell | Whole feet with thousands separators, e.g., `35,000`. Unit "ft MSL" below the number. |
| Airspeed | Purple cell | Integer knots, e.g., `420`. Unit "kts" below. |
| Heading | Orange cell | Integer degrees + cardinal letter, e.g., `270° W` or `45° NE`. |

The cardinal letter is the eight-direction compass abbreviation (N/NE/E/SE/S/SW/W/NW) computed from the heading - bucketed to the nearest 45°.

### 3. Nearest airport

| Field | Source |
|-------|--------|
| ICAO | The closest airport from the dashboard's own copy of the airport database (4,003 entries - same data as the simulator side). |
| Name | The airport's full name. |
| Distance | Nautical miles, one decimal place (e.g., `12.3 NM`). |

The dashboard computes the nearest airport on every position update. The math is great-circle distance against the in-memory dictionary - O(N) but the constant factor is tiny, so it's instant in practice.

If the dashboard has just started and a position arrived but the airport calculation hasn't completed yet, this section shows `---`. In practice you'll never see that - calculation is sub-millisecond.

### 4. Footer

| Field | What it shows |
|-------|---------------|
| Left: Port | The UDP port the dashboard is listening on for this card (matches `SIM_N_PORT`). Useful for confirming the env-var-to-card mapping. |
| Right: Packets | Total position packets received since the dashboard container started (not since the rebroadcaster started). Thousands separators. |

The packet count grows by 1 every second the rebroadcaster is streaming. A card that's online but where the count isn't growing means heartbeats are arriving but position packets aren't - check the rebroadcaster's [Output Viewer](../manual/output-viewer.md).

## Card body - offline state

When a card is offline, the body shows the same section layout but every numeric field reads `---` and the colors mute to gray:

| Section | Offline rendering |
|---------|-------------------|
| Latitude / Longitude | `---` and `---` |
| Altitude / Airspeed / Heading | `---` in each colored cell (colors muted) |
| Nearest airport | `---` |
| Footer | Port still shown; packet count still shown (the count from before going offline) |

## Online vs offline - how the dashboard decides

A simulator is considered **online** if the dashboard has received any position packet from it within the last **5 seconds**.

| Window | Status |
|--------|--------|
| 0 s since last packet | Online |
| 5 s with no packet | Still online (just) |
| 5+ s with no packet | Offline |

The check is re-evaluated as part of every WebSocket broadcast, which happens once per second. So the offline transition is sub-second after the 5 s timeout expires.

**Heartbeats do not count as position packets** - only the actual position payload. A rebroadcaster that's idle (rebroadcaster running, but the upstream sender silent) sends heartbeats every second but no position. From the dashboard's perspective, that card is offline.

## Hover and click behavior

| State | Hover | Click |
|-------|-------|-------|
| Online, position view | Card raises slightly (`hover:scale-[1.02]`), shadow deepens, cursor becomes pointer. | Opens `https://www.google.com/maps?q=<lat>,<lon>` in a new tab. |
| Offline, position view | No hover effect. | No-op. |
| Any state, health view | No hover effect. | No-op. |

The click handler is `openGoogleMaps()`. It builds the URL and calls `window.open(url, '_blank')`. No Maps API key, no embedded map - just a query-string handoff.

## Visual sequence: card going from online to offline

1. Rebroadcaster stops emitting position packets (USB unplugged, container restarted, network broke).
2. For 5 seconds the card continues to show its last known position (green border, ONLINE pill).
3. At the 5-second mark, the next WebSocket broadcast flips `is_online` to `false`.
4. The card transitions: border goes from green to gray, ONLINE -> OFFLINE, every numeric field becomes `---`, opacity drops a bit (75%).

There is no fade animation - the transition is one frame.

## Visual sequence: offline going back to online

1. Rebroadcaster resumes emitting position packets.
2. The first packet arrives at the dashboard's listener.
3. On the next WebSocket broadcast, `is_online` flips back to `true`.
4. The card transitions: gray -> green, all fields populate with the new values.

Packet count picks up where it left off (the dashboard never resets it on offline - resets only happen on container restart).

## When the values look wrong

| Symptom | Likely cause |
|---------|--------------|
| Card is the wrong aircraft's data | `SIM_N_PORT` doesn't match the rebroadcaster's `AUTO_START_UDP_RETRANSMIT_PORT`. The dashboard identifies cards by port, not by payload content. |
| Altitude is hundreds of thousands of feet | Sender or rebroadcaster published a bad value. Drop back to the simulator's [Status Display](../manual/status-display.md) to see what the source thinks the value is. |
| Nearest airport is on a different continent | Lat or lon sign is wrong (positive vs negative for E/W or N/S). Check the upstream source. |
| Packet count is stuck | Rebroadcaster is sending heartbeats but no position. The upstream sender is silent. |
| Port shown in the footer is unexpected | `SIM_N_PORT` is from the dashboard side. Verify the compose file. |

## Persistent state

The card has no persistent state - it's a pure rendering of the data the WebSocket delivers. Configuration that drives card identity (name, port, GPS system label) lives on the dashboard side via env vars; see [Configuration](configuration.md).

## What's next

- [Health Chain](health-chain.md) - what replaces the card body in health view.
- [Configuration](configuration.md) - how `SIM_N_*` env vars become cards.
- [Fleet Monitoring](../user-guides/fleet-monitoring.md) - end-to-end multi-simulator setup.
