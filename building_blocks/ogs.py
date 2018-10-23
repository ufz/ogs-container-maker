

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import os
import traceback

import config
import hpccm.config
from config import package_manager
from hpccm.building_blocks.packages import packages
from hpccm.common import container_type
from hpccm.primitives.comment import comment
from hpccm.primitives.label import label
from hpccm.primitives.raw import raw
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget
from hpccm.toolchain import toolchain


class ogs(CMakeBuild):
  """OGS building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    #super(python, self).__init__(**kwargs)
    CMakeBuild.__init__(self, **kwargs)

    self.__ospackages = []
    self.__app = kwargs.get('app', 'ogs')
    self.__prefix = kwargs.get('prefix', '/scif/apps/{}'.format(self.__app))
    self.__repo = kwargs.get('repo', 'https://github.com/ufz/ogs')
    self.__branch = kwargs.get('branch', 'master')
    self.configure_opts = kwargs.get('configure_opts', [])
    self.__toolchain = kwargs.get('toolchain', toolchain())
    self.__skip_lfs = kwargs.get('skip_lfs', False)

    self.__commands = [] # Filled in by __setup()

    self.__setup()

  def __str__(self):
    """String representation of the building block"""
    ogs_binary = '{}/bin/ogs'.format(self.__prefix)
    instructions = []
    instructions.append(comment(
      'OpenGeoSys build from repo {0}, branch {1}'.format(self.__repo, self.__branch)))
    instructions.append(packages(ospackages=self.__ospackages))
    instructions.append(shell(commands=self.__commands, _app=self.__app, _appenv=True))
    instructions.append(runscript(commands=['{} "$@"'.format(ogs_binary)], _app='ogs'))
    instructions.append(label(metadata={'REPOSITORY': self.__repo, 'BRANCH': self.__branch}, _app='ogs'))
    instructions.append(raw(singularity='%apptest {}\n    {} --help'.format(self.__app, ogs_binary)))
    if hpccm.config.g_ctype == container_type.SINGULARITY:
      # Is also default runscript in singularity
      instructions.append(runscript(commands=['{} "$@"'.format(ogs_binary)]))

    return '\n'.join(str(x) for x in instructions)

  def __setup(self):
    spack = config.g_package_manager == config.package_manager.SPACK
    conan = config.g_package_manager == config.package_manager.CONAN
    self.__commands.extend([
        '{}git clone --depth=1 --branch {} {} src'.format(
            'GIT_LFS_SKIP_SMUDGE=1 ' if self.__skip_lfs else '',
            self.__branch, self.__repo),
        "(cd src && git fetch --tags)"
    ])
    self.configure_opts.extend([
      "-G Ninja",
      "-DCMAKE_BUILD_TYPE=Release",
      "-DCMAKE_INSTALL_PREFIX={}".format(self.__prefix),
    ])
    if self.__skip_lfs:
      self.configure_opts.append('-DOGS_BUILD_TESTS=OFF')
    if spack:
      self.__commands.extend([
        '. /opt/spack/share/spack/setup-env.sh',
        'spack load boost',
        'spack load eigen',
        'spack load vtk'
      ])
    if self.__toolchain.CC == 'mpicc':
      if spack:
        self.__commands.append('spack load petsc')
      self.configure_opts.append("-DOGS_USE_PETSC=ON")
      if conan:
        self.configure_opts.append("-DOGS_CONAN_USE_SYSTEM_OPENMPI=ON")

    self.__commands.append(self.configure_step(
      directory='{}/src'.format(self.__prefix),
      build_directory='{}/build'.format(self.__prefix),
      opts=self.configure_opts,
      toolchain=self.__toolchain))
    self.__commands.append(self.build_step(target='install'))
    self.__commands.append(self.build_step(target='clean'))

  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
