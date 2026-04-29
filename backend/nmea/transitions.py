# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# transitions.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Gradual value transition logic."""

from dataclasses import dataclass


@dataclass
class GradualTransition:
    """Handles gradual transitions between values."""

    rate_per_sec: float

    def update(self, current: float, target: float, elapsed_sec: float) -> float:
        if current == target:
            return current

        max_change = self.rate_per_sec * elapsed_sec
        diff = target - current

        if abs(diff) <= max_change:
            return target

        if diff > 0:
            return current + max_change
        else:
            return current - max_change


@dataclass
class HeadingTransition:
    """Handles gradual heading transitions with wrap-around."""

    rate_per_sec: float

    def update(self, current: float, target: float, elapsed_sec: float) -> float:
        current = current % 360
        target = target % 360

        if current == target:
            return current

        max_change = self.rate_per_sec * elapsed_sec

        clockwise = (target - current) % 360
        counterclockwise = (current - target) % 360

        if clockwise <= counterclockwise:
            if clockwise <= max_change:
                return target
            new_heading = current + max_change
        else:
            if counterclockwise <= max_change:
                return target
            new_heading = current - max_change

        return new_heading % 360
