# Dashboard Overview

The Fleet Dashboard is a single-screen, grid-of-cards UI. There is no login, no mode selector, no per-card configuration. The only operator controls in the entire app are the **health view toggle**, the **theme toggle**, and the **connection-status badge** in the header.

<!-- SCREENSHOT-PENDING: dashboard-overview-01-grid.png - dashboard with 6 cards in 3-column grid, header visible. -->

## The layout

```
+--------------------------------------------------------------------------+
|  HEADER                                                                  |
|  [Logo] Fleet Dashboard                          [Health] [Theme]        |
|         Real-time simulator monitoring                    [Connected]    |
+--------------------------------------------------------------------------+
|                                                                          |
|  +-------SIM CARD-------+  +-------SIM CARD-------+  +-------SIM CARD--+ |
|  | CJ3        ONLINE    |  | Ultra      ONLINE    |  | CL350   OFFLINE| |
|  | Lat / Lon            |  | Lat / Lon            |  |  ---            | |
|  | Alt / Speed / Heading|  | Alt / Speed / Heading|  |  ---            | |
|  | Nearest airport      |  | Nearest airport      |  |  ---            | |
|  | Port / Packets       |  | Port / Packets       |  | Port / Packets  | |
|  +----------------------+  +----------------------+  +-----------------+ |
|                                                                          |
|  ...more cards if more simulators are configured...                      |
|                                                                          |
+--------------------------------------------------------------------------+
| LOFT Fleet Dashboard v1.0.0 • Richard J. Sears ©2026 • N simulators      |
+--------------------------------------------------------------------------+
```

Cards lay out in a responsive 3-column grid on a desktop, 2 columns on tablets, single column on phones. The grid scales to however many simulators you've configured - 1, 6, 20 (the maximum the env-var parser supports).

## Header

| Element | What it does |
|---------|--------------|
| **LOFT logo + "Fleet Dashboard" title + subtitle** | Branding. The subtitle reads "Real-time simulator monitoring". Static. |
| **Health toggle** (stethoscope icon) | Switches every card between **position view** and **health view**. See [Health Chain](health-chain.md). |
| **Theme toggle** (sun/moon icon) | Toggles light <-> dark. Stored in `localStorage` as `dashboard-theme` (distinct from the simulator's `theme` key so the two apps' themes can differ). |
| **Connection badge** | Green "Connected" or red "Disconnected" with a dot. Reflects the WebSocket connection to `/ws`. |

The connection badge is the most important diagnostic on the header. If it's red, the cards are stale - whatever you see is from before the WebSocket dropped.

### Health toggle states

| State | Cards show |
|-------|------------|
| Health toggle **off** (default) | **Position view**: lat/lon, altitude, airspeed, heading, nearest airport, packet count. Online cards are clickable - clicking opens Google Maps centered on the aircraft. |
| Health toggle **on** | **Health view**: the four-node diagnostic chain (Dashboard -> Emulator -> Simulator -> GPS Data) with the failing-segment message. Cards are not clickable. |

The toggle is global - flipping it changes every card at once. There is no per-card health view.

## Card grid

The grid renders one card per configured simulator. Cards stay in the order they're declared in env vars (`SIM_1_*` first, `SIM_2_*` second, etc.).

| State | Card appearance |
|-------|-----------------|
| Online | Green border, green ONLINE pill, all fields populated, cursor changes to pointer on hover, hover slightly raises the card. |
| Offline | Gray border, gray OFFLINE pill, position/altitude/speed/heading/airport all show "---", not clickable. |
| Health view, all OK | Green border, green ALL OK pill, four green nodes in the chain. |
| Health view, issue | Red border, red ISSUE pill, failing node shown in red. |

See [Simulator Card](simulator-card.md) for per-field detail.

## Click-through to Google Maps

In position view, any online card is clickable. Clicking opens `https://www.google.com/maps?q=<lat>,<lon>` in a new browser tab, centered on the aircraft's current position.

This is intentionally a simple URL trick - no Maps API key required, no JavaScript embedding, just a query-string lookup. Works from anywhere with browser internet access.

Offline cards are not clickable (no real position to navigate to). Health-view cards are also not clickable (the chain view is the primary content; we don't want a misclick on the card to navigate away).

## Empty state

If the dashboard starts before any simulator packets have arrived (no `SIM_N_NAME` env vars, or all of them set but no rebroadcasters running yet), the main area shows a centered spinner with "Waiting for simulator data..."

This state resolves the moment a single simulator card has a configuration entry plus a packet arrival.

## Footer

A persistent line at the bottom showing version, author, and the **configured simulator count** (the number of `SIM_N_*` entries the dashboard parsed at start, not necessarily the number that are online right now).

## WebSocket connection lifecycle

The connection badge reflects the state of `/ws`:

| Lifecycle event | Badge |
|-----------------|-------|
| Page loads | Red "Disconnected" until WebSocket completes its handshake. |
| WebSocket open | Green "Connected". |
| WebSocket drops (network blip, container restart) | Red "Disconnected" until the reconnect logic re-establishes. |
| Reconnect succeeds | Green "Connected". A momentary flash of red may be visible. |

The reconnect runs on a 2-second timer. The dashboard will keep trying forever - the design assumes the dashboard is left up and watched. There is no manual reconnect button.

## Multi-browser sync

Like the simulator, the dashboard fans out updates over a single WebSocket per browser. Two browsers viewing the same dashboard see the same state, synchronized by the server.

| Action | Effect on other browsers |
|--------|--------------------------|
| One operator toggles the health view | Other browsers' toggles **do not** change - the health toggle is per-browser-window state. |
| One operator toggles the theme | Same - per-browser. |
| A new simulator packet arrives | All browsers see the card update simultaneously. |
| A simulator goes offline (5 s of no packets) | All browsers see the card flip to gray simultaneously. |

## Persistent state

| Setting | Storage | Survives restart? |
|---------|---------|-------------------|
| Theme | `localStorage["dashboard-theme"]` | Per-browser, per-host. Survives anything. |
| Health toggle | In-memory React state | No - resets to off on every page load. |
| Connection state | In-memory React state | No. |
| Simulator data | In-memory on the server; broadcast to browsers via WebSocket | No - the dashboard is stateless across restarts. Every restart starts the per-card packet count back at 0. |

## What's next

- [Simulator Card](simulator-card.md) - per-card field reference.
- [Health Chain](health-chain.md) - the diagnostic view.
- [Configuration](configuration.md) - env vars that drive the card list.
