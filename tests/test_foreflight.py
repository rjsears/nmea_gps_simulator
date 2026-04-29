# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_foreflight.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 27th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for EFB (ForeFlight/Garmin Pilot) sender."""

import pytest
from unittest.mock import patch, MagicMock

from backend.network.foreflight import (
    EFBSender,
    ForeFlightSender,
    EFB_PORT,
    FEET_TO_METERS,
    KNOTS_TO_MS,
    parse_ip_list,
)


class TestEFBSender:
    """Tests for EFBSender class."""

    def test_init_defaults(self):
        with patch("socket.socket"):
            sender = EFBSender()
            assert sender.sim_name == "LOFT GPS"
            assert sender.broadcast is False
            assert sender.target_ips == []

    def test_init_broadcast_only(self):
        with patch("socket.socket"):
            sender = EFBSender(sim_name="CL350", broadcast=True)
            assert sender.sim_name == "CL350"
            assert sender.broadcast is True
            assert sender.target_ips == []

    def test_init_with_target_ips(self):
        with patch("socket.socket"):
            sender = EFBSender(
                sim_name="CL350", target_ips=["192.168.1.50", "192.168.1.51"]
            )
            assert sender.sim_name == "CL350"
            assert sender.broadcast is False
            assert sender.target_ips == ["192.168.1.50", "192.168.1.51"]

    def test_init_broadcast_and_ips(self):
        with patch("socket.socket"):
            sender = EFBSender(
                sim_name="ULTRA", broadcast=True, target_ips=["192.168.1.50"]
            )
            assert sender.broadcast is True
            assert sender.target_ips == ["192.168.1.50"]

    def test_create_xgps_message_basic(self):
        with patch("socket.socket"):
            sender = EFBSender(sim_name="TestSim")
            msg = sender.create_xgps_message(
                lat=33.1283,
                lon=-117.2803,
                altitude_ft=1000,
                heading=90,
                speed_kts=100,
            )

            # Check format: XGPSSimName,lon,lat,alt_m,track,speed_ms
            assert msg.startswith("XGPSTestSim,")
            parts = msg.split(",")
            assert len(parts) == 6

            # Check values
            assert parts[0] == "XGPSTestSim"
            assert float(parts[1]) == pytest.approx(-117.280, rel=1e-2)  # lon
            assert float(parts[2]) == pytest.approx(33.128, rel=1e-2)  # lat
            assert float(parts[3]) == pytest.approx(
                1000 * FEET_TO_METERS, rel=1e-1
            )  # alt in meters
            assert float(parts[4]) == pytest.approx(90, rel=1e-1)  # track
            assert float(parts[5]) == pytest.approx(
                100 * KNOTS_TO_MS, rel=1e-1
            )  # speed in m/s

    def test_create_xgps_message_heading_normalization(self):
        with patch("socket.socket"):
            sender = EFBSender(sim_name="Test")

            # Test heading > 360
            msg = sender.create_xgps_message(
                lat=0, lon=0, altitude_ft=0, heading=450, speed_kts=0
            )
            parts = msg.split(",")
            track = float(parts[4])
            assert track == pytest.approx(90, abs=1)

    def test_send_broadcast_only(self):
        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender(sim_name="Test", broadcast=True)
            sender.send(
                lat=33.0, lon=-117.0, altitude_ft=5000, heading=90, speed_kts=150
            )

            # Verify sendto was called with broadcast address
            mock_socket.sendto.assert_called_once()
            args = mock_socket.sendto.call_args
            assert args[0][1] == ("<broadcast>", EFB_PORT)

    def test_send_unicast_only(self):
        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender(sim_name="Test", target_ips=["192.168.1.50"])
            sender.send(
                lat=33.0, lon=-117.0, altitude_ft=5000, heading=90, speed_kts=150
            )

            # Verify sendto was called with specific IP
            mock_socket.sendto.assert_called_once()
            args = mock_socket.sendto.call_args
            assert args[0][1] == ("192.168.1.50", EFB_PORT)

    def test_send_broadcast_and_unicast(self):
        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender(
                sim_name="Test",
                broadcast=True,
                target_ips=["192.168.1.50", "192.168.1.51"],
            )
            sender.send(
                lat=33.0, lon=-117.0, altitude_ft=5000, heading=90, speed_kts=150
            )

            # Verify sendto was called 3 times (broadcast + 2 IPs)
            assert mock_socket.sendto.call_count == 3

            # Check destinations
            calls = mock_socket.sendto.call_args_list
            destinations = [call[0][1] for call in calls]
            assert ("<broadcast>", EFB_PORT) in destinations
            assert ("192.168.1.50", EFB_PORT) in destinations
            assert ("192.168.1.51", EFB_PORT) in destinations

    def test_send_returns_true_on_success(self):
        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender(broadcast=True)
            result = sender.send(lat=0, lon=0, altitude_ft=0, heading=0, speed_kts=0)
            assert result is True

    def test_send_returns_false_on_all_failures(self):
        mock_socket = MagicMock()
        mock_socket.sendto.side_effect = Exception("Network error")
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender(broadcast=True)
            result = sender.send(lat=0, lon=0, altitude_ft=0, heading=0, speed_kts=0)
            assert result is False

    def test_close(self):
        mock_socket = MagicMock()
        with patch("socket.socket", return_value=mock_socket):
            sender = EFBSender()
            sender.close()
            mock_socket.close.assert_called_once()
            assert sender._socket is None


class TestBackwardsCompatibility:
    """Test that ForeFlightSender alias still works."""

    def test_foreflight_sender_alias(self):
        assert ForeFlightSender is EFBSender


class TestConversionFactors:
    """Tests for unit conversion factors."""

    def test_feet_to_meters(self):
        # 1 foot = 0.3048 meters
        assert FEET_TO_METERS == pytest.approx(0.3048, rel=1e-4)

    def test_knots_to_ms(self):
        # 1 knot = 0.514444 m/s
        assert KNOTS_TO_MS == pytest.approx(0.514444, rel=1e-4)

    def test_conversion_examples(self):
        # 10000 feet = 3048 meters
        assert 10000 * FEET_TO_METERS == pytest.approx(3048, rel=1e-2)

        # 100 knots = 51.4444 m/s
        assert 100 * KNOTS_TO_MS == pytest.approx(51.4444, rel=1e-2)


class TestParseIpList:
    """Tests for parse_ip_list function."""

    def test_empty_string(self):
        """Should return empty list for empty input."""
        assert parse_ip_list("") == []
        assert parse_ip_list(None) == []

    def test_single_ip(self):
        """Should parse single IP address."""
        result = parse_ip_list("192.168.1.100")
        assert result == ["192.168.1.100"]

    def test_multiple_ips(self):
        """Should parse comma-separated IPs."""
        result = parse_ip_list("192.168.1.100, 192.168.1.101, 192.168.1.102")
        assert result == ["192.168.1.100", "192.168.1.101", "192.168.1.102"]

    def test_ip_range(self):
        """Should expand IP range."""
        result = parse_ip_list("192.168.1.10-192.168.1.13")
        assert result == [
            "192.168.1.10",
            "192.168.1.11",
            "192.168.1.12",
            "192.168.1.13",
        ]

    def test_mixed_ips_and_ranges(self):
        """Should handle mix of IPs and ranges."""
        result = parse_ip_list("192.168.1.5, 192.168.1.10-192.168.1.12, 192.168.1.20")
        assert "192.168.1.5" in result
        assert "192.168.1.10" in result
        assert "192.168.1.11" in result
        assert "192.168.1.12" in result
        assert "192.168.1.20" in result
        assert len(result) == 5

    def test_invalid_range_reversed(self):
        """Should skip reversed range (end < start)."""
        result = parse_ip_list("192.168.1.20-192.168.1.10")
        assert result == []

    def test_invalid_range_format(self):
        """Should skip invalid range format."""
        result = parse_ip_list("192.168.1-192.168.1.10")  # Missing octet
        assert result == []

    def test_whitespace_handling(self):
        """Should handle whitespace around IPs."""
        result = parse_ip_list("  192.168.1.100  ,  192.168.1.101  ")
        assert result == ["192.168.1.100", "192.168.1.101"]

    def test_empty_parts_ignored(self):
        """Should ignore empty parts from extra commas."""
        result = parse_ip_list("192.168.1.100,,192.168.1.101,")
        assert result == ["192.168.1.100", "192.168.1.101"]

    def test_large_range(self):
        """Should handle larger IP ranges."""
        result = parse_ip_list("10.0.0.1-10.0.0.5")
        assert len(result) == 5
        assert result[0] == "10.0.0.1"
        assert result[-1] == "10.0.0.5"

    def test_cross_octet_range(self):
        """Should handle range that crosses octet boundary."""
        result = parse_ip_list("192.168.1.254-192.168.2.2")
        assert len(result) == 5
        assert "192.168.1.254" in result
        assert "192.168.1.255" in result
        assert "192.168.2.0" in result
        assert "192.168.2.1" in result
        assert "192.168.2.2" in result
