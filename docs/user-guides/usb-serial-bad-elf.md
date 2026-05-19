# USB Serial (Bad Elf)

The Bad Elf SBK-2500 was the original target hardware for this project and remains the canonical USB-serial sink. This guide walks through end-to-end setup from cable choice to verified NMEA on the downstream device. The same procedure applies to any USB-serial bridge with minor cable / driver differences.

## The hardware

| Component | Choice |
|-----------|--------|
| **Bad Elf device** | SBK-2500 (RS-232 output) or Bad Elf Pro / Pro+ (USB-C / Lightning) |
| **Host-to-device cable** | USB-A on the host side; the device-side end depends on the model - check the Bad Elf documentation. The SBK-2500 typically uses a USB-A to RJ-45 (Yost-pinout) cable. |
| **Downstream consumer** | Whatever expects NMEA-0183 in: legacy avionics, an HSI, a moving-map display. |
| **Cable from Bad Elf to downstream** | Determined entirely by the consumer's connector. RS-232 9-pin D-sub is the most common. |

## Host-side preparation

### Confirm Docker sees `/dev`

The simulator container needs `/dev` to enumerate USB-serial devices. In `docker-compose.yml`:

```yaml
services:
  gps-emulator:
    privileged: true
    volumes:
      - /dev:/dev
```

Both are required. `privileged: true` is the easiest way to grant device access; without it, you'd need to enumerate each device individually with `devices:` entries.

### Plug in the device **before** starting the container

The bind mount of `/dev` happens at container start. On most Linux kernels, devices added after `docker compose up -d` do appear in the container's `/dev` automatically, but the simulator's serial enumerator only rescans on **Refresh** clicks or restart. The reliable rule:

1. Plug the Bad Elf into the host.
2. Confirm with `ls /dev/tty*` on the host - look for `/dev/ttyUSB0` (Linux) or `/dev/tty.usbserial-<xxxx>` (macOS).
3. `docker compose up -d`.

If you have to hot-plug after start: `docker compose restart gps-emulator`.

### Verify visibility inside the container

```bash
docker compose exec gps-emulator ls /dev/tty*
```

You should see the same device paths the host shows. If they're missing, the bind mount didn't work; fix that before continuing.

## Configure the simulator side

### Via the UI

1. Pick a mode that supports USB output (Stand-Alone, Sender, Receiver, or Rebroadcaster).
2. In the USB block:
   - Toggle **USB Serial Output** on.
   - Pick the Bad Elf's device path from the **Device** dropdown.
   - Set the **Baud Rate** to match the downstream consumer (see below).
3. Press **Start**.

### Via env vars (headless auto-start)

```yaml
environment:
  - AUTO_START_MODE=rebroadcaster
  - AUTO_START_USB_ENABLED=true
  - AUTO_START_USB_DEVICE=/dev/ttyUSB0
  - SERIAL_BAUDRATE=9600
```

`SERIAL_BAUDRATE` is the host-wide default - all modes use it as the initial value. Override it per-run in the UI if needed.

## Baud rate choice

The right baud is **whatever the downstream consumer expects**. There's no "best" choice in the abstract.

| Consumer | Likely baud |
|----------|-------------|
| Legacy avionics with NMEA-0183 input | 4800 or 9600 |
| Bad Elf SBK-2500 pass-through to an iPad | 115200 (the device's USB side runs full speed) |
| Garmin GPSMAP-class panels | 9600 |
| Modern integrated avionics with NMEA | 38400 or 115200 |
| Generic test rig | 115200 (the project default, fastest, fewest buffer issues) |

If you don't know, start at 9600 and step up. At low baud (4800, 9600), enabling too many optional NMEA sentences will overflow the consumer's buffer - see [NMEA Sentences](../manual/nmea-sentences.md) for the trade-off.

## Wire format

The simulator drives **8N1** (8 data bits, no parity, 1 stop bit). This is the NMEA-0183 standard and there is no UI knob to change it. If your consumer expects 7E1 or 7O1, use a different bridge.

## Wiring the Bad Elf to the downstream consumer

The Bad Elf SBK-2500 emits standard RS-232 levels (+/- 12V). For a 9-pin D-sub downstream port:

| Bad Elf pin (RJ-45, Yost) | DB-9 pin (DCE) | Signal |
|----------------------------|----------------|--------|
| TX (4) | Pin 2 (RX) | Bad Elf TX -> consumer RX |
| RX (3) | Pin 3 (TX) | (Optional) consumer TX -> Bad Elf RX |
| GND (5) | Pin 5 | Signal ground |

The simulator only **transmits** NMEA, so the Bad Elf's RX line and the consumer's TX line are unused for this use case. If your consumer's avionics expects to send back acknowledgements, you'd need to wire RX too - the simulator doesn't process incoming bytes on the serial line, so the link will work but the consumer's ACKs are dropped.

For other Bad Elf models (USB-C, Lightning, Pro+), check the device's pinout / cable kit. The host side is always USB-A; the device side varies.

## Verifying NMEA on the wire

| Where to look | What to expect |
|---------------|----------------|
| Simulator's **Output Viewer** | NMEA scrolling at 1 Hz; same bytes hit the serial line. |
| Simulator's **Status Display** | Serial row green with the selected device path. |
| `screen /dev/ttyUSB1 9600` on the same host (with a loopback Bad Elf) | NMEA bytes appearing once per second. |
| Downstream consumer's GPS-source screen | Position updates within a few seconds of pressing Start. |

If the Output Viewer shows NMEA but the consumer is silent, the issue is almost always one of:

- Baud rate mismatch.
- TX/RX swap on the cable.
- A break in the cable (try a known-good cable).
- Consumer expects different wire format (rare; very few consumers don't accept 8N1).

## Common gotchas

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Device dropdown is empty | Bad Elf isn't enumerated by the host. | `ls /dev/tty*` on the host; if missing, check the USB cable and the FTDI/Prolific driver on macOS. |
| Device dropdown shows the path, but Start fails with "Failed to open serial port: [Errno 2]" | Path was removed between Refresh and Start (rare; cable wiggle). | Replug, Refresh, Start. |
| Start fails with "[Errno 13] Permission denied" | Container lacks privileged access. | Add `privileged: true` to compose. |
| NMEA flows in Output Viewer but consumer is silent | Baud mismatch, TX/RX swap, or cable break. | Try a different baud; swap a known-good cable. |
| Consumer gets garbled characters | Baud mismatch is the most common (a 9600-vs-4800 mistake renders gibberish). | Match baud exactly. |
| Consumer occasionally misses sentences | Buffer overflow at low baud with too many sentences enabled. | Disable optional NMEA sentences; start with just `GPGGA` + `GPRMC`. |
| `docker compose restart` was needed after hot-plug | Expected. The container's enumerator scans `/dev` at start. | Plug before start; restart if hot-plugging. |

## Multiple Bad Elf devices

If you have two USB-serial bridges plugged in, both appear in the dropdown (`/dev/ttyUSB0`, `/dev/ttyUSB1`). The simulator drives **one at a time** - per-mode there's a single device picker.

For driving two consumers simultaneously, your options:

| Pattern | How |
|---------|-----|
| One simulator, one device, splitter cable | Use a passive RS-232 Y-splitter; both consumers see the same NMEA. |
| Two simulator containers, one device each | Run two simulator containers on the same host (different web UI ports), each with its own `AUTO_START_USB_DEVICE`. |
| Rebroadcaster fan-out | A single Rebroadcaster can drive USB and also UDP retransmit to a second host that also drives USB - effectively a "via the network" splitter. |

The single-container, multiple-device pattern is intentionally not supported in the UI - the use case is too niche for the complexity it would add.

## What's next

- [Serial Output](../manual/serial-output.md) - the UI panel reference.
- [NMEA Sentences](../manual/nmea-sentences.md) - which sentences to enable for which consumer.
- [NMEA Sentence Catalog](nmea-sentence-catalog.md) - field-by-field reference for every supported sentence.
