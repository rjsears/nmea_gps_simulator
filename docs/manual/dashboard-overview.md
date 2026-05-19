# Dashboard Overview

The Dashboard is the single screen the simulator UI lives on. It's a three-column layout that adapts based on the operating mode you've chosen. Everything you do with the simulator - configuration, starting, stopping, watching live output - happens here.

This page is orientation; each panel has its own page in this manual for the per-control reference.

<!-- SCREENSHOT-PENDING: dashboard-01-overview.png - full dashboard with Rebroadcaster mode active, all panels visible. -->

## The layout at a glance

```
+---------------------------------------------------------------+
|  HEADER                                                       |
|  [Logo] GPS Emulator                  [Theme] admin [Logout]  |
+---------------------------------------------------------------+
|                                                               |
|  +-----LEFT-----+   +----CENTER----+   +----RIGHT----+        |
|  | Mode         |   | Position     |   | NMEA        |        |
|  | (Standalone/ |   | (Airport)    |   | (Sentence   |        |
|  | Sender/      |   |              |   |  picker)    |        |
|  | Receiver/    |   |              |   |             |        |
|  | Rebroadcast) |   | Navigation   |   |             |        |
|  |              |   | (Altitude /  |   |             |        |
|  | Mode-        |   |  Airspeed /  |   |             |        |
|  | specific     |   |  Heading)    |   | Status      |        |
|  | config       |   |              |   |             |        |
|  | (USB, EFB,   |   | Start / Stop |   |             |        |
|  |  Network,    |   |              |   |             |        |
|  |  Rebroadcast)|   |              |   |             |        |
|  +--------------+   +--------------+   +-------------+        |
|                                                               |
|  +---------- OUTPUT VIEWER (full width) ----------+           |
|  | $GPGGA,...   $GPRMC,...   $GPGLL,...           |           |
|  +------------------------------------------------+           |
+---------------------------------------------------------------+
| NMEA GPS Emulator v1.0.0 • Richard J. Sears ©2026             |
+---------------------------------------------------------------+
```

On a laptop screen the three columns sit side-by-side; on a narrower screen they stack vertically. The Output Viewer is full-width across the bottom on every layout.

## Header

The header is the same on every screen of the app. It's documented in detail on the [Common UI Elements](common-ui.md) page.

| Element | What it does |
|---------|--------------|
| **Logo + "GPS Emulator" text** | Branding. Click does nothing - the app is single-page. |
| **Theme toggle** (sun / moon icon) | Toggles between light and dark. Preference is saved to `localStorage` and respected across sessions and across the Login screen. |
| **`admin` username** | Static placeholder showing who is logged in. Today it's hard-coded to "admin" - the underlying auth check is for any valid session. |
| **Logout button** (door icon) | Calls `POST /api/auth/logout`, clears the session cookie, navigates to Login. |

## Left column - mode and configuration

The left column always has the **Mode Selector** at the top. Picking a mode (Stand Alone / Sender / Receiver / Rebroadcaster) reveals the configuration panel for that mode below it.

| Mode | Panel revealed | Manual page |
|------|----------------|-------------|
| Stand Alone | **Output Settings** (USB + EFB blocks) | [Stand-Alone Mode](mode-standalone.md) |
| Sender | **Sender Settings** (NMEA + EFB + USB blocks) | [Sender Mode](mode-sender.md) |
| Receiver | **Receiver Settings** (protocol + port) plus a separate **Serial Selector** panel | [Receiver Mode](mode-receiver.md) |
| Rebroadcaster | **Rebroadcaster Settings** (EFB + UDP retransmit + USB blocks) | [Rebroadcaster Mode](mode-rebroadcaster.md) |

The mode picker is disabled while the emulator is running. Press **Stop** if you need to switch.

## Center column - position, navigation, and control

The center column has three panels, top to bottom:

| Panel | What it does | Manual page |
|-------|--------------|-------------|
| **Position** (airport picker) | Snaps lat / lon to an airport in the built-in database. Manual lat/lon entry is also exposed. | [Airport Lookup](airport-lookup.md) (database) + [Navigation Controls](navigation-controls.md) (the inputs) |
| **Navigation** (altitude, airspeed, heading) | Sets target altitude / airspeed / heading. The engine ramps to these values at configurable rates. | [Navigation Controls](navigation-controls.md) |
| **Start / Stop** | Big, can't-miss button. Disabled until every required field is filled - hovering reveals the disabled reason as a tooltip. | (see below for the reasons) |

In **Receiver Mode** the position panels are disabled - the position comes from the upstream sender, not from this UI. The Navigation panel grays out for the same reason.

### Why the Start button might be disabled

The dashboard validates configuration before letting you press Start. The tooltip on the disabled button names the missing piece.

| Tooltip message | What's missing |
|-----------------|----------------|
| "Select an operating mode" | None of the four mode tabs is selected. |
| "Select an airport" | Stand-Alone or Sender mode with no airport selected yet. |
| "Select at least one output (USB or EFB)" | Stand-Alone with both USB and EFB blocks off. |
| "Select a USB device" | A mode requires USB output but no `/dev/...` device is picked. |
| "Enter target IP address for NMEA output" | Sender's NMEA block is on but Target IP is empty. |
| "Enable at least one output (NMEA, EFB, or USB)" | Sender mode with all three output blocks off. |
| "Select Broadcast or Garmin Pilot/ForeFlight (IP Address)" | EFB master toggle is on but neither sub-option is checked. |
| "Enter a simulator name for EFB output" | EFB output enabled with no Simulator Name. |
| "Enter IP address(es) for EFB output" | EFB IP targeting on with the target-IPs field empty. |
| "Select at least one rebroadcast output (USB, EFB, or UDP)" | Rebroadcaster with all three output blocks off. |
| "Enter target IP for UDP retransmit" | Rebroadcaster's UDP retransmit on with no target IP. |

If you see a different message, it came from the server (an error during Start). Read the API error banner above the panels for details.

## Right column - NMEA sentences and status

| Panel | What it does | Manual page |
|-------|--------------|-------------|
| **NMEA Sentences** | Toggle which optional NMEA sentences to emit. `GPGGA` and `GPRMC` are always on. | [NMEA Sentences](nmea-sentences.md) |
| **Status Display** | Live readout of position, altitude, speed, heading, packet counts, mode state, selected device. | [Status Display](status-display.md) |

The NMEA picker is disabled in Receiver mode (the receiver inherits whatever the sender's payload contains) and while the emulator is running (sentence list is read once at Start).

## Bottom - Output Viewer

Full-width terminal-style scrolling view of the NMEA bytes being emitted (or, in Receiver mode, the incoming packets being parsed). Pause / resume, clear, message count - see [Output Viewer](output-viewer.md).

## Error handling

The dashboard surfaces two kinds of errors:

| Error class | Where it appears | What you do |
|-------------|------------------|-------------|
| **Initial fetch failure** | Full-screen "Error loading status" message with the error text. | The container probably isn't running, or networking between your browser and the container is broken. Check `docker compose ps` and your network. |
| **API-call failure** during normal use | Red banner above the columns with a Dismiss button. | The API call (`/api/control`, `/api/position`, etc.) returned a non-2xx. The text is the server's error message. Dismiss after reading. |

Errors do not roll the local state back. If a "Start" call failed and you see the banner, the React state already says `is_running: false` - it just couldn't transition. Read the message, fix the issue, try again.

## Multi-browser sync

Two browser windows pointed at the same simulator container stay in sync, in near-real-time. The mechanism is the WebSocket at `/ws` - both windows subscribe, every server-side state change is broadcast to all connections.

This is covered in detail at [Multi-Browser Sync](../user-guides/multi-browser-sync.md). Practical effect for this page: you can open the dashboard from multiple devices and they'll always agree on the running state.

## Persistent state

Most of what the dashboard manages is **per-run** and lives only in the container's memory. The only things that survive a container restart are the env-var defaults documented on each mode's page (`DEFAULT_LAT`, `AUTO_START_MODE`, etc.). See [Environment Variables](../reference/env-vars.md) for the full reference.

## What's next

- [Login](login.md) - the screen before this one.
- The four operating modes - each linked from the Mode Selector section above.
- [Output Viewer](output-viewer.md) - live NMEA stream.
- [Status Display](status-display.md) - live runtime status.
- [Common UI Elements](common-ui.md) - header, theme toggle, multi-browser sync, help dialog.
