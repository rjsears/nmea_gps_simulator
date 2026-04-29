# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# sentences.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""NMEA sentence classes."""

from datetime import datetime
from dataclasses import dataclass

from .checksum import format_sentence


def decimal_to_nmea_lat(decimal_degrees: float) -> tuple[str, str]:
    """Convert decimal degrees latitude to NMEA format.

    Args:
        decimal_degrees: Latitude in decimal degrees (positive=N, negative=S)

    Returns:
        Tuple of (DDMM.MMM, N/S)
    """
    direction = "N" if decimal_degrees >= 0 else "S"
    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes = (decimal_degrees - degrees) * 60
    return f"{degrees:02d}{minutes:06.3f}", direction


def decimal_to_nmea_lon(decimal_degrees: float) -> tuple[str, str]:
    """Convert decimal degrees longitude to NMEA format.

    Args:
        decimal_degrees: Longitude in decimal degrees (positive=E, negative=W)

    Returns:
        Tuple of (DDDMM.MMM, E/W)
    """
    direction = "E" if decimal_degrees >= 0 else "W"
    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes = (decimal_degrees - degrees) * 60
    return f"{degrees:03d}{minutes:06.3f}", direction


@dataclass
class GPGGA:
    """GPGGA - Global Positioning System Fix Data.

    Required sentence for Bad Elf.
    """

    utc_time: datetime
    lat: float
    lon: float
    altitude_m: float
    fix_quality: int = 1
    satellites: int = 8

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        time_str = self.utc_time.strftime("%H%M%S")
        lat_str, lat_dir = decimal_to_nmea_lat(self.lat)
        lon_str, lon_dir = decimal_to_nmea_lon(self.lon)

        data = (
            f"GPGGA,{time_str},{lat_str},{lat_dir},"
            f"{lon_str},{lon_dir},{self.fix_quality},{self.satellites},,"
            f"{self.altitude_m:.1f},M,,"
        )
        return format_sentence(data)


@dataclass
class GPRMC:
    """GPRMC - Recommended Minimum Specific GPS/Transit Data.

    Required sentence for Bad Elf.
    """

    utc_time: datetime
    lat: float
    lon: float
    speed_kts: float
    heading: float
    status: str = "A"

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        time_str = self.utc_time.strftime("%H%M%S")
        date_str = self.utc_time.strftime("%d%m%y")
        lat_str, lat_dir = decimal_to_nmea_lat(self.lat)
        lon_str, lon_dir = decimal_to_nmea_lon(self.lon)

        data = (
            f"GPRMC,{time_str},{self.status},{lat_str},{lat_dir},"
            f"{lon_str},{lon_dir},{self.speed_kts:.1f},{self.heading:.1f},"
            f"{date_str},,"
        )
        return format_sentence(data)


@dataclass
class GPGLL:
    """GPGLL - Geographic Position, Latitude/Longitude."""

    utc_time: datetime
    lat: float
    lon: float
    status: str = "A"
    mode: str = "A"

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        time_str = self.utc_time.strftime("%H%M%S")
        lat_str, lat_dir = decimal_to_nmea_lat(self.lat)
        lon_str, lon_dir = decimal_to_nmea_lon(self.lon)

        data = (
            f"GPGLL,{lat_str},{lat_dir},{lon_str},{lon_dir},"
            f"{time_str}.000,{self.status},{self.mode}"
        )
        return format_sentence(data)


@dataclass
class GPGSA:
    """GPGSA - GPS DOP and Active Satellites."""

    mode: str = "A"
    fix_type: int = 3
    pdop: float = 1.56
    hdop: float = 0.92
    vdop: float = 1.25

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        sats = ",".join([f"{i:02d}" for i in [22, 11, 27, 1, 3, 2, 10, 21, 19]])
        sat_fields = sats + "," * 3  # Pad to 12 fields
        data = f"GPGSA,{self.mode},{self.fix_type},{sat_fields}{self.pdop:.2f},{self.hdop:.2f},{self.vdop:.2f}"
        return format_sentence(data)


@dataclass
class GPGSV:
    """GPGSV - GPS Satellites in View."""

    total_satellites: int = 15

    def to_nmea_list(self) -> list[str]:
        """Generate list of NMEA sentence strings."""
        import random

        random.seed(42)
        sentences = []
        total_msgs = (self.total_satellites + 3) // 4

        for msg_num in range(1, total_msgs + 1):
            start_sat = (msg_num - 1) * 4
            end_sat = min(start_sat + 4, self.total_satellites)

            sat_data = []
            for i in range(start_sat, end_sat):
                prn = (i % 32) + 1
                elevation = random.randint(10, 90)
                azimuth = random.randint(0, 359)
                snr = random.randint(30, 99)
                sat_data.append(f"{prn:02d},{elevation},{azimuth:03d},{snr:02d}")

            data = f"GPGSV,{total_msgs},{msg_num},{self.total_satellites}," + ",".join(
                sat_data
            )
            sentences.append(format_sentence(data))
        return sentences


@dataclass
class GPHDT:
    """GPHDT - True Heading."""

    heading: float

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        data = f"GPHDT,{self.heading:.1f},T"
        return format_sentence(data)


@dataclass
class GPVTG:
    """GPVTG - Track Made Good and Ground Speed."""

    heading_true: float
    speed_kts: float

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        speed_kmh = self.speed_kts * 1.852
        data = f"GPVTG,{self.heading_true:.1f},T,,M,{self.speed_kts:.1f},N,{speed_kmh:.1f},K"
        return format_sentence(data)


@dataclass
class GPZDA:
    """GPZDA - Date and Time."""

    utc_time: datetime

    def to_nmea(self) -> str:
        """Generate NMEA sentence string."""
        time_str = self.utc_time.strftime("%H%M%S")
        day = self.utc_time.day
        month = self.utc_time.month
        year = self.utc_time.year
        data = f"GPZDA,{time_str}.000,{day:02d},{month:02d},{year},0,0"
        return format_sentence(data)
