# Troubleshooting

The project-wide symptom -> cause -> fix matrix. Organized by subsystem. For per-page troubleshooting, see the appendix of [User Manual (Simulator)](../manual/appendix.md) or [User Manual (Fleet Dashboard)](../dashboard-manual/appendix.md).

## Container / Docker

| Symptom | Cause | Fix |
|---------|-------|-----|
| `docker compose up -d` fails: `port is already allocated` | Another process is on the mapped host port. | Remap (`"8080:80"` instead of `"80:80"`). |
| Container starts, then immediately exits | The image was pulled but a startup error occurred. | `docker compose logs gps-emulator` - look for the Python traceback at the top. |
| `Failed to open serial port: [Errno 13] Permission denied` at startup | Container lacks `/dev` access. | Add `privileged: true` and `volumes: - /dev:/dev` to compose. |
| Container running, but UI says "Error loading status" | App is up but `/api/status` failed. | Read the error message; usually a transient startup race. Wait a few seconds, refresh. |
| Container running, but UI never loads at all | Wrong port, host firewall, or wrong host IP. | `docker compose ps` to confirm the container is healthy; `curl -v http://<host>:<port>/health` from the operator host to confirm reachability. |
| Image is `linux/amd64` but I'm on arm64 (or vice versa) | Old image build that wasn't multi-arch. | Pull the latest image - it's a multi-arch manifest and will pick the right arch automatically. |

## Authentication

| Symptom | Cause | Fix |
|---------|-------|-----|
| Login screen shows even though `BYPASS_AUTH=true` | The env var didn't make it to the container. | `docker compose exec gps-emulator env | grep BYPASS_AUTH` to confirm. |
| "Invalid credentials" with the right username and password | `USERNAME` or `PASSWORD` env var was empty at startup. | Set both explicitly; restart the container. |
| Logged in but immediately bumped back to Login | Cookie wasn't set (often a reverse-proxy stripping cookies, or `SameSite` issues with cross-origin). | Use the same hostname for the UI and the API. Disable any reverse-proxy cookie manipulation. |
| Every request returns 401 from a script | The cookie jar isn't being carried across requests. | `curl -c cookies.txt` for login, `curl -b cookies.txt` for subsequent calls. |

## NMEA / serial output

| Symptom | Cause | Fix |
|---------|-------|-----|
| Output Viewer is silent, Start succeeded | Mode requires USB but no USB device is selected, and the SPA didn't reject Start. (Should be impossible; if it happens, file a bug.) | Stop, pick a device, Start. |
| Device dropdown empty | Host's `/dev` doesn't expose the device, or the container's bind mount didn't capture it. | `ls /dev/tty*` on the host; `docker compose exec gps-emulator ls /dev/tty*` inside. They should match. |
| Downstream consumer gets garbled NMEA | Baud rate mismatch. | Match the consumer's expected baud. |
| Consumer gets some sentences but drops others | Buffer overflow at low baud. | Disable optional NMEA sentences; reduce to `GPGGA` + `GPRMC`. |
| Output Viewer shows correct NMEA but consumer is silent | Wire-side issue: TX/RX swap, cable break, ground missing. | Try a known-good cable; verify with a loopback test. |
| Bad Elf is plugged in but never appears | `privileged: true` not set, or `/dev:/dev` bind missing. | Both required. |

## Network / sender / receiver

| Symptom | Cause | Fix |
|---------|-------|-----|
| Sender Output Viewer scrolling, Receiver Output Viewer empty | Packets not arriving at Receiver. | `tcpdump -i any 'udp port 12000'` on the Receiver host. If empty, network blocked. |
| Packets arriving at Receiver host but Output Viewer still empty | Port collision or Receiver not actually started. | `lsof -iUDP:12000` on Receiver host. |
| TCP Sender start fails: "Connection refused" | Receiver isn't running, or listening on a different port. | Start Receiver first; verify the target. |
| Position values look wrong in Receiver | Source is sending CYGNUS / JSON with wrong field names. | Validate the payload with a manual `nc -u` test. |
| Position values flicker | Source is bouncing between values. The Receiver smooths via transitions but extreme flicker can show through. | Stabilize the source. |
| "Bad UDP checksum" warnings in `tcpdump` | TX checksum offload on the sending NIC. | See [TX Checksum Offload Fix](../user-guides/tx-checksum-offload.md). |

## EFB (ForeFlight / Garmin Pilot)

| Symptom | Cause | Fix |
|---------|-------|-----|
| iPad never sees the simulator | AP isolation, different VLANs, host firewall. | Same SSID + no AP isolation; or use unicast targeting. |
| ForeFlight sees it, Garmin Pilot doesn't | Garmin Pilot doesn't accept broadcast. | Add the iPad's IP to **EFB target IPs**. |
| Garmin Pilot sees a brief connection, then loses it | iPad's DHCP lease rotated. | DHCP reservation, or use an IP range. |
| Two simulators showing up, ForeFlight picks the wrong one | Both broadcasting with different sim names. | Pick one or differentiate via app settings. |
| Simulator name shows blank or "LOFT GPS" | `AUTO_START_EFB_SIM_NAME` unset (or UI field empty). | Set it. |
| Wrong altitude on iPad | Simulator's altitude is correct; iPad's app is interpreting units oddly. | Compare against `Status Display` - if simulator's value is right, the issue is iPad-side. |

## Fleet Dashboard

| Symptom | Cause | Fix |
|---------|-------|-----|
| All cards stay gray | No rebroadcaster is sending, **or** port mismatches between dashboard and rebroadcasters. | Cross-check `SIM_N_PORT` vs `AUTO_START_UDP_RETRANSMIT_PORT`. |
| Some cards online, some gray | Specific rebroadcasters aren't running or aren't pointing at the dashboard. | Check each rebroadcaster's container status and env vars. |
| Card shows wrong simulator's data | Two rebroadcasters using the same dashboard port. | Each rebroadcaster must use a unique `AUTO_START_UDP_RETRANSMIT_PORT`. |
| Health Chain shows Simulator segment red but the sim is on | `SIMULATOR_IP` is wrong, or ICMP is filtered. | Set the right IP; allow ICMP echo. |
| Health Chain says "Restart GPSConnect application on the simulator" with no system name | `SIM_N_GPS_SYSTEM` unset for that card. | Set it. |
| Connection badge stays red | Dashboard is down, or browser->dashboard network broken. | `docker compose ps` on dashboard host. |

## MkDocs / docs site

| Symptom | Cause | Fix |
|---------|-------|-----|
| `mkdocs build --strict` fails with `link not found` | A `[text](path.md)` link points at a file that doesn't exist. | Run the build and grep for the broken link target. Fix the path. |
| Page renders without admonitions | GitHub-style `> [!WARNING]` syntax used instead of Material's `!!! warning`. | Convert to `!!! warning "Title"` form. |
| Page renders without a sidebar entry | File is in `docs/` but not in `mkdocs.yml`'s `nav:`. | Add a nav entry. |
| `mkdocs serve` works but the GitHub Pages site is stale | The publish step (manual or via GitHub Action) hasn't been run since the last edit. | Re-run the publish step. |

## Performance

| Symptom | Cause | Fix |
|---------|-------|-----|
| Container CPU pinned at 100% | Something is wrong. The simulator runs <5% even on a Raspberry Pi 4. | Check logs for a busy loop or infinite retry. |
| Output Viewer scrolling at less than 1 Hz | Browser tab is backgrounded; browsers throttle inactive tabs. | Bring the tab to the foreground. |
| WebSocket reconnect every minute on a long-running connection | Reverse proxy is closing idle WebSockets. | `proxy_read_timeout 3600;` (nginx) or equivalent. |

## When all else fails

| Step | Why |
|------|-----|
| `docker compose logs gps-emulator --tail 200` | See what the container itself is saying. The most useful thing in the toolbox. |
| `docker compose logs fleet-dashboard --tail 200` | Same for the dashboard. |
| `tcpdump -i any 'udp port <port>' -nn -X` | Confirm packets are or aren't on the wire. Independent of the application's reporting. |
| Reproduce on a minimal setup (one simulator, one container, default compose) | Eliminates configuration-drift variables. If the minimal setup works, your real setup has a configuration issue. |
| Re-pull `:latest` | Eliminates image-version-drift variables. |
| Restart everything in a known order: dashboard first, then each rebroadcaster | Eliminates race-condition variables. |

## What's next

- [Health Chain](../dashboard-manual/health-chain.md) - the dashboard-side diagnostic view.
- [TX Checksum Offload Fix](../user-guides/tx-checksum-offload.md) - the most surprisingly-common gotcha.
- [Security](security.md) - hardening checklist (separate from troubleshooting but worth a look).
