# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
# __init__.py
#
# Part of the "NMEA GPS Simulator" suite
# Version 1.0.0 - April 10th, 2026
#
# Richard J. Sears
# richardjsears@protonmail.com
# https://github.com/rjsears
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=

"""Network communication modules."""

from .sender import NetworkSender
from .receiver import NetworkReceiver, ReceiverState, parse_gps_packet

__all__ = ["NetworkSender", "NetworkReceiver", "ReceiverState", "parse_gps_packet"]
