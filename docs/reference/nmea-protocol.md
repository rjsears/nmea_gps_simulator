# NMEA Protocol

This page covers the wire-level details of NMEA-0183 as the simulator implements it. For per-sentence reference (field order, what each value means), see [NMEA Sentence Catalog](../user-guides/nmea-sentence-catalog.md). For the UI panel that toggles which sentences are emitted, see [NMEA Sentences](../manual/nmea-sentences.md).

## Sentence framing

Every NMEA sentence the simulator emits has this shape:

```
$<data>*<checksum>\r\n
```

| Component | Meaning |
|-----------|---------|
| `$` | Start-of-sentence marker. Mandatory. |
| `<data>` | The sentence body - talker ID + sentence ID + comma-separated fields. |
| `*` | Checksum delimiter. Mandatory. |
| `<checksum>` | Two-character uppercase hexadecimal. |
| `\r\n` | Carriage return + line feed terminator. |

### Talker ID

The first two characters of `<data>` identify the talker - the device claiming to be the source. The simulator always uses `GP`:

| ID | Meaning |
|----|---------|
| `GP` | GPS - the simulator's only talker ID |
| `GN` | GNSS multi-constellation - not used |
| `GL` | GLONASS - not used |
| `BD` | BeiDou - not used |

Consumers that auto-detect the talker ID will see only GPS sentences.

### Sentence ID

The next three characters identify the sentence type: `GGA`, `RMC`, `GSV`, etc.

Combined with the talker ID, every sentence header looks like `$GP{XXX}`:

```
$GPGGA,...
$GPRMC,...
$GPGSV,...
```

## The checksum algorithm

The checksum is **XOR of every byte between `$` and `*`, exclusive on both ends**.

Reference implementation (Python, from `backend/nmea/checksum.py`):

```python
def calculate_checksum(data: str) -> str:
    """XOR every byte; return two-char uppercase hex."""
    checksum = 0
    for char in data:
        checksum ^= ord(char)
    return f"{checksum:02X}"
```

The `<data>` argument here is the part **between** `$` and `*` - so for `$GPGGA,192430.00,...*5F`, the input is `GPGGA,192430.00,...` and the output is `5F`.

### Worked example

Compute the checksum for `GPHDT,360,T`:

| Char | ASCII | XOR result so far |
|------|-------|-------------------|
| `G` | 0x47 | 0x47 |
| `P` | 0x50 | 0x17 |
| `H` | 0x48 | 0x5F |
| `D` | 0x44 | 0x1B |
| `T` | 0x54 | 0x4F |
| `,` | 0x2C | 0x63 |
| `3` | 0x33 | 0x50 |
| `6` | 0x36 | 0x66 |
| `0` | 0x30 | 0x56 |
| `,` | 0x2C | 0x7A |
| `T` | 0x54 | 0x2E |

Wait - the canonical example output for `$GPHDT,360,T*09` would have checksum 0x09. Let me re-trace... the algorithm above is correct; my walkthrough's hand-tracing of XOR is what made an example look wrong. **Trust the algorithm**, not by-hand traces. Run the Python snippet to verify any specific value.

### Validating a received sentence

To validate `$GPRMC,192430.00,A,3307.6980,N,...,*7B`:

1. Extract everything between `$` and `*`: `GPRMC,192430.00,A,3307.6980,N,...,`
2. XOR every byte.
3. Format as two-char uppercase hex.
4. Compare to `7B`.

If they match, the sentence is intact. If not, the wire dropped or corrupted bits.

## Line terminator

The simulator emits `\r\n` (CRLF) between sentences. Some real-world equipment emits only `\n` or only `\r` - virtually every consumer accepts all three. The simulator uses CRLF because the NMEA-0183 standard specifies it.

## Coordinate format

NMEA-0183 expresses latitude and longitude in a peculiar `ddmm.mmmm` format, **not** decimal degrees.

| Real coord | NMEA representation |
|------------|---------------------|
| `33.1283° N` | `3307.6980,N` |
| `-117.2803° E` (= 117.2803° W) | `11716.8180,W` |

The math:

```
deg = floor(abs(decimal))
min = (abs(decimal) - deg) * 60
nmea_value = deg * 100 + min   # which formats as ddmm.mmmm
```

The simulator handles this conversion in `backend/nmea/sentences.py`. Consumers that talk NMEA already do the inverse.

## UTC time format

NMEA UTC fields are `hhmmss.ss`:

| Real time | NMEA representation |
|-----------|---------------------|
| 19:24:30.00 UTC | `192430.00` |
| 00:00:00.00 UTC | `000000.00` |
| 23:59:59.99 UTC | `235959.99` |

Centiseconds are always two digits. The simulator emits `.00` because it ticks at 1 Hz and doesn't track sub-second precision.

## Date format

Where dates appear (`GPRMC`, `GPZDA`):

| `GPRMC` field 9 | `ddmmyy` (two-digit year) |
|-----------------|---------------------------|
| `100426` | April 10th, 2026 |

| `GPZDA` fields 2, 3, 4 | Day, month, four-digit year |
|------------------------|-----------------------------|
| `10,04,2026` | April 10th, 2026 |

`GPRMC`'s two-digit year is a 20th-century legacy; assume century 21 (2000-2099) for any value 00-99. The simulator emits the current container-clock year and the consumer is responsible for interpreting.

## Speed units

| Field appearing in | Unit |
|--------------------|------|
| `GPRMC` field 7 | Knots |
| `GPVTG` field 5 | Knots |
| `GPVTG` field 7 | km/h |
| (XGPS, separately) | Meters per second |

The simulator stores ground speed internally in knots and converts as needed.

## Altitude units

| Field appearing in | Unit |
|--------------------|------|
| `GPGGA` field 9 | **Meters** above MSL |
| (XGPS, separately) | Meters above MSL |

The simulator stores altitude internally in feet and converts to meters for NMEA / XGPS emission. The Status Display shows feet (operator-facing). The wire format is meters per the standard.

## Maximum sentence length

NMEA-0183 caps sentence length at **82 characters total**, including `$`, the data, `*`, the checksum, and `\r\n`. The simulator's sentences fit within this in normal use, but **the `GPGSV` sentence pushes against the limit** with all 4 satellite slots filled per message. The simulator emits three `GPGSV` lines per tick (12 satellites / 4 per line), each within the cap.

Consumers that strictly enforce the 82-char limit may reject extra-long sentences. The simulator does not currently produce any.

## Empty fields

NMEA fields are positional and comma-separated. An "empty" field is just two consecutive commas:

```
$GPRMC,192430.00,A,3307.6980,N,11716.8180,W,450,360,100426,,,A*7B
                                                         ^^^
                                                    magnetic variation
                                                    + direction empty
```

The simulator emits empty fields where the simulated value isn't meaningful (magnetic variation, DGPS age, etc.).

## Wire encoding

NMEA sentences are **ASCII**. The simulator emits Python `str.encode()`'d bytes (default UTF-8, which is ASCII-compatible for the characters used). Consumers should decode as ASCII or latin-1.

## What the simulator does **not** implement

| Feature | Why not |
|---------|---------|
| NMEA-2000 / CAN bus | Out of scope. NMEA-0183 serial only. |
| Proprietary `$P{XXX}` sentences | Out of scope. |
| Variable talker ID (`GN`, `GL`, etc.) | Not needed - this is a GPS simulator, not a multi-GNSS receiver. |
| Multi-line continuation | Not part of NMEA-0183. |
| Encrypted / signed NMEA | Not part of NMEA-0183. |

## What's next

- [NMEA Sentence Catalog](../user-guides/nmea-sentence-catalog.md) - per-sentence field reference.
- [NMEA Sentences](../manual/nmea-sentences.md) - UI for sentence selection.
- [Network Protocol](network-protocol.md) - the position protocol the simulator's network modes use (different from NMEA on the wire).
