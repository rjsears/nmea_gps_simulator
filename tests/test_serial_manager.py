# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_serial_manager.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for serial manager."""

from unittest.mock import Mock, patch
from backend.serial_manager import SerialManager, list_serial_ports


class TestListSerialPorts:
    @patch("backend.serial_manager.serial.tools.list_ports.comports")
    def test_list_ports(self, mock_comports):
        mock_port1 = Mock()
        mock_port1.device = "/dev/ttyUSB0"
        mock_port1.description = "USB Serial"

        mock_port2 = Mock()
        mock_port2.device = "/dev/ttyUSB1"
        mock_port2.description = "USB Serial"

        mock_comports.return_value = [mock_port1, mock_port2]

        ports = list_serial_ports()
        assert len(ports) == 2
        assert ports[0]["device"] == "/dev/ttyUSB0"


class TestSerialManager:
    @patch("backend.serial_manager.serial.Serial")
    def test_open_close(self, mock_serial_class):
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        manager = SerialManager("/dev/ttyUSB0", baudrate=115200)
        manager.open()

        mock_serial_class.assert_called_once_with(
            "/dev/ttyUSB0",
            baudrate=115200,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=1,
        )

        manager.close()
        mock_serial.close.assert_called_once()

    @patch("backend.serial_manager.serial.Serial")
    def test_write(self, mock_serial_class):
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial_class.return_value = mock_serial

        manager = SerialManager("/dev/ttyUSB0")
        manager.open()
        manager.write("$GPGGA,test*00\r\n")

        mock_serial.write.assert_called_once_with(b"$GPGGA,test*00\r\n")
