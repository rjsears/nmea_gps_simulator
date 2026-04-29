# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# engine.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""NMEA sentence generation engine."""

from datetime import datetime, timezone
from typing import Optional

from .sentences import GPGGA, GPRMC, GPGLL, GPGSA, GPGSV, GPHDT, GPVTG, GPZDA
from .geodesic import update_position
from .transitions import GradualTransition, HeadingTransition

FEET_TO_METERS = 0.3048


class NmeaEngine:
    """Orchestrates NMEA sentence generation with position updates."""

    REQUIRED_SENTENCES = {"GPGGA", "GPRMC"}
    ALL_SENTENCES = {
        "GPGGA",
        "GPRMC",
        "GPGLL",
        "GPGSA",
        "GPGSV",
        "GPHDT",
        "GPVTG",
        "GPZDA",
    }

    def __init__(
        self,
        lat: float,
        lon: float,
        altitude_ft: float,
        speed_kts: float,
        heading: float,
        enabled_sentences: Optional[set[str]] = None,
        altitude_rate_ft_per_2sec: float = 1000,
        airspeed_rate_kts_per_sec: float = 30,
        heading_rate_deg_per_sec: float = 3,
    ):
        self.lat = lat
        self.lon = lon
        self.altitude_ft = altitude_ft
        self.speed_kts = speed_kts
        self.heading = heading

        self.target_altitude_ft = altitude_ft
        self.target_speed_kts = speed_kts
        self.target_heading = heading

        self.enabled_sentences = (
            enabled_sentences or self.REQUIRED_SENTENCES
        ) | self.REQUIRED_SENTENCES

        self._altitude_trans = GradualTransition(
            rate_per_sec=altitude_rate_ft_per_2sec / 2
        )
        self._speed_trans = GradualTransition(rate_per_sec=airspeed_rate_kts_per_sec)
        self._heading_trans = HeadingTransition(rate_per_sec=heading_rate_deg_per_sec)

    def set_target_altitude(self, altitude_ft: float) -> None:
        self.target_altitude_ft = altitude_ft

    def set_target_speed(self, speed_kts: float) -> None:
        self.target_speed_kts = speed_kts

    def set_target_heading(self, heading: float) -> None:
        self.target_heading = heading % 360

    def update_position(
        self,
        lat: float,
        lon: float,
        altitude_ft: float,
        speed_kts: float,
        heading: float,
    ) -> None:
        """Directly update position values (used in receiver mode)."""
        self.lat = lat
        self.lon = lon
        self.altitude_ft = altitude_ft
        self.speed_kts = speed_kts
        self.heading = heading % 360
        # Also update targets to match
        self.target_altitude_ft = altitude_ft
        self.target_speed_kts = speed_kts
        self.target_heading = heading % 360

    def tick(self, elapsed_sec: float = 1.0) -> None:
        self.lat, self.lon = update_position(
            self.lat, self.lon, self.speed_kts, self.heading, elapsed_sec
        )
        self.altitude_ft = self._altitude_trans.update(
            self.altitude_ft, self.target_altitude_ft, elapsed_sec
        )
        self.speed_kts = self._speed_trans.update(
            self.speed_kts, self.target_speed_kts, elapsed_sec
        )
        self.heading = self._heading_trans.update(
            self.heading, self.target_heading, elapsed_sec
        )

    def generate(self, utc_time: Optional[datetime] = None) -> list[str]:
        if utc_time is None:
            utc_time = datetime.now(timezone.utc)

        # Use CURRENT values (gradual transition) rounded to whole numbers for NMEA output
        altitude_ft_rounded = round(self.altitude_ft)
        speed_kts_rounded = round(self.speed_kts)
        heading_rounded = round(self.heading)
        # Convert 0 heading to 360 (North)
        if heading_rounded == 0:
            heading_rounded = 360

        altitude_m = altitude_ft_rounded * FEET_TO_METERS
        sentences = []

        if "GPGGA" in self.enabled_sentences:
            sentences.append(
                GPGGA(
                    utc_time=utc_time, lat=self.lat, lon=self.lon, altitude_m=altitude_m
                ).to_nmea()
            )

        if "GPRMC" in self.enabled_sentences:
            sentences.append(
                GPRMC(
                    utc_time=utc_time,
                    lat=self.lat,
                    lon=self.lon,
                    speed_kts=speed_kts_rounded,
                    heading=heading_rounded,
                ).to_nmea()
            )

        if "GPGLL" in self.enabled_sentences:
            sentences.append(
                GPGLL(utc_time=utc_time, lat=self.lat, lon=self.lon).to_nmea()
            )

        if "GPGSA" in self.enabled_sentences:
            sentences.append(GPGSA().to_nmea())

        if "GPGSV" in self.enabled_sentences:
            sentences.extend(GPGSV().to_nmea_list())

        if "GPHDT" in self.enabled_sentences:
            sentences.append(GPHDT(heading=heading_rounded).to_nmea())

        if "GPVTG" in self.enabled_sentences:
            sentences.append(
                GPVTG(
                    heading_true=heading_rounded, speed_kts=speed_kts_rounded
                ).to_nmea()
            )

        if "GPZDA" in self.enabled_sentences:
            sentences.append(GPZDA(utc_time=utc_time).to_nmea())

        return sentences

    def get_state(self) -> dict:
        # Round navigation values to whole numbers for display
        heading_val = round(self.heading)
        if heading_val == 0:
            heading_val = 360
        return {
            "lat": self.lat,
            "lon": self.lon,
            "altitude_ft": round(self.altitude_ft),
            "speed_kts": round(self.speed_kts),
            "heading": heading_val,
            "target_altitude_ft": self.target_altitude_ft,
            "target_speed_kts": self.target_speed_kts,
            "target_heading": self.target_heading,
        }
