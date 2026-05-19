# Status Display

The **Status** panel in the right column gives you a single-glance summary of what the simulator is doing right now: emulator state, serial selection, network connection state, current position, altitude, airspeed, heading.

It is purely a display - no controls. Updates are pushed via WebSocket and rendered as soon as they arrive (typically once per second while running).

<!-- SCREENSHOT-PENDING: status-display-01-overview.png - Status panel with all rows visible, emulator running. -->

## Rows

| Row | What it shows | When it appears |
|-----|---------------|-----------------|
| **Emulator** | Green dot + "Running" or red dot + "Stopped" | Always. |
| **Serial** | Green dot + selected device path, or gray dot + "Not selected" | Always. |
| **Network** | Green/red dot + `PROTOCOL : PORT` (e.g., `UDP : 12000`) | Only in Sender or Receiver mode. |
| **Position** | `lat, lon` to four decimal places | Always. |
| **Altitude** | Current altitude in feet with thousands separators | Always. |
| **Airspeed** | Current airspeed in knots | Always. |
| **Heading** | Current heading in degrees | Always. |

The lat/lon, altitude, airspeed, and heading values are the **current** values, not the targets you set via the Navigation panel. So during a ramp, the slider says 35,000 ft but the Status row says whatever the engine has currently reached - useful for confirming the ramp is progressing.

## Indicator colors

| State | Dot color | Text color |
|-------|-----------|------------|
| Emulator running, serial selected, network connected | Green | Green / dark |
| Emulator stopped, serial unselected, network disconnected | Red or gray | Red or muted |

The `status-indicator` class drives the dot styling - it's a small circular badge that switches between `bg-green-500` and `bg-red-500` (or muted gray in the "not configured" case).

## What `network_connected` means

The Network row only appears in Sender or Receiver mode and reflects `status.network_connected` from the API response.

| Mode | What "connected" means |
|------|------------------------|
| Sender, **UDP** | Socket exists. UDP is connectionless so this just confirms the sender thread is alive and ready to send. |
| Sender, **TCP** | The TCP connection to the configured target IP:port is open. If the target is unreachable or the peer dropped, this goes red. |
| Receiver, **UDP** | The listen socket is bound. |
| Receiver, **TCP** | At least one TCP client is currently connected. Goes red between connections. |

This is a runtime-only flag - it isn't persisted, isn't an env var, and resets every Stop / Start cycle.

## Update cadence

The Status panel re-renders whenever the `useStatus` hook (`frontend/src/hooks/useStatus.js`) receives a new state object. That happens on:

| Trigger | Cadence |
|---------|---------|
| Server-side state changes (mode toggle, slider drag, Start/Stop) | Immediate broadcast over WebSocket. |
| Position update from the NMEA engine | Once per tick (1 Hz while running). |
| Heartbeat from the dashboard's polling loop | Every 1 s. |

In practice you'll see numeric values tick over once per second while the emulator is running; mode-change events appear within ~100 ms of the click.

## Difference between Status, Output Viewer, and the Navigation panel

It's easy to confuse these three.

| Panel | Tells you |
|-------|-----------|
| **Navigation Controls** | What you've *asked for* (target altitude, airspeed, heading). |
| **Status Display** | What the engine *currently has* (smoothed values during a ramp). |
| **Output Viewer** | The literal NMEA bytes on the wire, which encode the current values. |

If you set altitude to 35,000 and watch:

- The slider stays at 35,000.
- The Status shows 0 -> 500 -> 1000 -> ... -> 35,000 as the engine ramps.
- The Output Viewer's `GPGGA` altitude field tracks the Status value byte-for-byte.

## When something is wrong

| Symptom | What to check |
|---------|--------------|
| Status says "Running" but no NMEA in the Output Viewer | WebSocket connection from the viewer broke. Reload the page. |
| Status says "Stopped" but Output Viewer is still scrolling | Almost impossible - the Start button toggles both. If you see it, you're looking at stale data; reload. |
| Network row says disconnected in TCP mode | Peer is unreachable. Check the target host and the port-forward path. |
| Serial row says "Not selected" but Start is enabled in non-USB modes | Expected - USB output is optional in Stand-Alone, Sender, and Rebroadcaster; Start can succeed without it. |
| Position values stuck at `0, 0` | The engine started without an airport selected and `DEFAULT_LAT`/`DEFAULT_LON` are unset or zero. Pick an airport. |

## Persistent state

The Status panel doesn't have its own persistent state - it's a pure read of `status` from the API. Everything it displays is documented in [Environment Variables](../reference/env-vars.md) (the defaults at boot) and on each mode's manual page (the runtime values).

## What's next

- [Output Viewer](output-viewer.md) - the live byte stream that backs the numeric values shown here.
- [Navigation Controls](navigation-controls.md) - where the target values come from.
- [Health Chain](../dashboard-manual/health-chain.md) - the Fleet Dashboard's equivalent multi-emulator health view.
