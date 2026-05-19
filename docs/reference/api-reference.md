# API Reference

The simulator and the Fleet Dashboard each expose a complete OpenAPI 3.x specification. Three views are available on each, served by the running container.

| URL | Purpose |
|-----|---------|
| `http://<host>/api/docs` | **Swagger UI** - interactive "try it out" explorer |
| `http://<host>/api/redoc` | **ReDoc** - clean read-only structured reference |
| `http://<host>/api/openapi.json` | **Raw OpenAPI JSON** - machine-readable spec for client generators and Postman |

The live Swagger UI is **authoritative**. The tables below are a navigation aid - they tell you which endpoint group covers what so you can jump to the right section in Swagger.

## Simulator API

### Authentication and access

| Default base URL | `http://<simulator-host>/api/` |
|------------------|-------------------------------|
| Auth | Cookie session (`gps_session`). The `Authorization: Bearer ...` pattern is **not** used. |
| Bypass | `BYPASS_AUTH=true` env var bypasses auth on every `/api/*` endpoint. |

To log in from a client:

```bash
curl -c cookies.txt -X POST http://<host>/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"changeme"}'

# Then use the cookie jar on subsequent calls:
curl -b cookies.txt http://<host>/api/status
```

### Endpoint groups

| Tag | Endpoints | What they do |
|-----|-----------|--------------|
| **Auth** | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/check` | Cookie session login / logout / status. |
| **Control** | `GET /api/status`, `POST /api/control`, `POST /api/position` | Read full state, start/stop the emulator, set position/altitude/speed/heading. |
| **Configuration** | `POST /api/config/modes`, `POST /api/config/network`, `POST /api/config/nmea`, `POST /api/config/serial` | Configure operating mode, network, NMEA sentence selection, serial. |
| **Serial** | `GET /api/serial/devices`, `POST /api/serial/select` | List USB-serial devices visible inside the container; select one. |
| **Airports** | `GET /api/airports/lookup/{icao}`, `GET /api/airports/search`, `GET /api/airports/list` | Airport database lookups. Same data as the UI picker. |
| **WebSocket** | `WS /ws` | Live state + NMEA stream. See [Multi-Browser Sync](../user-guides/multi-browser-sync.md). |
| (no tag) | `GET /health` | Unauthenticated. Returns `{"status": "healthy"}`. Intended for Docker healthchecks. |

The full list of paths (sourced from the running OpenAPI spec):

```
GET    /api/airports/list
GET    /api/airports/lookup/{icao}
GET    /api/airports/search
GET    /api/auth/check
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/config/modes
POST   /api/config/network
POST   /api/config/nmea
POST   /api/config/serial
POST   /api/control
POST   /api/position
GET    /api/serial/devices
POST   /api/serial/select
GET    /api/status
GET    /health
WS     /ws
```

### Common request bodies

Detailed schemas live in the live Swagger UI; this is a high-level orientation.

| Endpoint | Body shape |
|----------|-----------|
| `POST /api/auth/login` | `{"username": "...", "password": "..."}` |
| `POST /api/control` | `{"action": "start"}` or `{"action": "stop"}` |
| `POST /api/position` | Any subset of `{"lat", "lon", "altitude_ft", "speed_kts", "heading", "airport_icao"}` |
| `POST /api/config/modes` | `{"standalone": bool, "sender": bool, "receiver": bool, "rebroadcaster": bool, "usb_output": bool}` |
| `POST /api/config/network` | All Sender / Receiver / Rebroadcaster network fields. See Swagger. |
| `POST /api/config/nmea` | `{"gpgga": true, "gprmc": true, "gpgll": false, "gpgsa": false, "gpgsv": false, "gphdt": false, "gpvtg": false, "gpzda": false}` |
| `POST /api/config/serial` | `{"device": "/dev/ttyUSB0", "baudrate": 115200}` |
| `POST /api/serial/select` | `{"device": "/dev/ttyUSB0"}` |
| `GET /api/airports/search?q=KCRQ&limit=10` | Query string |

### WebSocket message types

The simulator's `/ws` carries multiple message types. The browser de-multiplexes by `type`.

| Type | Direction | Cadence | Payload |
|------|-----------|---------|---------|
| `status_update` | Server -> Client | Event-driven | Full or partial state |
| `nmea_output` | Server -> Client | 1 Hz while running | `{"sentences": ["$GPGGA,...", ...]}` |
| `position_update` | Server -> Client | 1 Hz while running | Position + ramp values |
| `ping` | Client -> Server | optional | Replies with `pong` |

The dashboard's `/ws` is simpler:

| Type | Direction | Cadence | Payload |
|------|-----------|---------|---------|
| `fleet_state` | Server -> Client | 1 Hz + on connect | `{"simulators": [{...per-sim fields}, ...]}` |

## Fleet Dashboard API

### Endpoint groups

| Tag | Endpoints | What they do |
|-----|-----------|--------------|
| **Status** | `GET /api/status` | One-shot HTTP snapshot of the same data the WebSocket pushes. |
| **WebSocket** | `WS /ws` | Live broadcast of every simulator's state, 1 Hz. |

The dashboard intentionally has a small API - configuration is deployment-time (env vars), not runtime. There's no "add a simulator" REST call.

## Authentication notes

### Simulator

| Mechanism | Details |
|-----------|---------|
| Session cookie | `gps_session`. HTTP-only, SameSite=Lax. No explicit Max-Age (lives until browser close). |
| Bypass | `BYPASS_AUTH=true` env var. When set, every `/api/*` endpoint accepts every request. |
| Credential storage | `USERNAME` / `PASSWORD` env vars. Default `admin` / `changeme`. |
| Verification | Simple equality. **Constant-time** comparison via Python operator semantics is not guaranteed - prefer a reverse proxy with proper auth in front for any deployment that's exposed beyond a closed lab. |
| Rate limiting | None in the application layer. Use a reverse proxy. |

### Fleet Dashboard

The dashboard has **no authentication**. Anyone who can reach `http://<dashboard-host>/` can see the fleet view. The expected deployment is on a closed internal network, behind a reverse proxy if exposed externally.

There is no API endpoint that mutates dashboard state - the only mutation surface would be the env vars at container start. So the lack of authentication is acceptable for a read-only-broadcast service. If you need to lock down read access, use an auth-aware reverse proxy.

## Client-generation tips

The `openapi.json` endpoint is suitable for any OpenAPI 3.x client generator. Tested combinations:

| Tool | Notes |
|------|-------|
| `openapi-generator-cli` | Works out of the box. Generate clients for Python, Java, Go, TypeScript, etc. |
| Postman | Import the JSON URL directly. |
| Insomnia | Same. |
| `httpie` + manual | Just hit the endpoints directly with `http` / `curl`. |

## API versioning

The simulator exposes `version: "1.0.0"` in the OpenAPI spec. There is no version-suffix on the URLs (no `/api/v1/...`). The expected upgrade path: if/when breaking changes are needed, the version string bumps and the breaking change is documented in the project README.

## What's next

- The live Swagger UI at `http://<host>/api/docs` is the authoritative reference.
- [Environment Variables](env-vars.md) - what configuration the container reads.
- [Security](security.md) - hardening, TLS termination, etc.
- [Multi-Browser Sync](../user-guides/multi-browser-sync.md) - WebSocket behavior in depth.
