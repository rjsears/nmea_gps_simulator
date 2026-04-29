# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# serial_manager.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Serial port management for USB GPS devices."""

import logging
from typing import Optional

import serial
import serial.tools.list_ports

logger = logging.getLogger(__name__)


def list_serial_ports() -> list[dict]:
    """List available USB serial ports.

    Returns USB serial devices for both Linux and macOS:
    - Linux: /dev/ttyUSB*, /dev/ttyACM*
    - macOS: /dev/tty.usbserial-*, /dev/cu.usbserial-*, /dev/tty.usbmodem-*, /dev/cu.usbmodem-*

    Returns:
        List of dicts with 'device' and 'description' keys
    """
    ports = serial.tools.list_ports.comports()
    usb_prefixes = (
        "/dev/ttyUSB",
        "/dev/ttyACM",
        "/dev/tty.usbserial",
        "/dev/cu.usbserial",
        "/dev/tty.usbmodem",
        "/dev/cu.usbmodem",
    )
    return [
        {"device": port.device, "description": port.description}
        for port in ports
        if any(port.device.startswith(prefix) for prefix in usb_prefixes)
    ]


class SerialManager:
    """Manages serial port connection for NMEA output."""

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        timeout: float = 1,
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def open(self) -> None:
        if self.is_open:
            return
        self._serial = serial.Serial(
            self.port,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.timeout,
        )
        logger.info(f"Opened serial port {self.port} at {self.baudrate} baud")

    def close(self) -> None:
        if self._serial:
            self._serial.close()
            logger.info(f"Closed serial port {self.port}")
            self._serial = None

    def write(self, data: str) -> int:
        if not self.is_open:
            raise RuntimeError("Serial port is not open")
        return self._serial.write(data.encode())

    def write_sentences(self, sentences: list[str]) -> int:
        total = 0
        for sentence in sentences:
            total += self.write(sentence)
        return total

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
