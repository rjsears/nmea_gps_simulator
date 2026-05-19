# Common UI Elements

The simulator UI has a small set of elements that show up on every screen, independent of the mode you're running. This page covers them in one place so the mode-specific pages don't have to repeat the same content.

<!-- SCREENSHOT-PENDING: common-ui-01-header.png - header showing logo, theme toggle, username, logout. -->

## The header

Persistent at the top of every Dashboard screen. Three areas: branding on the left, theme toggle in the middle, user controls on the right.

| Area | Element | Behavior |
|------|---------|----------|
| **Left** | LOFT logo + "GPS Emulator" text | Static. Click does nothing - the app is single-page. |
| **Middle** | Theme toggle (sun / moon icon) | Toggles light <-> dark. See [Theme toggle](#theme-toggle). |
| **Right** | Username placeholder + logout door icon | Username currently hard-coded to `admin`. Logout clears the session and bounces to Login. See [Logout](#logout-button). |

## Theme toggle

| State | Icon shown | Click result |
|-------|------------|--------------|
| Light mode active | **Moon** icon | Switches to dark mode. |
| Dark mode active | **Sun** icon | Switches to light mode. |

The icon shows the **target** mode (what you'll get if you click), not the current mode. This matches the convention most UIs use.

### How theme preference is stored

| Source | Order |
|--------|-------|
| `localStorage["theme"]` | Highest priority. Set the first time you flip the toggle. Possible values: `"light"`, `"dark"`, or `"system"`. |
| OS preference (`prefers-color-scheme`) | Used when `localStorage["theme"]` is unset or set to `"system"`. |
| Hard default | Light, if nothing else can be determined. |

The preference is per-browser per-host. Opening the dashboard in another browser (or in incognito) starts you fresh.

!!! info "The Login screen reads the same preference"
    `useEffect` on the Login route reads `localStorage["theme"]` the same way the Dashboard does, so you don't get a flash of the wrong theme on first paint.

## Logout button

| Trigger | Effect |
|---------|--------|
| Click the logout icon | `POST /api/auth/logout` clears the server-side session, removes the cookie, React calls `navigate('/login')`. |
| Browser closed without logout | The cookie is session-only (no `Max-Age` / `Expires`). It dies with the browser. Server-side session record persists until container restart or until it's evicted - in practice this is fine because the next API call from a fresh browser returns 401 and forces Login. |
| `BYPASS_AUTH=true` | The logout endpoint is still callable but the next page load sees `authenticated: true` from `/api/auth/check` and skips Login again. |

## The status badge in errors and notifications

Errors surface in red banners near the top of the column they came from. They have a small alert icon and (where appropriate) a Dismiss button.

| Banner | Origin | What you do |
|--------|--------|-------------|
| **Error loading status** (full-screen) | Initial fetch on app mount failed. | Check that the container is up and that the browser can reach `http://<host>/api/status`. |
| **API error** (top of Dashboard, dismissible) | A subsequent `/api/*` call returned non-2xx. | Read the text, fix the issue (often missing config or device not reachable), press Dismiss, retry. |
| **Login error** | Failed `/api/auth/login` response. | "Invalid credentials" or a server error. Re-enter and retry. |

The banners do **not** clear themselves on a timer - they stay visible until you press Dismiss or trigger a successful follow-up that replaces them.

## Loading states

The Dashboard renders one of three full-page states during startup:

| State | Visual | Cause |
|-------|--------|-------|
| Initial `/api/status` in flight | Spinning loader, "Loading..." text | App just mounted. Resolves in ~100 ms on a healthy host. |
| `/api/status` failed | Red error card with the error text | Same as the error banner above, but full-screen. |
| Status received, local state still initializing | Spinning loader, "Initializing..." text | Tiny gap between `useEffect` running and the local-state setter completing. Usually invisible. |

Once past those three, you land on the Dashboard proper.

## Multi-browser sync

You can open the Dashboard from multiple browsers (or multiple tabs) at the same time. They stay in sync via the WebSocket at `/ws`.

| Trigger | What happens in other open browsers |
|---------|------------------------------------|
| You toggle a mode or change a slider in Browser A | The server-side state update is broadcast over `/ws`. Browser B sees its `useStatus` hook fire and re-renders with the new value. Lag: typically < 200 ms. |
| Browser A starts the emulator | Browser B's Start button replaces itself with a Stop button; output begins scrolling in B's Output Viewer; status display updates. |
| Browser B stops the emulator | Same in reverse. |
| Browser A logs out | Browser B is **not** automatically logged out. Each browser holds its own session cookie. |

This is covered in depth at [Multi-Browser Sync](../user-guides/multi-browser-sync.md), including the WebSocket reconnect behavior and the failure modes when the WebSocket connection drops.

## WebSocket reconnect

If the WebSocket disconnects (network blip, container restart, browser sleep), the front end attempts to reconnect with a short delay. The user-visible signal is:

| Symptom | Likely cause |
|---------|--------------|
| Output Viewer stops scrolling | WebSocket disconnected. Reconnect attempts begin within ~1 s. |
| Status Display values freeze | Same. |
| Both resume on their own | Reconnect succeeded. No action needed. |
| Status banner appears with a connection-error message | Reconnect has failed multiple times. Check whether the container is still up. |

The reconnect logic lives in `frontend/src/hooks/useWebSocket.js`. The connect retry interval is hard-coded (a few seconds). It will keep trying forever - the container restart pattern is "the browser will catch up on its own once the container is back."

## Persistent state for the common UI

| Setting | UI control | Storage | Survives anything? |
|---------|-----------|---------|--------------------|
| Theme | Theme toggle button | `localStorage["theme"]` | Per-browser, per-host. Survives container restarts, simulator restarts, even a reinstall of the simulator on the same host - it lives entirely client-side. |
| Auth session | (created at Login) | Cookie `gps_emulator_session` + in-memory dict on the server | Survives until logout, browser close, or container restart - whichever comes first. |

## What's next

- [Login](login.md) - the screen before the Dashboard.
- [Dashboard Overview](dashboard-overview.md) - the main app layout.
- [Multi-Browser Sync](../user-guides/multi-browser-sync.md) - WebSocket behavior in depth.
- [Security](../reference/security.md) - auth model and hardening.
