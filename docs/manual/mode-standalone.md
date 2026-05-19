# Stand-Alone Mode

Stand-Alone is the simplest of the four operating modes. The simulator generates NMEA position data **entirely from local input** - no network ingest, no upstream source - and emits it to one or both of two outputs: a USB-serial device and / or one or more EFB apps over XGPS.

This is the mode you reach for when:

- You have a single station (one host, maybe one iPad).
- You want full manual control of position, altitude, speed, and heading from the web UI.
- You don't need another simulator or external script feeding position in.

!!! info "Stand-Alone vs Sender"
    Stand-Alone and [Sender Mode](mode-sender.md) both *generate* NMEA from manual input. The only difference: Sender additionally publishes the position to one or more network receivers. If you're not going to have a receiver downstream, Stand-Alone is the cleaner choice.

<!-- SCREENSHOT-PENDING: mode-standalone-01-overview.png - overview of the Output Settings panel with both blocks visible. -->

## When to use Stand-Alone

| Use case | Why Stand-Alone fits |
|----------|----------------------|
| Driving a single iPad with ForeFlight or Garmin Pilot | No network protocol needed; XGPS over UDP 49002 is enough. |
| Driving a single Bad Elf SBK-2500 over USB | The simulator generates NMEA-0183, the cable carries it, the avionics consume it. |
| Driving both a Bad Elf **and** an iPad from the same station | Both outputs run from the same NMEA engine. Enable both blocks. |
| Classroom demos and single-station tutorials | Operator sees the controls; the EFB or avionics see real position. |

## Reaching Stand-Alone mode

| Step | Action |
|------|--------|
| 1 | Log in if `BYPASS_AUTH=false`. |
| 2 | In the mode selector at the top of the dashboard, choose **Stand Alone**. |
| 3 | The **Output Settings** panel appears with two blocks - USB and EFB. |

Stand-Alone is *not* selectable while the emulator is running. Press **Stop** first if you need to switch modes.

## Output Settings panel

At least one output must be enabled before **Start** activates.

### USB Serial Output

| Control | Default | Valid values | What it does |
|---------|---------|--------------|--------------|
| **USB Serial Output** toggle | off | on / off | Enables NMEA-0183 emission to a USB-serial device. |
| **Device** | (none) | Any path matching the supported serial-device patterns | The serial device to open. The **Refresh** button rescans the host's device list. |
| **Baud Rate** | `115200` | 1200 - 115200 | Symbol rate on the serial line. Must match the receiving device's expectation. |

Wire format is fixed at **8N1**. See [Serial Output](serial-output.md) for per-device guidance and [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md) for the Bad Elf SBK-2500 setup end to end.

### EFB Output (UDP 49002 - ForeFlight and Garmin Pilot)

| Control | Default | Valid values | What it does |
|---------|---------|--------------|--------------|
| **EFB Output (Port 49002)** master toggle | off | on / off | Enables the EFB block. With this off, neither broadcast nor unicast EFB output is sent. |
| **Broadcast** | off | on / off | Sends XGPS frames to the local broadcast address. ForeFlight auto-discovers the source this way. |
| **Garmin Pilot / ForeFlight (IP Address)** | off | on / off | Sends XGPS frames to one or more unicast targets. Required for Garmin Pilot. |
| **EFB target IPs** | (empty) | Comma-separated list. See [IP Range Parsing](../user-guides/ip-range-parsing.md). | Individual IPs (`10.200.50.5`), ranges (`10.200.50.10-10.200.50.20`), or mixed. |
| **Simulator Name** | (empty) | Free text, typically aircraft type (`CL350`, `Ultra`) | The string that appears in the EFB's GPS-source list. Required when EFB output is enabled. |

#### When to use Broadcast vs IP targeting

| Situation | Broadcast | IP targeting |
|-----------|-----------|--------------|
| ForeFlight, same Wi-Fi, no AP isolation | Yes | Optional |
| Garmin Pilot, same Wi-Fi | **No** (Garmin Pilot doesn't accept broadcast) | **Yes** |
| Multiple iPads with mixed apps | Both (broadcast covers ForeFlight, IPs cover Garmin Pilot) | Both |
| iPads on a different VLAN with a router between | Broadcast won't cross routers | **Yes** |

For a complete EFB walk-through including iPad-side configuration, see [Connecting ForeFlight](../user-guides/connecting-foreflight.md) and [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md).

## Position, altitude, speed, heading

Stand-Alone mode is driven by the **Navigation Controls** panel - the one with the airport picker, the altitude / airspeed sliders, and the compass dial. It works identically across all four modes, so its detail lives on its own page: [Navigation Controls](navigation-controls.md).

| Input | What it sets |
|-------|--------------|
| **Airport picker** | Snaps lat / lon to a known airport from the built-in database (4,003 entries). See [Airport Lookup](airport-lookup.md). |
| **Altitude slider** | Target altitude in feet MSL. The engine ramps to it at `ALTITUDE_RATE_FT_PER_2SEC` (default 1000 ft / 2 s). |
| **Airspeed slider** | Target airspeed in knots. Ramps at `AIRSPEED_RATE_KTS_PER_SEC` (default 30 kts/s). |
| **Heading dial** | Target heading 1-360 degrees. Ramps at `HEADING_RATE_DEG_PER_SEC` (default 3 °/s). |

The "ramp" behavior is what makes Stand-Alone output look like a real aircraft instead of a teleporting cursor. See [Navigation Controls](navigation-controls.md) for the underlying math and the per-rate env vars.

## NMEA sentence selection

Stand-Alone honors the sentence selections from the **NMEA** panel. `GPGGA` and `GPRMC` are always emitted; everything else is opt-in. See [NMEA Sentences](nmea-sentences.md) for the per-sentence detail.

## Starting and stopping

| Action | What happens |
|--------|--------------|
| **Start** | The NMEA engine arms with current sliders / airport. The serial port opens (if USB enabled). The EFB sender opens its socket. NMEA output begins at 1 Hz. |
| **Stop** | All outputs close. The engine releases. Slider / heading values are preserved in memory for the next start. |
| **Adjust a slider while running** | The new value becomes the *target* the engine ramps toward. The transition rates govern how fast it gets there. |
| **Container restart** | All in-memory state is discarded. If `AUTO_START_MODE=standalone` is set, the simulator re-arms on the next boot with the env-var defaults. |

## Persistent state

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| Mode (set to standalone at boot) | Mode selector | `AUTO_START_MODE=standalone` | Only if env var set |
| Default position | Airport picker / lat-lon | `DEFAULT_LAT`, `DEFAULT_LON` | Yes (env var, used at boot) |
| Default altitude / airspeed / heading | Sliders / dial | `DEFAULT_ALT_FT`, `DEFAULT_AIRSPEED_KTS`, `DEFAULT_HEADING` | Yes (env var, used at boot) |
| Transition rates | (no UI control) | `ALTITUDE_RATE_FT_PER_2SEC`, `AIRSPEED_RATE_KTS_PER_SEC`, `HEADING_RATE_DEG_PER_SEC` | Yes (env var, applied always) |
| USB enabled | Output Settings | `AUTO_START_USB_ENABLED` | Only if env var set |
| USB device | Serial picker | `AUTO_START_USB_DEVICE` | Only if env var set |
| Serial baud | Serial picker | `SERIAL_BAUDRATE` | Yes (env var, host-wide default) |
| EFB enabled | Output Settings | `AUTO_START_EFB_ENABLED` | Only if env var set |
| EFB broadcast | Output Settings | `AUTO_START_EFB_BROADCAST` | Only if env var set |
| EFB IP targets | Output Settings | `AUTO_START_EFB_TARGET_IPS` | Only if env var set |
| EFB simulator name | Output Settings | `AUTO_START_EFB_SIM_NAME` | Only if env var set |

See [Environment Variables](../reference/env-vars.md) for the authoritative reference.

## Worked scenarios

### Scenario 1 - Single iPad with ForeFlight, no USB

A pilot at their desk wants ForeFlight on their iPad to think the aircraft is at KCRQ, taking off west at 450 knots, climbing to 45,000 feet.

| Setting | Value |
|---------|-------|
| Mode | Stand Alone |
| USB output | off |
| EFB output | on |
| Broadcast | on |
| IP targeting | off (broadcast is enough for ForeFlight on the same Wi-Fi) |
| Simulator name | `CL350` |
| Airport | KCRQ |
| Altitude | 45000 ft (ramps from 0) |
| Airspeed | 450 kts (ramps from 0) |
| Heading | 270 |

Pressing **Start** begins XGPS broadcast immediately. ForeFlight picks `CL350` from its GPS-source list within ~5 s. The altitude rolls from 0 to 45,000 over ~90 s.

### Scenario 2 - Bad Elf SBK-2500 driving cockpit avionics

A maintenance bench is testing a panel that consumes serial NMEA-0183 at 9600 baud (a common legacy rate). The Bad Elf is wired host-USB to RS-232 into the panel's GPS-in port.

| Setting | Value |
|---------|-------|
| Mode | Stand Alone |
| USB output | on |
| Device | `/dev/ttyUSB0` |
| Baud rate | 9600 |
| EFB output | off |
| Airport | KORD |
| Altitude | 0 ft |
| Airspeed | 0 kts |
| Heading | 360 |

The panel sees a stationary aircraft at KORD. Adjust heading on the compass dial to confirm the panel's HSI follows.

### Scenario 3 - Both outputs at once

The same maintenance bench, but the technician also wants a Garmin Pilot iPad to corroborate what the avionics is seeing.

| Setting | Value |
|---------|-------|
| Mode | Stand Alone |
| USB output | on, `/dev/ttyUSB0` at 9600 |
| EFB output | on |
| Broadcast | off |
| IP targeting | on, target `10.200.40.198` (the iPad) |
| Simulator name | `BENCH` |

Both outputs run from the same NMEA engine, so whatever the iPad sees is what the panel sees.

## What's next

- [Sender Mode](mode-sender.md) - the same generator with an additional network publish step.
- [Navigation Controls](navigation-controls.md) - reference for the airport / altitude / airspeed / heading inputs.
- [NMEA Sentences](nmea-sentences.md) - which sentences to enable for which consumer.
- [Connecting ForeFlight](../user-guides/connecting-foreflight.md) and [Connecting Garmin Pilot](../user-guides/connecting-garmin-pilot.md) - end-to-end EFB walkthroughs.
- [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md) - cable, baud, and per-device specifics.
