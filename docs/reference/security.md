# Security

The simulator and the Fleet Dashboard are designed for **deployment on a trusted internal network**: a flight training facility's lab LAN, a developer's workstation, or a private subnet that isn't routable from the public internet. They are **not hardened** for direct exposure on the public internet without additional protection.

This page documents the security model, the default trust posture, and what to add for production-grade hardening.

## Threat model (default deployment)

| Asset | What's worth protecting |
|-------|-------------------------|
| Simulator web UI | An attacker with UI access can start NMEA emission to connected hardware, change the position, change the EFB target IPs (potentially redirecting GPS data to an unintended iPad). |
| Simulator REST/WS API | Same surface as the UI; an attacker who can hit the API directly can do anything the UI can. |
| NMEA / EFB network ports (UDP/TCP 12000, UDP 49002) | An attacker on the same L2 segment can inject fake position data, displace EFB GPS sources, or DoS the receiver. |
| Fleet Dashboard web UI | Read-only view of every simulator's position and health. Exposes operational topology. |
| Container runtime (`privileged: true` + `/dev` mount) | The simulator container has access to every device on the host. A compromised image could exfiltrate or destroy local hardware. |

The default deployment trusts everyone on the local network. That's appropriate for a closed lab; it's not appropriate for anything else.

## Authentication

### Simulator

| Layer | Default |
|-------|---------|
| Credentials | `USERNAME` / `PASSWORD` env vars. Default `admin` / `changeme`. |
| Verification | Plain equality (`==`). Not constant-time at the application level. Effective constant-time is achievable only with a reverse proxy that handles auth before the simulator does. |
| Session | Cookie `gps_session`. HTTP-only, SameSite=Lax. Server-side store is in-memory; restarts evict all sessions. |
| `BYPASS_AUTH=true` | Skips the entire auth flow. Every `/api/*` endpoint accepts every request. |

!!! danger "Default `admin / changeme` credentials"
    The example compose file ships with default credentials **and** `BYPASS_AUTH=true`. Both are first-run conveniences. Change both before exposing the UI to anyone but yourself.

### Fleet Dashboard

No authentication. The dashboard is **read-only with respect to simulator state** - the only mutation surface is the env vars set at container start. So unauthenticated network reachability gives an attacker visibility into your fleet topology and live positions, but no ability to change anything.

If you need to lock down read access, put an auth-aware reverse proxy in front (nginx with basic-auth or a forward-auth pattern; Authelia; Cloudflare Access; Tailscale ACL).

## Network exposure

| Surface | Default reach | Recommended reach |
|---------|---------------|-------------------|
| Simulator UI (TCP 80) | Anywhere the host is reachable | Same lab LAN as the operator. TLS-terminate at a reverse proxy if exposed externally. |
| Dashboard UI (TCP 80) | Anywhere the host is reachable | Same as above. |
| NMEA in/out (UDP/TCP 12000) | Same LAN | Keep on lab LAN only. Authentication is not part of the protocol. |
| EFB (UDP 49002 outbound) | Same broadcast domain (for ForeFlight) or routable to iPad (for Garmin Pilot) | Same. The simulator doesn't open inbound 49002. |
| Per-sim dashboard listeners (UDP 12001..N) | Same as the dashboard host | Same lab LAN. |

### Putting the UI behind TLS

The container speaks plain HTTP. For TLS, terminate at a reverse proxy and forward to the container's port 80.

Minimal nginx example:

```nginx
server {
    listen 443 ssl http2;
    server_name gps.lab.example.com;

    ssl_certificate     /etc/letsencrypt/live/gps.lab.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gps.lab.example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;       # container's mapped port
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;

        # WebSocket
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600;
    }
}
```

`proxy_read_timeout 3600;` is the default-overriding bit for the WebSocket - nginx will otherwise close idle WebSockets after 60 s.

## Container security

| Aspect | Default | Concern |
|--------|---------|---------|
| `privileged: true` | Set in the example compose file | Container can access every device on the host. Trust the image you run. |
| `volumes: /dev:/dev` | Set | Same concern - bind-mounts the host's `/dev` tree. |
| User in container | Root | Container processes run as root. |
| Image source | Docker Hub `rjsears/gps-emulator:latest` | Pin to a specific tag (not `:latest`) for production reproducibility. |

If you can't tolerate `privileged: true`, an alternative is to grant only the specific device path:

```yaml
devices:
  - /dev/ttyUSB0
```

But this requires the device to exist at compose-up time and is harder to use with hot-plugged peripherals. The trade-off is yours.

## Rate limiting and abuse

The simulator has **no built-in rate limiting**. Anyone with network reach to `/api/auth/login` can brute-force credentials. Put a reverse proxy with rate-limit policy in front for any deployment more exposed than a closed lab.

Example nginx rate limit on the login path:

```nginx
limit_req_zone $binary_remote_addr zone=login_rl:10m rate=5r/m;

location /api/auth/login {
    limit_req zone=login_rl burst=10 nodelay;
    proxy_pass http://127.0.0.1:8080;
    # ...
}
```

## Secret handling

| Secret | Where it lives | Rotation |
|--------|---------------|----------|
| `USERNAME` / `PASSWORD` | Compose `environment:` block | Edit compose, `docker compose up -d`. |
| Session cookies | In-memory on the server | Auto-rotated on container restart. |

There is no `.env`-file path the operator must commit; the compose file is the operator-edited surface. **Don't commit your compose file to a public repo with non-default credentials**. Use a `.env` adjacent to compose:

```yaml
# docker-compose.yml
environment:
  - USERNAME=${USERNAME}
  - PASSWORD=${PASSWORD}
```

```bash
# .env (gitignored)
USERNAME=my-username
PASSWORD=my-very-strong-password
```

## Hardening checklist for production

| Item | Done? |
|------|-------|
| Change default `USERNAME` and `PASSWORD` from `admin` / `changeme` | |
| Set `BYPASS_AUTH=false` | |
| Pin the image to a specific tag (`rjsears/gps-emulator:v1.0.0`) rather than `:latest` | |
| Terminate TLS at a reverse proxy in front of port 80 | |
| Add rate limiting to `/api/auth/login` at the reverse proxy | |
| Add `Strict-Transport-Security` header at the reverse proxy | |
| Restrict the simulator host's inbound firewall to known operator IPs | |
| For the Fleet Dashboard, restrict inbound to the rebroadcasters + operator IPs | |
| Use a separate Wi-Fi / VLAN for EFB iPads, isolated from the rest of the office network | |
| Audit `docker-compose.yml` for accidentally-published secrets | |
| If using a `.env`, confirm it's in `.gitignore` | |

## Vulnerability disclosure

If you find a security issue, please open a private security advisory on the project's GitHub repository rather than a public issue. The maintainer monitors security advisories and will respond.

## What's next

- [Login](../manual/login.md) - the simulator's auth surface.
- [Environment Variables](env-vars.md) - the env-var-driven security controls.
- [API Reference](api-reference.md) - the surface that needs protecting.
