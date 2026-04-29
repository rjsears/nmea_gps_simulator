# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_network.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for network sender and receiver."""

import pytest
import json
from unittest.mock import Mock, patch
from backend.network.sender import NetworkSender
from backend.network.receiver import (
    NetworkReceiver,
    ReceiverState,
    parse_gps_packet,
    parse_cygnus_packet,
)


class TestNetworkSender:
    def test_create_json_packet(self):
        sender = NetworkSender(target_ip="192.168.1.100", port=12000, protocol="udp")

        packet = sender.create_packet(
            lat=33.1283,
            lon=-117.2803,
            alt_ft=5000,
            speed_kts=120,
            heading=270.5,
        )

        data = json.loads(packet)
        assert data["lat"] == 33.1283
        assert data["lon"] == -117.2803
        assert data["alt_ft"] == 5000
        assert data["speed_kts"] == 120
        assert data["heading"] == 270.5
        assert "timestamp" in data

    @patch("socket.socket")
    def test_send_udp(self, mock_socket_class):
        mock_socket = Mock()
        mock_socket_class.return_value.__enter__ = Mock(return_value=mock_socket)
        mock_socket_class.return_value.__exit__ = Mock(return_value=False)

        sender = NetworkSender(target_ip="127.0.0.1", port=12000, protocol="udp")
        packet = sender.create_packet(
            lat=33.0, lon=-117.0, alt_ft=0, speed_kts=0, heading=0
        )
        sender.send(packet)

        mock_socket.sendto.assert_called_once()


class TestNetworkReceiver:
    """Tests for NetworkReceiver class."""

    def test_instantiation_with_valid_protocol_udp(self):
        """Should create receiver with UDP protocol."""
        receiver = NetworkReceiver(port=12000, protocol="udp")
        assert receiver.protocol == "udp"
        assert receiver.port == 12000

    def test_instantiation_with_valid_protocol_tcp(self):
        """Should create receiver with TCP protocol."""
        receiver = NetworkReceiver(port=12001, protocol="tcp")
        assert receiver.protocol == "tcp"

    def test_instantiation_with_protocol_case_insensitive(self):
        """Should accept protocol in any case."""
        receiver = NetworkReceiver(protocol="UDP")
        assert receiver.protocol == "udp"

        receiver2 = NetworkReceiver(protocol="Tcp")
        assert receiver2.protocol == "tcp"

    def test_instantiation_with_invalid_protocol(self):
        """Should raise ValueError for unsupported protocol."""
        with pytest.raises(ValueError) as exc_info:
            NetworkReceiver(protocol="http")
        assert "Unsupported protocol" in str(exc_info.value)
        assert "http" in str(exc_info.value)

    def test_start_stop_lifecycle(self):
        """Should start and stop without errors."""
        receiver = NetworkReceiver(port=12002, protocol="udp")

        assert receiver.state.is_running is False

        receiver.start()
        assert receiver.state.is_running is True

        receiver.stop()
        assert receiver.state.is_running is False

    def test_on_packet_callback_invocation(self):
        """Should invoke on_packet callback when handling packet."""
        received_packets = []

        def callback(data):
            received_packets.append(data)

        receiver = NetworkReceiver(port=12003, protocol="udp", on_packet=callback)

        # Directly call _handle_packet with a valid packet
        valid_packet = '{"lat": 33.0, "lon": -117.0, "alt_ft": 1000, "speed_kts": 100, "heading": 90.0, "timestamp": "2026-04-09T12:00:00Z"}'
        receiver._handle_packet(valid_packet, "127.0.0.1")

        assert len(received_packets) == 1
        assert received_packets[0]["lat"] == 33.0
        assert receiver.state.packet_count == 1
        assert receiver.state.sender_address == "127.0.0.1"
        assert receiver.state.is_connected is True

    def test_handle_packet_without_callback(self):
        """Should handle packet even without callback."""
        receiver = NetworkReceiver(port=12004, protocol="udp", on_packet=None)

        valid_packet = '{"lat": 33.0, "lon": -117.0, "alt_ft": 1000, "speed_kts": 100, "heading": 90.0, "timestamp": "2026-04-09T12:00:00Z"}'
        receiver._handle_packet(valid_packet, "192.168.1.1")

        assert receiver.state.packet_count == 1
        assert receiver.state.last_packet["lat"] == 33.0

    def test_handle_invalid_packet(self):
        """Should not update state for invalid packet."""
        receiver = NetworkReceiver(port=12005, protocol="udp")

        receiver._handle_packet("invalid json", "127.0.0.1")

        assert receiver.state.packet_count == 0
        assert receiver.state.last_packet is None


class TestReceiverState:
    """Tests for ReceiverState dataclass."""

    def test_default_values(self):
        """Should have correct default values."""
        state = ReceiverState()
        assert state.is_running is False
        assert state.is_connected is False
        assert state.last_packet is None
        assert state.packet_count == 0
        assert state.sender_address is None

    def test_has_lock(self):
        """Should have a threading lock for thread safety."""
        state = ReceiverState()
        assert hasattr(state, "_lock")
        # Verify it's a lock by acquiring and releasing
        acquired = state._lock.acquire(blocking=False)
        assert acquired is True
        state._lock.release()


class TestParseGpsPacket:
    """Tests for packet parsing."""

    def test_parse_valid_packet(self):
        """Should parse valid JSON packet."""
        packet = '{"lat": 33.1283, "lon": -117.2803, "alt_ft": 5000, "speed_kts": 120, "heading": 270.5, "timestamp": "2026-04-09T18:30:45Z"}'

        data = parse_gps_packet(packet)

        assert data["lat"] == 33.1283
        assert data["lon"] == -117.2803
        assert data["alt_ft"] == 5000
        assert data["speed_kts"] == 120
        assert data["heading"] == 270.5

    def test_parse_invalid_json(self):
        """Should return None for invalid JSON."""
        data = parse_gps_packet("not json")
        assert data is None

    def test_parse_missing_fields(self):
        """Should return None for missing required fields."""
        packet = '{"lat": 33.0}'  # Missing other fields
        data = parse_gps_packet(packet)
        assert data is None


class TestParseCygnusPacket:
    """Tests for CYGNUS format packet parsing."""

    def test_parse_valid_cygnus(self):
        """Should parse valid CYGNUS packet."""
        packet = "$CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3"

        data = parse_cygnus_packet(packet)

        assert data is not None
        assert data["lat"] == 30.266925
        assert data["lon"] == -97.742798
        assert data["heading"] == 355.5
        assert data["alt_ft"] == 37000.0
        assert data["speed_kts"] == 375.3
        assert "timestamp" in data

    def test_parse_cygnus_without_prefix(self):
        """Should return None for packet without $CYGNUS: prefix."""
        packet = "lat=30.266925&lon=-97.742798&heading=355.5&alt=37000.0&airspeed=375.3"

        data = parse_cygnus_packet(packet)
        assert data is None

    def test_parse_cygnus_missing_fields(self):
        """Should return None for CYGNUS packet missing required fields."""
        packet = (
            "$CYGNUS:lat=30.266925&lon=-97.742798"  # Missing heading, alt, airspeed
        )

        data = parse_cygnus_packet(packet)
        assert data is None

    def test_parse_cygnus_with_null_bytes(self):
        """Should handle null bytes in packet."""
        packet = "$CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3\x00\x00"

        data = parse_cygnus_packet(packet)

        assert data is not None
        assert data["lat"] == 30.266925

    def test_parse_cygnus_with_whitespace(self):
        """Should handle whitespace in values."""
        packet = "$CYGNUS:lat= 30.266925 &lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3"

        data = parse_cygnus_packet(packet)

        assert data is not None
        assert data["lat"] == 30.266925

    def test_parse_cygnus_invalid_values(self):
        """Should return None for invalid numeric values."""
        packet = "$CYGNUS:lat=invalid&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3"

        data = parse_cygnus_packet(packet)
        assert data is None


class TestParseGpsPacketCygnusDetection:
    """Tests for CYGNUS format detection in parse_gps_packet."""

    def test_detect_cygnus_format(self):
        """Should detect and parse CYGNUS format."""
        packet = "$CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3"

        data = parse_gps_packet(packet)

        assert data is not None
        assert data["lat"] == 30.266925
        assert data["speed_kts"] == 375.3

    def test_detect_cygnus_with_whitespace(self):
        """Should strip whitespace before detecting format."""
        packet = "  $CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3  "

        data = parse_gps_packet(packet)

        assert data is not None
        assert data["lat"] == 30.266925

    def test_detect_cygnus_with_null_bytes(self):
        """Should strip null bytes before parsing."""
        packet = "$CYGNUS:lat=30.266925&lon=-97.742798&heading=355.5&magvar=-6.0&alt=37000.0&airspeed=375.3\x00"

        data = parse_gps_packet(packet)

        assert data is not None

    def test_json_preferred_when_valid(self):
        """Should parse JSON when not starting with $CYGNUS:."""
        packet = '{"lat": 33.0, "lon": -117.0, "alt_ft": 5000, "speed_kts": 120, "heading": 90, "timestamp": "2026-04-09T12:00:00Z"}'

        data = parse_gps_packet(packet)

        assert data is not None
        assert data["lat"] == 33.0
        assert data["alt_ft"] == 5000  # JSON uses alt_ft, not alt

    def test_invalid_format_returns_none(self):
        """Should return None for unrecognized format."""
        packet = "SOME_OTHER_FORMAT:lat=30.0"

        data = parse_gps_packet(packet)
        assert data is None
