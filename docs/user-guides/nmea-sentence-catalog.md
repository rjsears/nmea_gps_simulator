# NMEA Sentence Catalog

This is the per-sentence reference for every NMEA-0183 sentence the simulator can emit. The [NMEA Sentences](../manual/nmea-sentences.md) manual page covers the panel; this page covers what's actually in the bytes.

For the framing, checksum algorithm, and talker-ID notes, see [NMEA Protocol](../reference/nmea-protocol.md).

## Sentences emitted

The simulator emits the eight standard sentences listed below. Two are always on, six are operator-toggleable.

| Sentence | Always on | Carries |
|----------|-----------|---------|
| [`GPGGA`](#gpgga) | yes | Fix data: position, altitude, fix quality |
| [`GPRMC`](#gprmc) | yes | Recommended minimum: position, speed, heading, date/time |
| [`GPGLL`](#gpgll) | no | Geographic position lat/lon |
| [`GPGSA`](#gpgsa) | no | GPS DOP and active satellites |
| [`GPGSV`](#gpgsv) | no | Satellites in view |
| [`GPHDT`](#gphdt) | no | True heading |
| [`GPVTG`](#gpvtg) | no | Track made good and ground speed |
| [`GPZDA`](#gpzda) | no | Time and date |

Talker ID is `GP` (GPS) for every sentence the simulator emits. No `GN` (multi-GNSS), no `GL` (GLONASS) - this is a GPS simulator.

## GPGGA

GPS Fix Data - the most-consumed NMEA sentence.

```
$GPGGA,192430.00,3307.6980,N,11716.8180,W,1,12,0.9,13716.0,M,-32.6,M,,*5F
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPGGA` | Sentence type |
| UTC time | 1 | `192430.00` | `hhmmss.ss` UTC |
| Latitude | 2 | `3307.6980` | `ddmm.mmmm` |
| N/S | 3 | `N` | Hemisphere |
| Longitude | 4 | `11716.8180` | `dddmm.mmmm` |
| E/W | 5 | `W` | Hemisphere |
| Fix quality | 6 | `1` | 0=invalid, 1=GPS fix, 2=DGPS, ... |
| Satellites in use | 7 | `12` | Always 12 (simulated) |
| HDOP | 8 | `0.9` | Horizontal dilution of precision (simulated) |
| Altitude | 9 | `13716.0` | Meters above MSL |
| Altitude unit | 10 | `M` | Always `M` |
| Geoid separation | 11 | `-32.6` | Geoid - WGS84 separation, meters |
| Separation unit | 12 | `M` | Always `M` |
| DGPS age | 13 | (empty) | Always empty - not simulating DGPS |
| DGPS station | 14 | (empty) | Same |
| Checksum | 15 | `*5F` | XOR checksum |

Cadence: once per tick (1 Hz).

## GPRMC

Recommended Minimum - position, speed, course, date/time.

```
$GPRMC,192430.00,A,3307.6980,N,11716.8180,W,450,360,100426,,,A*7B
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPRMC` | |
| UTC time | 1 | `192430.00` | |
| Status | 2 | `A` | `A`=valid, `V`=warning. Always `A` when emulator is running. |
| Latitude | 3 | `3307.6980` | |
| N/S | 4 | `N` | |
| Longitude | 5 | `11716.8180` | |
| E/W | 6 | `W` | |
| Speed | 7 | `450` | Knots |
| Course | 8 | `360` | Degrees true |
| Date | 9 | `100426` | `ddmmyy` UTC |
| Magnetic variation | 10 | (empty) | Not simulated |
| Var direction | 11 | (empty) | Same |
| Mode indicator | 12 | `A` | `A`=autonomous. Always `A`. |
| Checksum | 13 | `*7B` | |

Cadence: once per tick.

## GPGLL

Geographic Position - lat/lon plus UTC and status. Subset of GPGGA.

```
$GPGLL,3307.6980,N,11716.8180,W,192430.00,A,A*7C
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPGLL` | |
| Latitude | 1 | `3307.6980` | |
| N/S | 2 | `N` | |
| Longitude | 3 | `11716.8180` | |
| E/W | 4 | `W` | |
| UTC time | 5 | `192430.00` | |
| Status | 6 | `A` | `A`=valid |
| Mode indicator | 7 | `A` | `A`=autonomous |
| Checksum | 8 | `*7C` | |

Cadence: once per tick (when enabled).

Useful for consumers that specifically look for `GPGLL` over `GPGGA`. Some HSI implementations do.

## GPGSA

GPS DOP and Active Satellites. Pads out a "real GPS receiver" feel.

```
$GPGSA,A,3,01,02,03,04,05,06,07,08,09,10,11,12,1.0,0.9,0.5*35
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPGSA` | |
| Mode 1 | 1 | `A` | `A`=automatic, `M`=manual |
| Mode 2 | 2 | `3` | 1=no fix, 2=2D, 3=3D |
| PRN 1-12 | 3-14 | `01..12` | Active satellite PRN numbers. Always 12 satellites. |
| PDOP | 15 | `1.0` | Position DOP |
| HDOP | 16 | `0.9` | Horizontal DOP |
| VDOP | 17 | `0.5` | Vertical DOP |
| Checksum | 18 | `*35` | |

Cadence: once per tick (when enabled).

DOP values are static (simulated). They're realistic for "ideal" conditions.

## GPGSV

Satellites in View. Drives sat-view widgets. Three sentences per tick (1/3, 2/3, 3/3) covering all 12 simulated satellites.

```
$GPGSV,3,1,12,01,45,090,50,02,30,180,48,03,60,270,52,04,15,045,44*7A
$GPGSV,3,2,12,05,50,135,49,06,25,225,46,07,70,315,51,08,35,000,47*7D
$GPGSV,3,3,12,09,55,090,50,10,20,180,45,11,40,270,48,12,65,045,53*70
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPGSV` | |
| Total messages | 1 | `3` | Always 3 (12 sats / 4 per msg) |
| Message number | 2 | `1`, `2`, `3` | |
| Satellites in view | 3 | `12` | Always 12 |
| Sat 1 PRN | 4 | `01` | |
| Sat 1 elevation | 5 | `45` | Degrees above horizon |
| Sat 1 azimuth | 6 | `090` | Degrees true |
| Sat 1 SNR | 7 | `50` | dB-Hz (0-99) |
| Sat 2 ... | 8-19 | | Same pattern, 4 sats per message |
| Checksum | 20 | `*7A` | |

Cadence: three sentences per tick (when enabled).

Satellite positions and SNRs are static. The simulator does not model satellite geometry over time - it's a position simulator, not an RF simulator.

## GPHDT

True Heading. Some autopilots and HSIs look for this specifically.

```
$GPHDT,360,T*09
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPHDT` | |
| Heading | 1 | `360` | Degrees true |
| Reference | 2 | `T` | Always `T` (true, not magnetic) |
| Checksum | 3 | `*09` | |

Cadence: once per tick (when enabled).

!!! warning "True vs Magnetic"
    `GPHDT` is **true** heading by definition. If your consumer expects magnetic heading via this sentence, you'll get an offset equal to the local magnetic variation. The simulator does not apply variation. Use `GPVTG` if you need magnetic track.

## GPVTG

Track Made Good and Ground Speed. Both true and (notionally) magnetic.

```
$GPVTG,360,T,,M,450,N,833.4,K,A*2F
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPVTG` | |
| True track | 1 | `360` | Degrees true |
| `T` | 2 | `T` | True indicator |
| Magnetic track | 3 | (empty) | **Not simulated** - the variation field is empty |
| `M` | 4 | `M` | Magnetic indicator |
| Speed (knots) | 5 | `450` | |
| `N` | 6 | `N` | Knots indicator |
| Speed (km/h) | 7 | `833.4` | Converted from knots |
| `K` | 8 | `K` | km/h indicator |
| Mode indicator | 9 | `A` | `A`=autonomous |
| Checksum | 10 | `*2F` | |

Cadence: once per tick (when enabled).

The magnetic-track field is intentionally blank. Consumers that need magnetic must apply their own variation.

## GPZDA

Time and Date in UTC. For consumers that want the clock from NMEA.

```
$GPZDA,192430.00,10,04,2026,00,00*69
```

| Field | Index | Example | Meaning |
|-------|-------|---------|---------|
| Header | 0 | `$GPZDA` | |
| UTC time | 1 | `192430.00` | |
| Day | 2 | `10` | UTC day of month |
| Month | 3 | `04` | UTC month |
| Year | 4 | `2026` | UTC year |
| Local zone hours | 5 | `00` | Always 00 (UTC) |
| Local zone minutes | 6 | `00` | Always 00 |
| Checksum | 7 | `*69` | |

Cadence: once per tick (when enabled).

The clock comes from the container's system clock. If you need a specific simulated time, set the container's clock - the simulator doesn't override it.

## Order of emission per tick

`backend/nmea/engine.py:tick()` emits enabled sentences in this fixed order:

1. `GPGGA` (always)
2. `GPRMC` (always)
3. `GPGLL` (if on)
4. `GPGSA` (if on)
5. `GPGSV` x3 (if on)
6. `GPHDT` (if on)
7. `GPVTG` (if on)
8. `GPZDA` (if on)

All sentences for a given tick are written back-to-back over USB serial and TCP, with `\r\n` between them.

## What's next

- [NMEA Sentences](../manual/nmea-sentences.md) - the UI panel for sentence selection.
- [NMEA Protocol](../reference/nmea-protocol.md) - checksum algorithm, framing details.
- [Serial Output](../manual/serial-output.md) - downstream USB consumer setup.
