from enum import Enum


class package_manager(Enum):
    """Supported container types"""

    OFF = 0
    EASYBUILD = 3
    GUIX = 4
    SYSTEM = 5
