# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# checksum.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""NMEA checksum calculation."""


def calculate_checksum(data: str) -> str:
    """Calculate NMEA checksum for data string.

    Performs XOR operation on all bytes and returns
    two-character uppercase hexadecimal string.

    Args:
        data: NMEA sentence data (without $ prefix and * suffix)

    Returns:
        Two-character uppercase hex checksum (e.g., "1C")
    """
    checksum = 0
    for char in data:
        checksum ^= ord(char)
    return f"{checksum:02X}"


def format_sentence(data: str) -> str:
    """Format complete NMEA sentence with checksum.

    Args:
        data: NMEA sentence data (without $ prefix and * suffix)

    Returns:
        Complete sentence: $<data>*<checksum>\r\n
    """
    checksum = calculate_checksum(data)
    return f"${data}*{checksum}\r\n"
