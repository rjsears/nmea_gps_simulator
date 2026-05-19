# Login

The login screen is the entry point to the simulator UI when authentication is enabled. With `BYPASS_AUTH=true` (the default in the example `docker-compose.yml`), you never see it - the URL bar takes you straight to the [Dashboard Overview](dashboard-overview.md).

This page documents the login screen and the auth model behind it. If you're configuring a deployment, the security trade-offs live on the [Security](../reference/security.md) reference page.

<!-- SCREENSHOT-PENDING: login-01-overview.png - login form, map background. -->

## The screen

| Element | Default | What it is |
|---------|---------|------------|
| **Logo + title** | "GPS Emulator" with the LOFT logo | Branding. Replaced by editing `frontend/public/LOFT_logo_130x100.png` and rebuilding the frontend. |
| **Username field** | empty (placeholder `admin`) | Auto-completed by the browser if you've logged in before. |
| **Password field** | empty | Standard `type="password"` field. |
| **Sign in button** | enabled when both fields are non-empty | Shows a spinner while the POST to `/api/auth/login` is in flight. |
| **Error banner** | hidden | Red banner with an alert icon, surfaces "Invalid credentials" or other login failures. |
| **Footer** | version + author | Static, comes from the React build. |

The background is a world-map GIF (`map_background.gif`) that follows the theme - a dark overlay layers over it in dark mode. The theme is read from `localStorage` on mount, so if you set it in a previous session it carries forward to the login screen.

## How authentication works

| Layer | Where | Detail |
|-------|-------|--------|
| Credentials | `USERNAME` / `PASSWORD` env vars | Read by `backend/config.py` at container start. Defaults: `admin` / `changeme`. |
| Verification | `POST /api/auth/login` | Compares submitted creds to the env-var values. Constant-time comparison via `secrets.compare_digest`. |
| Session storage | In-memory dict in `backend/auth.py` | Token is a UUID4. Sessions evaporate on container restart. |
| Session transport | Cookie `gps_session` | `HttpOnly`, `SameSite=Lax`. Not `Secure` (the container speaks plain HTTP; put a TLS reverse proxy in front of it for production). |
| Session check | `GET /api/auth/check` | Front-end calls this on mount via `useAuth.jsx` to decide whether to render Login or Dashboard. |
| Logout | `POST /api/auth/logout` | Deletes the server-side session record and clears the cookie. Triggered by the logout icon in the header on the Dashboard. |

## `BYPASS_AUTH` semantics

| `BYPASS_AUTH` | What happens |
|---------------|--------------|
| `true` (default in the example compose file) | Every `/api/auth/check` call returns `{authenticated: true}`. The Login route effectively never gets rendered - the React app skips straight to the Dashboard. `/api/*` endpoints accept every request. |
| `false` | Standard cookie-session flow as above. Unauthenticated `/api/*` calls return 401. |
| Any other value | Treated as falsy. The simulator does not parse `"yes" / "no"` or any other variant - only the exact string `"true"` flips the bypass on. |

!!! danger "Do not run `BYPASS_AUTH=true` on a network you don't control"
    The `/api/control` endpoint can start NMEA emission to connected hardware. The `/api/position` endpoint can move the position arbitrarily. Anyone who can reach the UI with bypass on can do both. Treat the bypass strictly as a closed-lab convenience and never as a production setting.

## What happens on a successful login

1. POST to `/api/auth/login` with the form values.
2. Server validates, creates a session, sets the cookie, returns `{success: true, message: "Login successful"}`.
3. React calls `navigate('/')` and the Dashboard renders.

## What happens on a failed login

| Cause | What you see |
|-------|--------------|
| Wrong username or password | Red banner: "Invalid credentials". Form remains; both fields preserved. |
| `USERNAME` or `PASSWORD` env var was empty at container start | Effectively every login fails with "Invalid credentials" because the constant-time comparison can never match an empty string. Set both env vars before exposing the UI. |
| Server error (database, network) | Banner shows whatever message the server returns. The form remains. |

The login form does **not** rate-limit on the front end. The container also does not impose its own rate limit. Run a reverse proxy (nginx, Caddy, Cloudflare) with rate limiting in front of the UI for production.

## Session lifetime

| Trigger | What happens to the session |
|---------|----------------------------|
| Operator clicks logout in the Dashboard header | Server-side record is deleted, cookie is cleared. Next API call returns 401, the React app falls back to Login. |
| Container restarts | The in-memory session dictionary is wiped. Every existing cookie becomes orphaned. Next API call returns 401, every connected operator is bumped to Login. |
| The cookie expires | The cookie has no explicit `Max-Age` / `Expires`, so it lives until the browser session ends. Once the browser is closed, the cookie is gone. |
| The cookie is forged or tampered with | The session token won't match any record on the server. Treated as 401. |

There is no concept of "session refresh" or "remember me" - by design the simulator is meant to be operated by someone actively at the console.

## Persistent state

| Setting | Env var | Effect |
|---------|---------|--------|
| Username | `USERNAME` | Login credential. Required for non-bypass auth. |
| Password | `PASSWORD` | Login credential. Required for non-bypass auth. |
| Bypass auth | `BYPASS_AUTH` | `true` skips the Login screen entirely. |

The login screen itself has no persistent state - what you type is in memory until you submit.

## What's next

- [Dashboard Overview](dashboard-overview.md) - the screen you land on after a successful login.
- [Common UI Elements](common-ui.md) - the header, theme toggle, logout button (all on the Dashboard side).
- [Security](../reference/security.md) - the full hardening checklist including TLS termination, rate limiting, and the bypass-auth trade-off.
