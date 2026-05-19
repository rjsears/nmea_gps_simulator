# Fleet Monitoring

The Fleet Dashboard is most useful when several rebroadcasters report to it. This guide is the end-to-end deployment walkthrough: dashboard container + per-rebroadcaster compose, matching env vars across both sides, health-chain coverage, what to verify and where.

## The wiring at a glance

```
+---------- Rebroadcaster A -----------+               +---------- Rebroadcaster B -----------+
|  AUTO_START_MODE=rebroadcaster       |               |  AUTO_START_MODE=rebroadcaster       |
|  AUTO_START_UDP_RETRANSMIT=true      |               |  AUTO_START_UDP_RETRANSMIT=true      |
|  AUTO_START_UDP_RETRANSMIT_IP=DASH   |               |  AUTO_START_UDP_RETRANSMIT_IP=DASH   |
|  AUTO_START_UDP_RETRANSMIT_PORT=12001|               |  AUTO_START_UDP_RETRANSMIT_PORT=12002|
|  SIMULATOR_IP=SimA-host              |               |  SIMULATOR_IP=SimB-host              |
+-------------+------------------------+               +-------------+------------------------+
              |                                                      |
              | UDP :12001 (position + heartbeat)                    | UDP :12002 (position + heartbeat)
              |                                                      |
              v                                                      v
              +--- Fleet Dashboard --------------------+
              |  SIM_1_NAME=A                          |
              |  SIM_1_PORT=12001                      |
              |  SIM_1_GPS_SYSTEM=Avionics             |
              |  SIM_2_NAME=B                          |
              |  SIM_2_PORT=12002                      |
              |  SIM_2_GPS_SYSTEM=Avionics 2           |
              +----------------------------------------+
```

Three things to keep aligned across the pair:

| Dashboard side | Rebroadcaster side |
|----------------|--------------------|
| `SIM_N_PORT` | `AUTO_START_UDP_RETRANSMIT_PORT` |
| The dashboard's host IP | `AUTO_START_UDP_RETRANSMIT_IP` |
| `SIM_N_GPS_SYSTEM` | (no rebroadcaster side - this is dashboard-only) |
| (none, dashboard doesn't ping) | `SIMULATOR_IP` (for the rebroadcaster's own ping to the flight sim host) |

## Step 1 - Deploy the dashboard

A standalone compose file for the dashboard, typically on a host different from any of the simulators:

```yaml
services:
  dashboard:
    image: rjsears/fleet-dashboard:latest
    pull_policy: always
    container_name: fleet-dashboard
    restart: unless-stopped
    network_mode: host
    environment:
      - HOST=0.0.0.0
      - PORT=80

      - SIM_1_NAME=CJ3
      - SIM_1_PORT=12001
      - SIM_1_GPS_SYSTEM=Avionics

      - SIM_2_NAME=Ultra
      - SIM_2_PORT=12002
      - SIM_2_GPS_SYSTEM=Avionics 2

      - SIM_3_NAME=CL350
      - SIM_3_PORT=12003
      - SIM_3_GPS_SYSTEM=rehost
```

`docker compose up -d`. Open `http://<dashboard-host>/` - you see three cards, all gray. That's expected: no rebroadcaster is reporting yet.

## Step 2 - Configure each rebroadcaster

For each simulator host, edit its `docker-compose.yml`:

```yaml
services:
  gps-emulator:
    image: rjsears/gps-emulator:latest
    pull_policy: always
    container_name: nmea-gps-emulator
    restart: unless-stopped
    privileged: true
    network_mode: host
    volumes:
      - /dev:/dev
    environment:
      - BYPASS_AUTH=true
      - TZ=America/Los_Angeles

      - AUTO_START_MODE=rebroadcaster
      - AUTO_START_LISTEN_PORT=12000
      - AUTO_START_PROTOCOL=udp

      # EFB (drive an iPad on this station)
      - AUTO_START_EFB_ENABLED=true
      - AUTO_START_EFB_BROADCAST=false
      - AUTO_START_EFB_TARGET_IPS=10.200.40.198
      - AUTO_START_EFB_SIM_NAME=CJ3

      # USB (optional)
      - AUTO_START_USB_ENABLED=false

      # UDP retransmit to dashboard
      - AUTO_START_UDP_RETRANSMIT=true
      - AUTO_START_UDP_RETRANSMIT_IP=10.200.40.3       # dashboard host IP
      - AUTO_START_UDP_RETRANSMIT_PORT=12001           # matches SIM_1_PORT on dashboard

      # Health: ping the flight simulator host
      - SIMULATOR_IP=10.200.50.11
```

`docker compose up -d`. The CJ3 card on the dashboard turns green within a few seconds.

Repeat for the Ultra rebroadcaster (port 12002, sim name `Ultra`, simulator IP `10.200.50.12`) and the CL350 (port 12003, sim name `CL350`, simulator IP `10.200.50.16`).

## Step 3 - Verify on the dashboard

| State | What to confirm |
|-------|-----------------|
| Position view | All configured cards green (or, for those that aren't started yet, gray). Each green card shows lat/lon/altitude/airspeed/heading and the closest airport. |
| Health view (toggle on) | Each card shows the four-node chain. With everything healthy, all four nodes are green and the footer reads "All systems operational". |
| Click an online card | New tab opens to Google Maps centered on the aircraft's current position. |
| Configuration | The dashboard's `SIM_N_NAME` becomes the card title. `SIM_N_GPS_SYSTEM` only appears when the GPS segment of the health chain goes red. |

## When a card stays gray

Walk down this list:

| Check | Command |
|-------|---------|
| Is the rebroadcaster's container up? | `docker compose ps` on the rebroadcaster's host. |
| Is `AUTO_START_MODE=rebroadcaster` set? | `docker compose exec gps-emulator env | grep AUTO_START` |
| Is UDP retransmit on with a real target IP? | Same. Confirm `AUTO_START_UDP_RETRANSMIT=true` and `AUTO_START_UDP_RETRANSMIT_IP=<dashboard-host>`. |
| Does the rebroadcaster's port match the dashboard's `SIM_N_PORT`? | `grep AUTO_START_UDP_RETRANSMIT_PORT` on the rebroadcaster; `grep SIM_.*_PORT` on the dashboard. |
| Are packets actually arriving at the dashboard host? | `tcpdump -i any 'udp port 12001'` on the dashboard host. You should see two packet types per second: position + heartbeat. |
| If `tcpdump` sees packets but the card is still gray | The dashboard listener thread isn't binding the port - probably because of a port collision on the dashboard host. Check `lsof -iUDP:12001` and ensure nothing else is on the port. |

The combination of "rebroadcaster Output Viewer scrolling" + "`tcpdump` on dashboard shows packets" + "card still gray" almost always means the port doesn't match between the two sides.

## When the health chain shows red

| Red segment | Cause | Fix |
|-------------|-------|-----|
| Dashboard -> Emulator | No heartbeat in 3 s | Rebroadcaster container down, or UDP retransmit IP wrong. |
| Emulator -> Simulator | `sim_reachable: false` in the heartbeat | `SIMULATOR_IP` unreachable or unset on the rebroadcaster. |
| Simulator -> GPS Data | `receiving_udp: false` in heartbeat **and** no position in 5 s | Upstream Sender / flight sim's GPSConnect-equivalent isn't running. The footer message names the system via `SIM_N_GPS_SYSTEM`. |

See [Health Chain](../dashboard-manual/health-chain.md) for the full state machine.

## When the data is wrong

| Symptom | Cause |
|---------|-------|
| Card shows the wrong aircraft (CJ3 data appears on the Ultra card) | Two rebroadcasters using the same `AUTO_START_UDP_RETRANSMIT_PORT`. The dashboard accepts whatever arrives last on that port. **Each rebroadcaster must use a unique port.** |
| Altitude is wildly wrong | Upstream sender's position payload is bad. Drop back to the simulator's Status Display to see what the source thinks the value is. |
| Heading flickers | Could be a noisy upstream source. The receiver smooths via `transitions.py`, so this is rare. |
| Closest airport is on the wrong continent | Lat or lon sign is flipped on the upstream source. |

## Performance characteristics

| Metric | Value |
|--------|-------|
| Packets per simulator per second | 2 (position + heartbeat) |
| Bandwidth per simulator | ~300 bytes/s |
| 20 simulators total | ~6 kB/s into the dashboard. Trivial. |
| Browsers connected to dashboard | Each gets the full `fleet_state` over WebSocket every second. ~3 kB/s per browser. |
| Dashboard CPU | <5% on a Raspberry Pi 4 with 20 simulators. |

The dashboard is intentionally cheap. It scales well past the documented max of 20 simulators - the only enforced limit is the `for i in range(1, 20)` loop in `dashboard/backend/config.py` (raise the constant if you genuinely need more).

## Persistent state on the dashboard

The dashboard has **no persistent state**. Every restart starts every card's packet count at 0. Configuration (names, ports, GPS system labels) lives entirely in `docker-compose.yml`. To change anything, edit and `docker compose up -d`.

## What's next

- [Configuration (Fleet Dashboard)](../dashboard-manual/configuration.md) - dashboard env vars in detail.
- [Health Chain](../dashboard-manual/health-chain.md) - what each red segment means.
- [Rebroadcaster Mode](../manual/mode-rebroadcaster.md) - rebroadcaster reference on the simulator side.
- [TX Checksum Offload Fix](tx-checksum-offload.md) - when `tcpdump` shows bad UDP checksums.
