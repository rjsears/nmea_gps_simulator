# NMEA Sentences

The **NMEA Sentences** panel controls which NMEA-0183 sentences the simulator emits. Two sentences (`GPGGA` and `GPRMC`) are always on; the other six are operator-toggleable.

This page documents the panel itself. For the wire-level details of each sentence (field order, formatting, the checksum algorithm), see [NMEA Sentence Catalog](../user-guides/nmea-sentence-catalog.md). For the underlying protocol, see [NMEA Protocol](../reference/nmea-protocol.md).

<!-- SCREENSHOT-PENDING: nmea-sentences-01-overview.png - panel with default selections. -->

## The panel

| Sentence | Default | Toggleable | What it carries |
|----------|---------|-----------|-----------------|
| **`GPGGA`** | on | **no** (always on) | Position, altitude, fix quality, satellite count, HDOP. The single most-consumed NMEA sentence. |
| **`GPRMC`** | on | **no** (always on) | Recommended-minimum: position, speed over ground, course over ground, magnetic variation, date/time. |
| **`GPGLL`** | off | yes | Geographic position (lat/lon) plus UTC and status. Subset of `GPGGA`. |
| **`GPVTG`** | off | yes | Track made good and ground speed in true and magnetic. Useful for HSI driving. |
| **`GPGSA`** | off | yes | DOP and active satellites. Pads out the realism for consumers that watch fix quality. |
| **`GPGSV`** | off | yes | Satellites in view - SNR, elevation, azimuth per satellite. Drives sat-view panels. |
| **`GPZDA`** | off | yes | Time and date in UTC. Useful when the consumer wants the clock from NMEA rather than from its own RTC. |
| **`GPHDT`** | off | yes | True heading. Some autopilots and HSIs look for this specifically. |

Each row has a checkbox; toggling it sends a `POST /api/config/nmea` request and updates the engine's enabled-sentence set immediately (when the emulator isn't running) or queues the change for the next Start (when it is).

!!! info "Why `GPGGA` and `GPRMC` are pinned on"
    These two are what every NMEA-aware consumer expects. Many devices simply won't recognize a "GPS" without them. The simulator enforces the pin server-side too - even if a request comes in trying to turn them off, the engine ignores it.

## What changes when you flip a sentence

| Change | Effect |
|--------|--------|
| Toggle a sentence **while the emulator is stopped** | The next **Start** uses the new set. |
| Toggle a sentence **while the emulator is running** | The toggle is ignored at the UI layer - the panel is disabled. Press Stop, toggle, Start. |
| Toggle a sentence **in Receiver mode** | The panel is also disabled. The Receiver inherits its own sentence selection at Start. |

The panel's disabled state matches both conditions, so you'll see the panel grayed out either when running or when in Receiver mode.

## When to enable optional sentences

Pick what the **downstream consumer** wants - not what looks impressive. NMEA over RS-232 is bandwidth-bound, and at low baud rates a consumer's serial buffer can overflow if you push more sentences per second than it can drain.

| Consumer | Likely needed |
|----------|---------------|
| ForeFlight / Garmin Pilot via XGPS | None of the optional ones - XGPS is its own one-line-per-second format, not NMEA. Your NMEA selection only matters for USB and TCP/UDP NMEA outputs. |
| Bad Elf SBK-2500 with downstream avionics | `GPGGA` + `GPRMC` is usually enough. Some panels also want `GPVTG` for ground track. |
| HSI / autopilot pickling true heading | `GPHDT` (and confirm the consumer is set to "true" not "magnetic"). |
| Software that draws a satellite-view widget | `GPGSV` and `GPGSA`. |
| Software that wants UTC from NMEA | `GPZDA`. |
| Generic GPS-logging software | `GPGGA` + `GPRMC` + `GPGLL` covers nearly every parser. |

!!! tip "Add sentences one at a time when troubleshooting"
    If a downstream device starts misbehaving after you turn on more sentences, the issue is almost always buffer overflow at low baud rates. Drop back to `GPGGA` + `GPRMC` and add one sentence per restart until you reproduce the failure - the last-added sentence is the culprit.

## Output cadence

Every enabled sentence is emitted once per second, in this fixed order:

1. `GPGGA`
2. `GPRMC`
3. `GPGLL` (if enabled)
4. `GPGSA` (if enabled)
5. `GPGSV` (if enabled)
6. `GPHDT` (if enabled)
7. `GPVTG` (if enabled)
8. `GPZDA` (if enabled)

This matches the `NmeaEngine.tick()` loop in `backend/nmea/engine.py`. All sentences for a given tick are written back-to-back with `\r\n` line terminators.

## Example output

With all sentences enabled, a single 1 Hz tick looks like:

```
$GPGGA,192430.00,3307.6980,N,11716.8180,W,1,12,0.9,13716.0,M,-32.6,M,,*5F
$GPRMC,192430.00,A,3307.6980,N,11716.8180,W,450,360,100426,,,A*7B
$GPGLL,3307.6980,N,11716.8180,W,192430.00,A,A*7C
$GPGSA,A,3,01,02,03,04,05,06,07,08,09,10,11,12,1.0,0.9,0.5*35
$GPGSV,3,1,12,01,45,090,50,02,30,180,48,03,60,270,52,04,15,045,44*7A
$GPGSV,3,2,12,05,50,135,49,06,25,225,46,07,70,315,51,08,35,000,47*7D
$GPGSV,3,3,12,09,55,090,50,10,20,180,45,11,40,270,48,12,65,045,53*70
$GPHDT,360,T*09
$GPVTG,360,T,,M,450,N,833.4,K,A*2F
$GPZDA,192430.00,10,04,2026,00,00*69
```

Each line ends with `*<checksum>` (two hex digits) and is followed by `\r\n` on the wire. The checksum is XOR of every byte between `$` and `*`, exclusive on both ends. See [NMEA Protocol](../reference/nmea-protocol.md) for the algorithm in detail.

## Where the state lives

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| `GPGGA` enabled | Pinned on | (no var) | Always on |
| `GPRMC` enabled | Pinned on | (no var) | Always on |
| `GPGLL`, `GPGSA`, `GPGSV`, `GPHDT`, `GPVTG`, `GPZDA` | NMEA panel | (no per-sentence boot var) | No - set via UI per run |

There is intentionally no env-var path to pre-select optional sentences at boot. The thinking: the right set depends on what's connected downstream, which is a per-deployment decision better handled by the operator at start time.

## What's next

- [NMEA Sentence Catalog](../user-guides/nmea-sentence-catalog.md) - per-sentence field-by-field reference.
- [NMEA Protocol](../reference/nmea-protocol.md) - the framing, checksum, talker-ID format.
- [Serial Output](serial-output.md) - downstream USB consumer setup.
- [Output Viewer](output-viewer.md) - watch the sentences scroll live as you toggle them.
