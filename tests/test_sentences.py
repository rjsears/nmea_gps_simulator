# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_sentences.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for NMEA sentence classes."""

from datetime import datetime, timezone
from backend.nmea.sentences import GPGGA, GPGLL, GPHDT, GPRMC, GPVTG, GPZDA


class TestGPGGA:
    """Tests for GPGGA sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPGGA sentence."""
        gpgga = GPGGA(
            utc_time=datetime(2026, 4, 9, 6, 12, 12, tzinfo=timezone.utc),
            lat=47.448,
            lon=-122.311,
            altitude_m=37.2,
        )
        sentence = gpgga.to_nmea()

        assert sentence.startswith("$GPGGA,")
        assert sentence.endswith("\r\n")
        assert ",061212," in sentence
        assert ",1,8,," in sentence  # Quality=1, Sats=8, HDOP blank

    def test_latitude_formatting(self):
        """Latitude should be in DDMM.MMM format."""
        gpgga = GPGGA(
            utc_time=datetime(2026, 4, 9, 12, 0, 0, tzinfo=timezone.utc),
            lat=33.1283,
            lon=-117.2803,
            altitude_m=0,
        )
        sentence = gpgga.to_nmea()
        # 33.1283 degrees = 33 degrees + 7.698 minutes = 3307.698
        assert "3307." in sentence
        assert ",N," in sentence


class TestGPRMC:
    """Tests for GPRMC sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPRMC sentence."""
        gprmc = GPRMC(
            utc_time=datetime(2026, 4, 9, 6, 12, 12, tzinfo=timezone.utc),
            lat=47.448,
            lon=-122.311,
            speed_kts=120.3,
            heading=39.2,
        )
        sentence = gprmc.to_nmea()

        assert sentence.startswith("$GPRMC,")
        assert sentence.endswith("\r\n")
        assert ",061212," in sentence
        assert ",A," in sentence  # Valid status
        assert ",090426," in sentence  # Date DDMMYY


class TestGPGLL:
    """Tests for GPGLL sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPGLL sentence."""
        gpgll = GPGLL(
            utc_time=datetime(2026, 4, 9, 17, 31, 24, tzinfo=timezone.utc),
            lat=54.5,
            lon=19.350483,
        )
        sentence = gpgll.to_nmea()
        assert sentence.startswith("$GPGLL,")
        assert ",A,A*" in sentence


class TestGPHDT:
    """Tests for GPHDT sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPHDT sentence."""
        gphdt = GPHDT(heading=90.0)
        sentence = gphdt.to_nmea()
        assert sentence.startswith("$GPHDT,")
        assert ",90.0,T*" in sentence


class TestGPVTG:
    """Tests for GPVTG sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPVTG sentence."""
        gpvtg = GPVTG(heading_true=90.0, speed_kts=10.5)
        sentence = gpvtg.to_nmea()
        assert sentence.startswith("$GPVTG,")
        assert ",90.0,T," in sentence
        assert ",10.5,N," in sentence


class TestGPZDA:
    """Tests for GPZDA sentence generation."""

    def test_basic_sentence(self):
        """Generate basic GPZDA sentence."""
        gpzda = GPZDA(utc_time=datetime(2021, 11, 5, 17, 31, 24, tzinfo=timezone.utc))
        sentence = gpzda.to_nmea()
        assert sentence.startswith("$GPZDA,")
        assert ",05,11,2021," in sentence
