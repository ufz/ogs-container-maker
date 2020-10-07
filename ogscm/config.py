"""Common stuff used by multiple parts of OGS Container Maker"""

from __future__ import absolute_import

import sys

from ogscm.common import package_manager

g_package_manager = package_manager.SYSTEM


def set_package_manager(pm):
    this = sys.modules[__name__]

    if pm == "conan":
        this.g_package_manager = package_manager.CONAN
    elif pm == "easybuild":
        this.g_package_manager = package_manager.EASYBUILD
    elif pm == "guix":
        this.g_package_manager = package_manager.GUIX
    elif pm == "system":
        this.g_package_manager = package_manager.SYSTEM
    elif pm == "off":
        this.g_package_manager = package_manager.OFF
    else:
        RuntimeError("Invalid package manager!")
