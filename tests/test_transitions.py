# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# test_transitions.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Tests for gradual value transitions."""

from backend.nmea.transitions import GradualTransition, HeadingTransition


class TestGradualTransition:
    def test_no_change_when_at_target(self):
        trans = GradualTransition(rate_per_sec=10)
        result = trans.update(current=100, target=100, elapsed_sec=1.0)
        assert result == 100

    def test_increase(self):
        trans = GradualTransition(rate_per_sec=30)
        result = trans.update(current=0, target=100, elapsed_sec=1.0)
        assert result == 30

    def test_decrease(self):
        trans = GradualTransition(rate_per_sec=30)
        result = trans.update(current=100, target=0, elapsed_sec=1.0)
        assert result == 70

    def test_clamp_to_target(self):
        trans = GradualTransition(rate_per_sec=100)
        result = trans.update(current=0, target=50, elapsed_sec=1.0)
        assert result == 50

    def test_partial_second(self):
        trans = GradualTransition(rate_per_sec=60)
        result = trans.update(current=0, target=100, elapsed_sec=0.5)
        assert result == 30


class TestHeadingTransition:
    def test_shortest_path_clockwise(self):
        trans = HeadingTransition(rate_per_sec=10)
        result = trans.update(current=350, target=10, elapsed_sec=1.0)
        # Should go 350 -> 0 -> 10, not 350 -> 340 -> ... -> 10
        assert result == 360 or result == 0

    def test_shortest_path_counterclockwise(self):
        trans = HeadingTransition(rate_per_sec=10)
        result = trans.update(current=10, target=350, elapsed_sec=1.0)
        assert result == 0 or result == 360

    def test_wrap_around_360(self):
        trans = HeadingTransition(rate_per_sec=10)
        result = trans.update(current=355, target=5, elapsed_sec=1.0)
        assert 0 <= result < 360
