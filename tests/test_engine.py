# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_engine.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for NMEA engine."""

from backend.nmea.engine import NmeaEngine

FEET_TO_METERS = 0.3048


class TestNmeaEngine:
    def test_generate_required_sentences(self):
        engine = NmeaEngine(
            lat=33.1283,
            lon=-117.2803,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
        )
        sentences = engine.generate()
        sentence_str = "".join(sentences)
        assert "$GPGGA," in sentence_str
        assert "$GPRMC," in sentence_str

    def test_generate_optional_sentences(self):
        engine = NmeaEngine(
            lat=33.1283,
            lon=-117.2803,
            altitude_ft=5000,
            speed_kts=120,
            heading=270,
            enabled_sentences={"GPGGA", "GPRMC", "GPHDT", "GPVTG"},
        )
        sentences = engine.generate()
        sentence_str = "".join(sentences)
        assert "$GPHDT," in sentence_str
        assert "$GPVTG," in sentence_str
        assert "$GPGLL," not in sentence_str

    def test_altitude_feet_to_meters(self):
        engine = NmeaEngine(
            lat=33.1283,
            lon=-117.2803,
            altitude_ft=1000,
            speed_kts=0,
            heading=0,
        )
        sentences = engine.generate()
        for sentence in sentences:
            if sentence.startswith("$GPGGA,"):
                assert ",304." in sentence or ",305." in sentence
                break

    def test_update_position(self):
        engine = NmeaEngine(
            lat=33.0,
            lon=-117.0,
            altitude_ft=5000,
            speed_kts=60,
            heading=90,
        )
        original_lon = engine.lon
        engine.tick(elapsed_sec=60)
        assert engine.lon > original_lon

    def test_gradual_heading_change(self):
        engine = NmeaEngine(
            lat=33.0,
            lon=-117.0,
            altitude_ft=0,
            speed_kts=0,
            heading=0,
            heading_rate_deg_per_sec=3,
        )
        engine.set_target_heading(90)
        engine.tick(elapsed_sec=1)
        assert engine.heading == 3
        assert engine.target_heading == 90
