# Multi-Browser Sync

Both the simulator UI and the Fleet Dashboard support multiple browsers viewing the same backend simultaneously. State (slider positions, mode selections, fleet card values) stays consistent across browsers via a per-app WebSocket fan-out.

This page documents the mechanism, the reconnect behavior, and the failure modes - useful when you're trying to understand why two windows seemed to disagree.

## What's synchronized

### Simulator UI

| Thing | Synchronized? |
|-------|---------------|
| Operating mode selection | Yes - flipping mode in Browser A changes Browser B's selector. |
| Slider positions (altitude, airspeed, heading) | Yes. |
| Airport selection | Yes (with a small heuristic to not stomp on what you're currently typing). |
| Network config target IP / port / protocol | Yes. |
| EFB block toggles, target IPs, sim name | Yes. |
| NMEA sentence selection | Yes (when not running; the panel is disabled when running anyway). |
| Serial device + baud | Yes. |
| Running / stopped state | Yes - Start in A causes B's button to flip to Stop. |
| Output Viewer scroll | **No** - each browser has its own WebSocket and buffer. Pausing one doesn't pause the other. |
| Theme (light/dark) | **No** - per-browser, stored in `localStorage`. |
| Errors / banners | **No** - errors from a server-side action you initiated show only in your browser. |

### Fleet Dashboard

| Thing | Synchronized? |
|-------|---------------|
| Card grid contents (per-sim position, altitude, etc.) | Yes - any update on the server is pushed to every browser. |
| Card online/offline status | Yes. |
| Health view toggle | **No** - per-browser. |
| Theme (light/dark) | **No** - per-browser. |
| Connection-status badge | Reflects each browser's own WebSocket health. |

In both apps, the rule is: **server-side state syncs; per-browser UI preferences don't.**

## How it works

```mermaid
sequenceDiagram
    participant A as Browser A
    participant B as Browser B
    participant Server as FastAPI backend

    A->>Server: REST POST /api/config/modes (toggle Rebroadcaster on)
    Server->>Server: update in-memory state
    Server->>A: 200 OK
    Server->>A: WebSocket: status update {modes: {rebroadcaster: true}}
    Server->>B: WebSocket: status update {modes: {rebroadcaster: true}}
    A->>A: useStatus hook fires; re-render
    B->>B: useStatus hook fires; re-render
```

Step by step:

1. Browser A makes a REST call that mutates server state.
2. The server updates its in-memory state.
3. The server returns 200 to Browser A.
4. The server **broadcasts** the new state over WebSocket to every connected client (including Browser A, which gets a redundant copy - the client de-duplicates harmlessly).
5. Each client's `useStatus` hook fires; React re-renders affected components with the new state.

Typical end-to-end latency on a LAN: <200 ms.

## The WebSocket endpoint

Both apps expose a WebSocket at `/ws`. The connection lives for the duration of the browser tab.

| Detail | Simulator | Fleet Dashboard |
|--------|-----------|-----------------|
| Path | `/ws` | `/ws` |
| Subprotocol | none (default) | none |
| Initial message from server | None - waits for client | `fleet_state` payload (current snapshot) |
| Server -> client broadcast cadence | Event-driven (whenever state changes) plus 1 Hz position updates while running | Once per second |
| Client -> server messages | `ping` (responded with `pong`) | none |
| Server detects client disconnect | When socket closes; client removed from broadcast list | Same |

The simulator's WebSocket carries multiple message types (`status_update`, `nmea_output`, `position_update`). The dashboard's carries one type (`fleet_state`).

## Reconnect logic

If the WebSocket drops (network blip, container restart, browser sleep), the client attempts to reconnect.

### Simulator UI (frontend/src/hooks/useWebSocket.js)

| Detail | Value |
|--------|-------|
| First reconnect attempt | Almost immediately after `onclose` |
| Backoff | None - retries on a fixed short interval |
| Max retries | Infinite - the page assumes the container will come back |
| User-visible signal | The OutputViewer falls back to "Waiting for data..." or the value displays freeze |

### Fleet Dashboard (dashboard/frontend/src/App.jsx)

| Detail | Value |
|--------|-------|
| First reconnect attempt | 2 s after `onclose` |
| Backoff | Constant 2 s interval |
| Max retries | Infinite |
| User-visible signal | The connection badge in the header turns red |

The dashboard's reconnect signal is the most visible because the badge is always in view. The simulator UI is less obvious - you have to notice that things stopped updating.

## When the WebSocket disconnects

| Cause | What you see |
|-------|--------------|
| Container restart | Both browsers' connections drop simultaneously. Reconnect succeeds when the container is back up. State is reset to the env-var defaults; running state is lost (unless auto-start re-arms it). |
| Network blip (Wi-Fi drop) | Only the affected browser's connection drops. Other browsers are unaffected. The blipped browser catches up on reconnect. |
| Browser tab backgrounded | Modern browsers may throttle WebSocket events on inactive tabs. The connection stays open; messages queue. When the tab is foregrounded, the queue drains. |
| Browser closes without logout | The WebSocket closes naturally. The session cookie may persist (depends on browser settings). |
| Reverse proxy timeout | Some reverse proxies (default nginx) close idle WebSockets after 60 s. Add `proxy_read_timeout 3600;` for long-running connections. |

## Subtle gotcha: "the airport picker is fighting me"

The simulator's airport picker has special logic to avoid stomping on what you're typing in Browser A when Browser B picks an airport at the same time. Specifically: if `userIsEditing` is true (you're actively typing), the picker ignores the incoming `airportIcao` change from the WebSocket.

This means in rare race conditions, two browsers can have **different** values in the search field for ~1 second while one user is typing. The server-side state is consistent; only the search-field display lags. As soon as you stop typing or pick an airport, the values reconcile.

This is by design. It would be worse to have your half-typed `KCRQ` get overwritten by another user's `KSAN` selection mid-keystroke.

## Errors and banners

API errors (red banners) show only in the browser that initiated the failing call. If Browser A presses Start and the server returns an error, Browser A sees the banner; Browser B doesn't. Browser B sees the running state stay false (because the Start didn't actually succeed) but doesn't know why.

This is intentional - the operator who pressed the button is the one who needs to know what went wrong.

## Two browsers, two WebSockets, same content

Each browser opens its own WebSocket. The server broadcasts identical messages to all of them. So two browsers downloading the same `fleet_state` payload is two separate WebSocket sends, doubling outbound bandwidth from the dashboard.

For typical deployments (a handful of operator browsers), this is negligible. For unusual cases (50+ browsers reading the same dashboard), consider putting a WebSocket-aware reverse proxy or message bus in front of it.

## Practical tips

| Tip | Why |
|-----|-----|
| Leave the dashboard up on a wall display, then operate from your laptop browser. | The wall display passively sees what you do. No coordination overhead. |
| If two operators need to drive the same simulator, agree on roles first. | Both can technically drive; nothing stops them. But race conditions on slider drags are confusing. |
| Open `/ws` directly with `wscat` for debugging. | `wscat -c ws://<host>/ws` gives you the raw message stream. Handy when figuring out a sync issue. |
| Reload the page after a long absence. | If the browser has been backgrounded for hours, force a fresh connection to be sure you're in sync. |

## What's next

- [Common UI Elements](../manual/common-ui.md) - simulator-side header + WebSocket reconnect behavior.
- [Overview (Fleet Dashboard)](../dashboard-manual/overview.md) - dashboard-side header + connection badge.
- [API Reference](../reference/api-reference.md) - the REST endpoints that mutate state; every mutation triggers a sync broadcast.
