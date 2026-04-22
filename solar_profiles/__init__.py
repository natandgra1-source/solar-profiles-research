"""
solar-profiles
==============
Access PVWatts-equivalent solar generation profiles for every country in the world.
January 1st, 24-hour local-time resolution, 4 kW DC system standard parameters.
"""

from .core import SolarProfiles

__version__ = "1.0.0"
__all__ = ["SolarProfiles"]
