"""Common stuff used by multiple parts of OGS Container Maker"""

from enum import Enum

class package_manager(Enum):
  """Supported container types"""
  CONAN = 1
  SPACK = 2
  EASYBUILD = 3
  GUIX = 4
  SYSTEM = 5

  @staticmethod
  def set(pm):
    if pm == 'conan':
      g_package_manager = package_manager.CONAN
    elif pm == 'spack':
      g_package_manager = package_manager.SPACK
    elif pm == 'easybuild':
      g_package_manager = package_manager.EASYBUILD
    elif pm == 'guix':
      g_package_manager = package_manager.GUIX
    elif pm == 'system':
      g_package_manager = package_manager.SYSTEM
    else:
      raise ValueError('Invalid package manager!')

    return g_package_manager

# Global variables
g_package_manager = package_manager.SYSTEM
