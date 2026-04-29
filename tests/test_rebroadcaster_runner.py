# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_rebroadcaster_runner.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 29th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for RebroadcasterRunner class."""

import pytest
from unittest.mock import Mock, patch

from backend.rebroadcaster_runner import RebroadcasterRunner, get_rebroadcaster_runner


class TestRebroadcasterRunner:
    """Tests for RebroadcasterRunner class."""

    def test_initial_state(self):
        """Should initialize with correct default state."""
        runner = RebroadcasterRunner()
        assert runner.is_running is False
        assert runner.is_connected is False
        assert runner._receiver is None
        assert runner._engine is None
        assert runner._serial is None
        assert runner._efb_sender is None
        assert runner._udp_socket is None

    def test_is_connected_no_receiver(self):
        """Should return False when no receiver."""
        runner = RebroadcasterRunner()
        assert runner.is_connected is False

    def test_is_connected_with_receiver(self):
        """Should return receiver connection state."""
        runner = RebroadcasterRunner()
        mock_receiver = Mock()
        mock_receiver.state.is_connected = True
        runner._receiver = mock_receiver

        assert runner.is_connected is True

    def test_set_ws_manager(self):
        """Should store WebSocket manager and event loop."""
        runner = RebroadcasterRunner()
        mock_ws = Mock()
        mock_loop = Mock()

        runner.set_ws_manager(mock_ws, mock_loop)

        assert runner._ws_manager is mock_ws
        assert runner._event_loop is mock_loop

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_basic(self, mock_engine_class, mock_receiver_class):
        """Should start with basic configuration."""
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(port=12000)

        assert runner.is_running is True
        mock_engine_class.assert_called_once()
        mock_receiver_class.assert_called_once()
        mock_receiver.start.assert_called_once()

        runner.stop()

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_already_running(self, mock_engine_class, mock_receiver_class):
        """Should not start if already running."""
        runner = RebroadcasterRunner()
        runner._running = True

        runner.start(port=12000)

        mock_engine_class.assert_not_called()
        runner._running = False

    @patch("backend.rebroadcaster_runner.SerialManager")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_with_usb(
        self, mock_engine_class, mock_receiver_class, mock_serial_class
    ):
        """Should open serial port when USB enabled."""
        mock_serial = Mock()
        mock_serial_class.return_value = mock_serial
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_usb=True,
            serial_device="/dev/ttyUSB0",
            baudrate=9600,
        )

        assert runner.is_running is True
        mock_serial_class.assert_called_once_with("/dev/ttyUSB0", baudrate=9600)
        mock_serial.open.assert_called_once()

        runner.stop()
        mock_serial.close.assert_called_once()

    @patch("backend.rebroadcaster_runner.SerialManager")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_usb_failure(
        self, mock_engine_class, mock_receiver_class, mock_serial_class
    ):
        """Should raise error when serial port fails to open."""
        mock_serial = Mock()
        mock_serial.open.side_effect = Exception("Port not found")
        mock_serial_class.return_value = mock_serial

        runner = RebroadcasterRunner()
        with pytest.raises(RuntimeError) as exc_info:
            runner.start(
                port=12000,
                rebroadcast_usb=True,
                serial_device="/dev/ttyUSB0",
            )

        assert "Failed to open serial port" in str(exc_info.value)

    @patch("backend.rebroadcaster_runner.EFBSender")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_with_efb_broadcast(
        self, mock_engine_class, mock_receiver_class, mock_efb_class
    ):
        """Should create EFB sender with broadcast."""
        mock_efb = Mock()
        mock_efb_class.return_value = mock_efb
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            efb_enabled=True,
            foreflight_broadcast=True,
            foreflight_sim_name="TestSim",
        )

        assert runner.is_running is True
        mock_efb_class.assert_called_once_with(
            sim_name="TestSim",
            broadcast=True,
            target_ips=[],
        )

        runner.stop()
        mock_efb.close.assert_called_once()

    @patch("backend.rebroadcaster_runner.parse_ip_list")
    @patch("backend.rebroadcaster_runner.EFBSender")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_with_efb_ips(
        self, mock_engine_class, mock_receiver_class, mock_efb_class, mock_parse
    ):
        """Should create EFB sender with target IPs."""
        mock_parse.return_value = ["192.168.1.100", "192.168.1.101"]
        mock_efb = Mock()
        mock_efb_class.return_value = mock_efb
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            efb_enabled=True,
            efb_ip_enabled=True,
            efb_target_ips="192.168.1.100,192.168.1.101",
            foreflight_sim_name="TestSim",
        )

        assert runner.is_running is True
        mock_parse.assert_called_once_with("192.168.1.100,192.168.1.101")
        mock_efb_class.assert_called_once_with(
            sim_name="TestSim",
            broadcast=False,
            target_ips=["192.168.1.100", "192.168.1.101"],
        )

        runner.stop()

    @patch("backend.rebroadcaster_runner.socket")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_start_with_udp_retransmit(
        self, mock_engine_class, mock_receiver_class, mock_socket_module
    ):
        """Should create UDP socket for retransmit."""
        mock_socket = Mock()
        mock_socket_module.socket.return_value = mock_socket
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_udp=True,
            rebroadcast_udp_ip="192.168.1.200",
            rebroadcast_udp_port=12001,
        )

        assert runner.is_running is True
        assert runner._udp_retransmit_ip == "192.168.1.200"
        assert runner._udp_retransmit_port == 12001
        mock_socket_module.socket.assert_called_once()

        runner.stop()
        mock_socket.close.assert_called_once()

    def test_stop_when_not_running(self):
        """Should handle stop when not running."""
        runner = RebroadcasterRunner()
        runner.stop()  # Should not raise

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_stop_cleans_up(self, mock_engine_class, mock_receiver_class):
        """Should clean up all resources on stop."""
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(port=12000)

        runner.stop()

        assert runner.is_running is False
        assert runner._receiver is None
        assert runner._engine is None
        mock_receiver.stop.assert_called_once()

    @patch("backend.rebroadcaster_runner.SerialManager")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_stop_serial_error_handled(
        self, mock_engine_class, mock_receiver_class, mock_serial_class
    ):
        """Should handle serial close errors gracefully."""
        mock_serial = Mock()
        mock_serial.close.side_effect = Exception("Close error")
        mock_serial_class.return_value = mock_serial
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_usb=True,
            serial_device="/dev/ttyUSB0",
        )

        # Should not raise
        runner.stop()
        assert runner.is_running is False

    def test_get_state_no_receiver(self):
        """Should return None when no receiver."""
        runner = RebroadcasterRunner()
        assert runner.get_state() is None

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_get_state_with_receiver(self, mock_engine_class, mock_receiver_class):
        """Should return receiver state."""
        mock_receiver = Mock()
        mock_receiver.state.is_connected = True
        mock_receiver.state.packet_count = 42
        mock_receiver.state.sender_address = "192.168.1.50"
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(port=12000)

        state = runner.get_state()
        assert state["is_connected"] is True
        assert state["packet_count"] == 42
        assert state["sender_address"] == "192.168.1.50"

        runner.stop()

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_no_engine(self, mock_engine_class, mock_receiver_class):
        """Should handle packet gracefully when no engine."""
        runner = RebroadcasterRunner()
        # Should not raise - just logs warning
        runner._handle_packet(
            {
                "lat": 33.0,
                "lon": -117.0,
                "alt_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            }
        )

    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_basic(self, mock_engine_class, mock_receiver_class):
        """Should update engine and generate NMEA."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA...", "$GPRMC..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        runner = RebroadcasterRunner()
        runner.start(port=12000)

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

    @patch("backend.rebroadcaster_runner.SerialManager")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_writes_serial(
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

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_usb=True,
            serial_device="/dev/ttyUSB0",
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

    @patch("backend.rebroadcaster_runner.EFBSender")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_sends_efb(
        self, mock_engine_class, mock_receiver_class, mock_efb_class
    ):
        """Should send to EFB apps."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver
        mock_efb = Mock()
        mock_efb_class.return_value = mock_efb

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            efb_enabled=True,
            foreflight_broadcast=True,
            foreflight_sim_name="TestSim",
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

        mock_efb.send.assert_called_once_with(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            heading=270,
            speed_kts=120,
        )

        runner.stop()

    @patch("backend.rebroadcaster_runner.socket")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_udp_retransmit(
        self, mock_engine_class, mock_receiver_class, mock_socket_module
    ):
        """Should retransmit via UDP."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver
        mock_socket = Mock()
        mock_socket_module.socket.return_value = mock_socket

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_udp=True,
            rebroadcast_udp_ip="192.168.1.200",
            rebroadcast_udp_port=12001,
        )

        test_packet = {
            "lat": 33.0,
            "lon": -117.0,
            "alt_ft": 5000,
            "speed_kts": 120,
            "heading": 270,
        }
        runner._handle_packet(test_packet)

        mock_socket.sendto.assert_called_once()
        call_args = mock_socket.sendto.call_args
        assert call_args[0][1] == ("192.168.1.200", 12001)

        runner.stop()

    @patch("backend.rebroadcaster_runner.socket")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_handle_packet_udp_error_handled(
        self, mock_engine_class, mock_receiver_class, mock_socket_module
    ):
        """Should handle UDP send errors gracefully."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver
        mock_socket = Mock()
        mock_socket.sendto.side_effect = Exception("Network error")
        mock_socket_module.socket.return_value = mock_socket

        runner = RebroadcasterRunner()
        runner.start(
            port=12000,
            rebroadcast_udp=True,
            rebroadcast_udp_ip="192.168.1.200",
        )

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

        runner.stop()

    @patch("backend.rebroadcaster_runner.asyncio")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_broadcast_nmea(self, mock_engine_class, mock_receiver_class, mock_asyncio):
        """Should broadcast NMEA via WebSocket."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA...", "$GPRMC..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver

        mock_ws = Mock()
        mock_loop = Mock()

        runner = RebroadcasterRunner()
        runner.set_ws_manager(mock_ws, mock_loop)
        runner.start(port=12000)

        runner._handle_packet(
            {
                "lat": 33.0,
                "lon": -117.0,
                "alt_ft": 5000,
                "speed_kts": 120,
                "heading": 270,
            }
        )

        mock_asyncio.run_coroutine_threadsafe.assert_called()

        runner.stop()

    @patch("backend.rebroadcaster_runner.asyncio")
    @patch("backend.rebroadcaster_runner.NetworkReceiver")
    @patch("backend.rebroadcaster_runner.NmeaEngine")
    def test_broadcast_nmea_error_handled(
        self, mock_engine_class, mock_receiver_class, mock_asyncio
    ):
        """Should handle WebSocket broadcast errors gracefully."""
        mock_engine = Mock()
        mock_engine.generate.return_value = ["$GPGGA..."]
        mock_engine_class.return_value = mock_engine
        mock_receiver = Mock()
        mock_receiver_class.return_value = mock_receiver
        mock_asyncio.run_coroutine_threadsafe.side_effect = Exception("WS error")

        mock_ws = Mock()
        mock_loop = Mock()

        runner = RebroadcasterRunner()
        runner.set_ws_manager(mock_ws, mock_loop)
        runner.start(port=12000)

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

        runner.stop()

    def test_broadcast_nmea_no_ws_manager(self):
        """Should handle broadcast when no WS manager."""
        runner = RebroadcasterRunner()
        # Should not raise
        runner._broadcast_nmea(["$GPGGA...", "$GPRMC..."])


class TestGetRebroadcasterRunner:
    """Tests for get_rebroadcaster_runner singleton."""

    def test_returns_same_instance(self):
        """Should return same instance each call."""
        runner1 = get_rebroadcaster_runner()
        runner2 = get_rebroadcaster_runner()
        assert runner1 is runner2

    def test_returns_rebroadcaster_runner(self):
        """Should return RebroadcasterRunner instance."""
        runner = get_rebroadcaster_runner()
        assert isinstance(runner, RebroadcasterRunner)
