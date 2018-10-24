

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OSU benchmarks building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget
from hpccm.toolchain import toolchain

from building_blocks.scif import scif
from building_blocks.scif import scif_app


class osu_benchmarks(ConfigureMake, rm, tar, wget):
  """OSU benchmarks building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    #super(python, self).__init__(**kwargs)
    ConfigureMake.__init__(self, **kwargs)
    rm.__init__(self, **kwargs)
    tar.__init__(self, **kwargs)
    wget.__init__(self, **kwargs)

    self.__ospackages = kwargs.get('ospackages', ['wget', 'tar'])
    self.__prefix = kwargs.get('prefix', '/scif/apps/osu')
    self.__version = kwargs.get('version', '5.4.2')
    self.toolchain = toolchain(CC='mpicc', CXX='mpicxx')
    self.configure_opts = kwargs.get('configure_opts', [])

    self.__commands = [] # Filled in by __setup()
    self.__wd = '/var/tmp' # working directory

    self.__setup()

  def __str__(self):
    """String representation of the building block"""
    instructions = [comment('OSE benchmarks version {}'.format(self.__version))]
    instructions.append(packages(ospackages=self.__ospackages))

    scif_osu = scif()
    scif_osu.install(scif_app(
      name = 'osu',
      labels = {'osu.version': self.__version},
      install = self.__commands
    ))
    instructions.extend(scif_osu.instructions)

    return '\n'.join(str(x) for x in instructions)

  def __setup(self):
    directory = 'osu-micro-benchmarks-{}'.format(self.__version)
    tarball = '{}.tar.gz'.format(directory)
    self.__commands.append(self.download_step(
      url="http://mvapich.cse.ohio-state.edu/download/mvapich/{}".format(tarball),
      directory=self.__wd))
    self.__commands.append(self.untar_step(
      tarball=os.path.join(self.__wd, tarball), directory=self.__wd))
    self.__commands.append(self.configure_step(
      directory=os.path.join(self.__wd, directory),
      toolchain=self.toolchain))
    self.__commands.append(self.build_step())
    self.__commands.append(self.install_step())

    self.__commands.append(self.cleanup_step(
      items=[os.path.join(self.__wd, tarball),
             os.path.join(self.__wd, directory)]))

  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
