# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_receiver_runner.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for ReceiverRunner class."""

from unittest.mock import Mock, patch

from backend.receiver_runner import ReceiverRunner, get_receiver_runner


class TestReceiverRunner:
    """Tests for ReceiverRunner class."""

    def test_initial_state(self):
        """Should initialize with correct default state."""
        runner = ReceiverRunner()
        assert runner.is_running is False
        assert runner.is_connected is False
        assert runner._receiver is None
        assert runner._engine is None
        assert runner._serial is None

    def test_set_ws_manager(self):
        """Should store WebSocket manager and event loop."""
        runner = ReceiverRunner()
        mock_ws = Mock()
        mock_loop = Mock()

        runner.set_ws_manager(mock_ws, mock_loop)

        assert runner._ws_manager is mock_ws
        assert runner._event_loop is mock_loop

    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_start_without_serial(self, mock_engine_class, mock_receiver_class):
        """Should start without serial device."""
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="udp",
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        assert runner.is_running is True
        mock_engine_class.assert_called_once()
        mock_receiver_class.assert_called_once()
        mock_receiver.start.assert_called_once()

        runner.stop()

    @patch("backend.receiver_runner.SerialManager")
    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_start_with_serial(
        self, mock_engine_class, mock_receiver_class, mock_serial_class
    ):
        """Should open serial port when device specified."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="tcp",
            serial_device="/dev/ttyUSB0",
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        assert runner.is_running is True
        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", baudrate=115200)
        mock_serial.open.assert_called_once()

        runner.stop()
        mock_serial.close.assert_called_once()

    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_start_already_running(self, mock_engine_class, mock_receiver_class):
        """Should not start if already running."""
        runner = ReceiverRunner()
        runner._running = True

        runner.start(
            port=12000,
            protocol="udp",
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        mock_engine_class.assert_not_called()
        runner._running = False

    def test_stop_when_not_running(self):
        """Should handle stop when not running."""
        runner = ReceiverRunner()
        runner.stop()  # Should not raise

    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_stop_with_receiver(self, mock_engine_class, mock_receiver_class):
        """Should stop receiver properly."""
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="udp",
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        runner.stop()

        assert runner.is_running is False
        mock_receiver.stop.assert_called_once()

    def test_get_state_no_receiver(self):
        """Should return None if no receiver."""
        runner = ReceiverRunner()
        assert runner.get_state() is None

    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_get_state_with_receiver(self, mock_engine_class, mock_receiver_class):
        """Should return receiver state."""
        mock_receiver = Mock()
        mock_receiver.state.is_connected = True
        mock_receiver.state.packet_count = 42
        mock_receiver.state.sender_address = "192.168.1.100"
        mock_receiver_class.return_value = mock_receiver

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="udp",
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        state = runner.get_state()
        assert state["is_connected"] is True
        assert state["packet_count"] == 42
        assert state["sender_address"] == "192.168.1.100"

        runner.stop()

    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_handle_packet(self, mock_engine_class, mock_receiver_class):
        """Should handle incoming GPS packet."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA...", "$GPRMC..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="udp",
            serial_device=None,
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        # Simulate receiving a packet
        runner._handle_packet(
            {
                "lat": 33.0,
                "lon": -117.0,
                "alt_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            }
        )

        mock_engine.update_position.assert_called_once_with(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
        )
        mock_engine.generate.assert_called_once()

        runner.stop()

    def test_handle_packet_no_engine(self):
        """Should handle packet gracefully when no engine."""
        runner = ReceiverRunner()
        # Should not raise
        runner._handle_packet(
            {
                "lat": 33.0,
                "lon": -117.0,
                "alt_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            }
        )

    @patch("backend.receiver_runner.SerialManager")
    @patch("backend.receiver_runner.NetworkReceiver")
    @patch("backend.receiver_runner.NmeaEngine")
    def test_handle_packet_with_serial(
        self, mock_engine_class, mock_receiver_class, mock_serial_class
    ):
        """Should write NMEA to serial port."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA...\r\n", "$GPRMC...\r\n"]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver
        mock_serial = Mock()
        mock_serial.is_open = True
        mock_serial.write.return_value = 20
        mock_serial_class.return_value = mock_serial

        runner = ReceiverRunner()
        runner.start(
            port=12000,
            protocol="udp",
            serial_device="/dev/ttyUSB0",
            enabled_sentences={"GPGGA", "GPRMC"},
        )

        runner._handle_packet(
            {
                "lat": 33.0,
                "lon": -117.0,
                "alt_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            }
        )

        assert mock_serial.write.call_count == 2

        runner.stop()


class TestGetReceiverRunner:
    """Tests for get_receiver_runner singleton."""

    def test_returns_same_instance(self):
        """Should return same instance each call."""
        runner1 = get_receiver_runner()
        runner2 = get_receiver_runner()
        assert runner1 is runner2

    def test_returns_receiver_runner(self):
        """Should return ReceiverRunner instance."""
        runner = get_receiver_runner()
        assert isinstance(runner, ReceiverRunner)
