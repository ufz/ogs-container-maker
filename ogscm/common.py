from enum import Enum

class package_manager(Enum):
  """Supported container types"""
  CONAN = 1
  SPACK = 2
  EASYBUILD = 3
  GUIX = 4
  SYSTEM = 5
