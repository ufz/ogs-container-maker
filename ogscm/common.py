from enum import Enum


class package_manager(Enum):
    """Supported container types"""

    OFF = 0
    CONAN = 1
    EASYBUILD = 3
    GUIX = 4
    SYSTEM = 5
