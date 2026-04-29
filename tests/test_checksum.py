# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_checksum.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for NMEA checksum calculation."""

from backend.nmea.checksum import calculate_checksum, format_sentence


class TestCalculateChecksum:
    """Tests for checksum calculation."""

    def test_gpgga_checksum(self):
        """Verify checksum for known GPGGA sentence."""
        # From Bad Elf docs: $GPGGA,061212,4726.88,N,12218.66,W,1,8,,122.1,M,,*1C
        data = "GPGGA,061212,4726.88,N,12218.66,W,1,8,,122.1,M,,"
        assert calculate_checksum(data) == "1C"

    def test_gprmc_checksum(self):
        """Verify checksum for known GPRMC sentence."""
        # From Bad Elf docs: $GPRMC,061212,A,4726.88,N,12218.66,W,0.0,000.9,250413,,*0E
        data = "GPRMC,061212,A,4726.88,N,12218.66,W,0.0,000.9,250413,,"
        assert calculate_checksum(data) == "0E"

    def test_empty_string(self):
        """Empty string should return 00."""
        assert calculate_checksum("") == "00"

    def test_single_char(self):
        """Single character checksum."""
        # XOR of 'A' (65) = 0x41 = "41"
        assert calculate_checksum("A") == "41"


class TestFormatSentence:
    """Tests for full sentence formatting."""

    def test_format_with_checksum(self):
        """Format should add $ prefix, * and checksum suffix, and CRLF."""
        data = "GPGGA,061212,4726.88,N,12218.66,W,1,8,,122.1,M,,"
        result = format_sentence(data)
        assert result == "$GPGGA,061212,4726.88,N,12218.66,W,1,8,,122.1,M,,*1C\r\n"
