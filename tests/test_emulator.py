# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_emulator.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for EmulatorRunner class."""

import time
from unittest.mock import Mock, patch

from backend.emulator import EmulatorRunner, get_emulator


class TestEmulatorRunner:
    """Tests for EmulatorRunner class."""

    def test_initial_state(self):
        """Should initialize with correct default state."""
        emulator = EmulatorRunner()
        assert emulator.is_running is False
        assert emulator._engine is None
        assert emulator._serial is None
        assert emulator._sender is None

    def test_set_ws_manager(self):
        """Should store WebSocket manager and event loop."""
        emulator = EmulatorRunner()
        mock_ws = Mock()
        mock_loop = Mock()

        emulator.set_ws_manager(mock_ws, mock_loop)

        assert emulator._ws_manager is mock_ws
        assert emulator._event_loop is mock_loop

    @patch("backend.emulator.SerialManager")
    @patch("backend.emulator.NmeaEngine")
    def test_start_without_serial(self, mock_engine_class, mock_serial_class):
        """Should start without serial device."""
        emulator = EmulatorRunner()

        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        # Give thread time to start
        time.sleep(0.1)

        assert emulator.is_running is True
        mock_engine_class.assert_called_once()
        mock_serial_class.assert_not_called()

        emulator.stop()

    @patch("backend.emulator.SerialManager")
    @patch("backend.emulator.NmeaEngine")
    def test_start_with_serial(self, mock_engine_class, mock_serial_class):
        """Should open serial port when device specified."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial

        emulator = EmulatorRunner()

        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device="/dev/ttyUSB0",
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        time.sleep(0.1)

        assert emulator.is_running is True
        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", baudrate=115200)
        mock_serial.open.assert_called_once()

        emulator.stop()
        mock_serial.close.assert_called_once()

    @patch("backend.emulator.SerialManager")
    @patch("backend.emulator.NmeaEngine")
    def test_start_with_sender_config(self, mock_engine_class, mock_serial_class):
        """Should create network sender when config provided."""
        emulator = EmulatorRunner()

        with patch("backend.emulator.NetworkSender") as mock_sender_class:
            mock_sender = Mock()
            mock_sender_class.return_value = mock_sender

            emulator.start(
                lat=33.0,
                lon=-117.0,
                altitude_ft=5000,
                speed_kts=120,
                heading=270,
                serial_device=None,
                enabled_sentences={"GPGGA", "GPRMC"},
                sender_config={
                    "target_ip": "192.168.1.100",
                    "port": 12000,
                    "protocol": "udp",
                },
            )

            time.sleep(0.1)

            mock_sender_class.assert_called_once_with(
                target_ip="192.168.1.100",
                port=12000,
                protocol="udp",
            )

            emulator.stop()
            mock_sender.close.assert_called_once()

    @patch("backend.emulator.NmeaEngine")
    def test_start_already_running(self, mock_engine_class):
        """Should not start if already running."""
        emulator = EmulatorRunner()
        emulator._running = True

        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        mock_engine_class.assert_not_called()
        emulator._running = False

    @patch("backend.emulator.NmeaEngine")
    def test_stop_when_not_running(self, mock_engine_class):
        """Should handle stop when not running."""
        emulator = EmulatorRunner()
        emulator.stop()  # Should not raise

    @patch("backend.emulator.NmeaEngine")
    def test_set_target_altitude(self, mock_engine_class):
        """Should pass target altitude to engine."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        emulator = EmulatorRunner()
        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        time.sleep(0.1)
        emulator.set_target_altitude(10000)

        mock_engine.set_target_altitude.assert_called_with(10000)
        emulator.stop()

    @patch("backend.emulator.NmeaEngine")
    def test_set_target_speed(self, mock_engine_class):
        """Should pass target speed to engine."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        emulator = EmulatorRunner()
        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        time.sleep(0.1)
        emulator.set_target_speed(200)

        mock_engine.set_target_speed.assert_called_with(200)
        emulator.stop()

    @patch("backend.emulator.NmeaEngine")
    def test_set_target_heading(self, mock_engine_class):
        """Should pass target heading to engine."""
        mock_engine = Mock()
        mock_engine_class.return_value = mock_engine

        emulator = EmulatorRunner()
        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        time.sleep(0.1)
        emulator.set_target_heading(90)

        mock_engine.set_target_heading.assert_called_with(90)
        emulator.stop()

    @patch("backend.emulator.NmeaEngine")
    def test_get_current_state(self, mock_engine_class):
        """Should return engine state."""
        mock_engine = Mock()
        mock_engine.get_state.return_value = {
            "lat": 33.5,
            "lon": -117.5,
            "altitude_ft": 6000,
            "speed_kts": 130,
            "heading": 275,
        }
        mock_engine_class.return_value = mock_engine

        emulator = EmulatorRunner()
        emulator.start(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        time.sleep(0.1)
        state = emulator.get_current_state()

        assert state["lat"] == 33.5
        assert state["altitude_ft"] == 6000
        emulator.stop()

    def test_get_current_state_no_engine(self):
        """Should return None if no engine."""
        emulator = EmulatorRunner()
        assert emulator.get_current_state() is None

    def test_set_targets_no_engine(self):
        """Should handle target setters with no engine."""
        emulator = EmulatorRunner()
        # Should not raise
        emulator.set_target_altitude(10000)
        emulator.set_target_speed(200)
        emulator.set_target_heading(90)


class TestGetEmulator:
    """Tests for get_emulator singleton."""

    def test_returns_same_instance(self):
        """Should return same instance each call."""
        emulator1 = get_emulator()
        emulator2 = get_emulator()
        assert emulator1 is emulator2

    def test_returns_emulator_runner(self):
        """Should return EmulatorRunner instance."""
        emulator = get_emulator()
        assert isinstance(emulator, EmulatorRunner)
