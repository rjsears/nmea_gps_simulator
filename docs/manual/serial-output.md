# Serial Output

The **Serial Port** panel selects a USB-serial device and the baud rate at which to drive it. It appears in different places depending on the mode:

| Mode | Where the controls live |
|------|-------------------------|
| Stand Alone | Inside the **Output Settings** panel's USB block. |
| Sender | Inside the **Sender Settings** panel's USB block. |
| Receiver | A dedicated **Serial Port** panel in the left column. |
| Rebroadcaster | Inside the **Rebroadcaster Settings** panel's USB block. |

The underlying state is the same in every case (`backend/state.py`'s serial fields). This page documents the controls and behavior; for end-to-end hardware setup against a Bad Elf SBK-2500, see [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md).

<!-- SCREENSHOT-PENDING: serial-output-01-overview.png - Serial Port panel showing device picker, baud picker, 8N1 line. -->

## Controls

| Control | Default | Valid values | What it does |
|---------|---------|--------------|--------------|
| **Device** | `(none)` | Any path the host's `/dev` exposes that matches the supported patterns | The serial device the simulator opens at Start. |
| **Refresh** button | n/a | n/a | Rescans the host for matching device paths and rebuilds the dropdown. |
| **Baud Rate** | `115200` (`SERIAL_BAUDRATE`) | 1200 - 115200 | Symbol rate. Must match the downstream device. |
| **Format note** | "Format: 8N1 (8 data bits, no parity, 1 stop bit)" | Static | Reminder that the wire format is fixed - the simulator does not expose 7-bit or parity options. |

## Supported device-path patterns

The serial manager probes for these patterns at runtime:

| Platform | Patterns |
|----------|----------|
| Linux | `/dev/ttyUSB*`, `/dev/ttyACM*` |
| macOS | `/dev/tty.usbserial-*`, `/dev/cu.usbserial-*`, `/dev/tty.usbmodem-*`, `/dev/cu.usbmodem-*` |

Multiple matches all enumerate. The dropdown shows the path plus any human-readable description the OS reports (typically the FTDI / Prolific / CH340 chip name).

!!! info "macOS: `/dev/tty.*` vs `/dev/cu.*`"
    On macOS each USB-serial device exposes both `/dev/tty.usbserial-...` and `/dev/cu.usbserial-...`. `cu` (call-up) doesn't block on the absence of carrier detect, which is what you almost always want. Either works for an NMEA-out use case, but `cu` is the safer pick.

## Baud rates

The dropdown lists the same eight choices in every mode:

| Baud | Typical consumer |
|------|------------------|
| 1200 | Legacy modems |
| 2400 | Low-speed printers, legacy avionics |
| 4800 | GPS modules - the historical NMEA-0183 default |
| 9600 | Common embedded and EFB default |
| 19200 | Industrial / PLC |
| 38400 | Instrumentation |
| 57600 | Higher-speed embedded |
| **115200** | USB-serial bridges - **the project default** |

The simulator does not validate that the chosen baud is supported by the host's UART driver - it just opens the port at that rate. If the host can't honor the rate, opening the port fails at Start with an OS error in the Status Display.

## Behavior across Start / Stop / device hot-plug

| Event | Effect |
|-------|--------|
| Click **Refresh** with no device plugged in | Dropdown shows only "Select device...". |
| Plug in a Bad Elf, click **Refresh** | The device appears in the dropdown. (Refresh re-reads `/dev`.) |
| Pick a device, press **Start** | The serial manager opens the port with the configured baud and 8N1. If the open fails, Start aborts with an error banner. |
| Press **Stop** | The serial port is released. The downstream device sees the line go idle. |
| Unplug the device mid-run | The next write fails. The Status Display flips Serial to disconnected and an error is logged. **The simulator does not auto-reopen** - press Stop, fix the cable, press Start. |
| Container restart | `/dev` mount is refreshed; the auto-start handler reopens the device path from `AUTO_START_USB_DEVICE` if set. |

!!! warning "Hot-plugging after container start doesn't always work"
    The `-v /dev:/dev` bind mount captures the `/dev` tree as it exists at container-start time on some hosts (Linux behavior depends on the kernel's `devtmpfs` and how Docker handles it). The reliable rule: plug the USB device in **before** `docker compose up -d`. If you can't, `docker compose restart gps-emulator` after plugging is the next-best option.

## What 8N1 means and why it's fixed

NMEA-0183 mandates **8 data bits, no parity, 1 stop bit** on the serial line. Every consumer the simulator is realistically going to drive expects exactly that. The simulator does not expose a different framing.

If you have a non-NMEA-0183 consumer that wants 7E1 or 7O1 - you're outside the scope of this tool. Use a real serial-protocol bridge.

## The selected device shows in the Status panel

The [Status Display](status-display.md) panel mirrors the selection: a green dot + the chosen device path when one is picked, a gray dot + "Not selected" otherwise. Glance there to confirm the picker is talking to the runtime.

## Persistent state

| Setting | UI control | Env var | Survives restart? |
|---------|-----------|---------|-------------------|
| Selected device | Serial picker | `AUTO_START_USB_DEVICE` | Only if env var set (and the simulator auto-starts) |
| Baud rate | Serial picker | `SERIAL_BAUDRATE` | Yes (env var, used as the default for every new run) |

## What's next

- [USB Serial (Bad Elf)](../user-guides/usb-serial-bad-elf.md) - end-to-end Bad Elf SBK-2500 walkthrough including cable, jumper, and avionics-side wiring.
- [Status Display](status-display.md) - where to see the live device state.
- [Hardware Requirements](../getting-started/hardware.md) - the host-side hardware prereqs for USB serial.
