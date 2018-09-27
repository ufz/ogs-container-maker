

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import os
import traceback

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.label import label
from hpccm.primitives.raw import raw
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.git import git
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget
from templates.ConfigureCMake import ConfigureCMake
from hpccm.toolchain import toolchain


class ogs(ConfigureCMake, rm, tar, wget):
  """OGS building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    #super(python, self).__init__(**kwargs)
    ConfigureCMake.__init__(self, **kwargs)
    rm.__init__(self, **kwargs)
    tar.__init__(self, **kwargs)
    wget.__init__(self, **kwargs)

    self.__ospackages = []
    self.__prefix = kwargs.get('prefix', '/scif/apps/ogs')
    self.__repo = kwargs.get('repo', 'https://github.com/ufz/ogs')
    self.__branch = kwargs.get('branch', 'master')
    self.configure_opts = kwargs.get('configure_opts', [])
    self.__toolchain = kwargs.get('toolchain', toolchain())

    self.__commands = [] # Filled in by __setup()
    self.__wd = self.__prefix # working directory

    self.__setup()

  def __str__(self):
    """String representation of the building block"""
    instructions = []
    instructions.append(comment(
      'OpenGeoSys build from repo {0}, branch {1}'.format(self.__repo, self.__branch)))
    instructions.append(packages(ospackages=self.__ospackages))
    instructions.append(shell(commands=self.__commands, _app='ogs', _appenv=True))
    instructions.append(runscript(commands=['/scif/apps/ogs/bin/ogs "$@"'], _app='ogs'))
    instructions.append(label(metadata={'REPOSITORY': self.__repo, 'BRANCH': self.__branch}, _app='ogs'))
    instructions.append(raw(singularity='%apptest ogs\n    /scif/apps/ogs/bin/ogs --help'))
    instructions.append(runscript(commands=['/scif/apps/ogs/bin/ogs "$@"'])) # Is also default runscript

    return '\n'.join(str(x) for x in instructions)

  def __setup(self):
    self.__commands.extend([
      git().clone_step(repository=self.__repo,
        branch=self.__branch, path=self.__prefix,  directory='src'),
      "cd {0}/src && git fetch --tags".format(self.__prefix)
    ])
    self.configure_opts = [
      "-G Ninja",
      "-DCMAKE_BUILD_TYPE=Release",
      "-DCMAKE_INSTALL_PREFIX={}".format(self.__prefix),
      "-DOGS_USE_CONAN=ON"
    ]
    if self.__toolchain.CC == 'mpicc':
    #if self.__ompi:
      self.configure_opts.extend([
        "-DOGS_USE_PETSC=ON",
        "-DOGS_CONAN_USE_SYSTEM_OPENMPI=ON"
      ])
    # TODO: cmake_cmd = 'CONAN_SYSREQUIRES_SUDO=0 '
    self
    self.__commands.append(self.configure_step(
      directory='{}/src'.format(self.__prefix),
      build_directory='{}/build'.format(self.__prefix),
      toolchain=self.__toolchain))
    self.__commands.append(self.build_step(target='install'))
    self.__commands.append(self.build_step(target='clean'))

  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
