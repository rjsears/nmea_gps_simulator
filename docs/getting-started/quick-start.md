# Quick Start

The goal of this page is to get a working simulator on your host in under five minutes. The path here keeps Stand-Alone mode + auth bypass on, so you can see the web UI working before tightening anything down.

If you're planning a real deployment (production EFB driver, multi-station fleet, hardware integration), this page is still the right starting point — but go through [Architecture](architecture.md) and [Hardware Requirements](hardware.md) before you commit any of the values below to your actual `docker-compose.yml`.

## Prerequisites

| Need | Confirmed by |
|------|--------------|
| Docker Engine 20.10+ or Docker Desktop 4.x+ | `docker --version` |
| Docker Compose plugin (`docker compose ...`) | `docker compose version` |
| Outbound network to Docker Hub | `docker pull hello-world` |
| Port 80 free on the host (or you'll remap it below) | `ss -tlnp` on Linux, `lsof -iTCP:80 -sTCP:LISTEN` on macOS |

USB-serial peripherals and EFB iPads are **not** required for the steps below. Add them later once the container is healthy.

## 1. Drop a `docker-compose.yml` on the host

Create a directory for the deployment and put this file in it as `docker-compose.yml`:

```yaml
services:
  gps-emulator:
    image: rjsears/gps-emulator:latest
    pull_policy: always
    container_name: nmea-gps-emulator
    restart: unless-stopped
    privileged: true                # Required for USB device access

    ports:
      - "80:80"                     # Web UI
      - "12000:12000/udp"           # NMEA sender/receiver
      - "12000:12000/tcp"
      - "49002:49002/udp"           # ForeFlight / Garmin Pilot (XGPS)

    volumes:
      - /dev:/dev                   # USB device access

    environment:
      # Authentication
      - USERNAME=admin
      - PASSWORD=changeme
      - BYPASS_AUTH=true            # Skip the login screen for first run

      # Transition rates
      - ALTITUDE_RATE_FT_PER_2SEC=1000
      - AIRSPEED_RATE_KTS_PER_SEC=30
      - HEADING_RATE_DEG_PER_SEC=3

      # Default position (KCRQ - McClellan-Palomar)
      - DEFAULT_LAT=33.1283
      - DEFAULT_LON=-117.2803
      - DEFAULT_ALT_FT=0
      - DEFAULT_AIRSPEED_KTS=0
      - DEFAULT_HEADING=360

      # Serial
      - SERIAL_BAUDRATE=115200

      # Timezone
      - TZ=America/Los_Angeles
```

!!! warning "`BYPASS_AUTH=true` is a first-run convenience"
    The example above leaves authentication off so you can see the UI immediately. Set `BYPASS_AUTH=false` and change `USERNAME` / `PASSWORD` before exposing the UI to anyone but yourself.

## 2. Bring the container up

From the directory containing `docker-compose.yml`:

```bash
docker compose up -d
```

The first run pulls the image (~250 MB) and starts the container. Subsequent runs are instant.

Confirm it's healthy:

```bash
docker compose ps
docker compose logs -f gps-emulator
```

You should see Uvicorn announce that the app is listening on `0.0.0.0:80`. If you set `AUTO_START_MODE` (this guide does not), you'll also see a startup log line for that.

## 3. Open the web UI

In a browser on the same network as the host, navigate to:

```
http://<host>/
```

`<host>` is the IP or hostname of the machine running the container. On the same machine, `http://localhost/` works.

You should land on the simulator dashboard with no login challenge (because `BYPASS_AUTH=true`).

## 4. Drive a position

To verify the simulator is generating NMEA:

1. Select **Stand-Alone** mode in the mode picker.
2. Pick an airport with the airport search box, or accept the default (KCRQ).
3. Set altitude, airspeed, and heading using the sliders or the compass dial.
4. Press **Start**.
5. The **Output Viewer** panel scrolls live NMEA-0183 sentences (`$GPGGA`, `$GPRMC`, plus any optional sentences you enabled).

That's the smallest end-to-end loop — you're now generating realistic, smoothly-changing position data.

## 5. Send the data somewhere

The simulator is most useful when it's driving something downstream. Pick whichever applies:

| Destination | What to add next | Reference |
|-------------|------------------|-----------|
| **iPad running ForeFlight** | Enable EFB output, leave broadcast on. | [Connecting ForeFlight](../user-guides/connecting-foreflight.md) |
| **iPad running Garmin Pilot** | Enable EFB output, set target IP(s) to the iPad's IP. | [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md) |
| **Bad Elf SBK-2500 or other USB-serial device** | Plug in the device, select it in the Serial picker, enable USB output. | [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md) |
| **Another simulator instance** | Switch one side to Sender, the other to Receiver. | [Sender/Receiver Pair](../user-guides/sender-receiver-pair.md) |
| **Fleet Dashboard** | Switch to Rebroadcaster, enable UDP retransmit to the dashboard's IP. | [Fleet Monitoring](../user-guides/fleet-monitoring.md) |

## 6. (Optional) Run the Fleet Dashboard

If you want the multi-simulator view, on the same host or a different one, drop a second compose file:

```yaml
services:
  dashboard:
    image: rjsears/fleet-dashboard:latest
    pull_policy: always
    container_name: fleet-dashboard
    restart: unless-stopped
    network_mode: host             # Listens on N UDP ports - host networking is simplest
    environment:
      - HOST=0.0.0.0
      - PORT=80

      # Simulator configuration: name + port (+ optional GPS system label)
      - SIM_1_NAME=CJ3
      - SIM_1_PORT=12001
      - SIM_1_GPS_SYSTEM=Avionics

      - SIM_2_NAME=Ultra
      - SIM_2_PORT=12002
      - SIM_2_GPS_SYSTEM=Avionics 2
```

Bring it up:

```bash
docker compose up -d
```

Then on each simulator that should report to it, set:

```yaml
environment:
  - AUTO_START_MODE=rebroadcaster
  - AUTO_START_UDP_RETRANSMIT=true
  - AUTO_START_UDP_RETRANSMIT_IP=<dashboard-host>
  - AUTO_START_UDP_RETRANSMIT_PORT=12001       # Match the SIM_1_PORT above
  - SIMULATOR_IP=<flight-simulator-ip>         # Optional - enables ping health check
```

Open `http://<dashboard-host>/` and the card for that simulator will turn green within a couple of seconds.

## Common first-run issues

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `docker compose up -d` fails with "port is already allocated" | Something else is on port 80 (Apache, a reverse proxy, etc.) | Remap to `"8080:80"` and use `http://<host>:8080/` instead. |
| Web UI loads but the **Start** button stays disabled | A required field (mode, target IPs in Sender, USB device in USB-output mode) is unset | The button's tooltip explains what's missing. Fill it in. |
| Output Viewer is empty even after pressing Start | The selected output is disabled (no USB device plugged in, EFB broadcast off without target IPs) | Pick a valid output. Pure "started, no outputs" runs silently by design. |
| `docker compose logs` shows "permission denied" on `/dev/...` | Container ran without `privileged: true` or the `/dev` mount | Add both to the compose file and recreate the container. |
| ForeFlight on the iPad never sees the simulator | iPad and host are not on the same L2 segment, or AP isolation is on | Put them on the same Wi-Fi SSID, with AP isolation disabled. See [Connecting ForeFlight](../user-guides/connecting-foreflight.md). |

For anything not covered here, see the [Troubleshooting](../reference/troubleshooting.md) matrix.

## What's next

- **Operating the UI day-to-day:** start at [User Manual — Welcome](../manual/welcome.md).
- **Auto-starting into a specific mode at boot:** see [Auto-Start](../user-guides/auto-start.md). You'll never have to click anything in the UI after a reboot.
- **Tightening security before production use:** see [Security](../reference/security.md).
- **Building the API into your own software:** see [API Reference](../reference/api-reference.md).
