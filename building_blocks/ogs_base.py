
# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS base building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import hpccm.config

from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.python import python
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget


class ogs_base(ConfigureMake, rm, tar, wget):
  """OGS base building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    # super(python, self).__init__(**kwargs)
    ConfigureMake.__init__(self, **kwargs)
    rm.__init__(self, **kwargs)
    tar.__init__(self, **kwargs)
    wget.__init__(self, **kwargs)

    self.__ospackages = kwargs.get('ospackages', [])

    self.__commands = [] # Filled in by __setup()
    self.__wd = '/var/tmp' # working directory

    self.__setup()

  def __str__(self):
    """String representation of the building block"""
    instructions = [comment(__doc__, reformat=False)]
    dist = 'deb'
    instructions.extend([
      python(),
      packages(
        apt=['python3-setuptools', 'python3-pip', 'python3-dev', 'python-dev'],
        yum=['python34-setuptools', 'python34-dev', 'python-dev'])
    ])

    if hpccm.config.g_linux_distro == linux_distro.CENTOS:
      dist = 'rpm'
    instructions.append(shell(commands=[
        "curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.{0}.sh | bash".format(dist)
      ]))
    instructions.append(packages(ospackages=self.__ospackages,
      apt_ppas=['ppa:git-core/ppa'], epel=True))

    instructions.append(shell(commands=self.__commands))

    return '\n'.join(str(x) for x in instructions)

  def __setup(self):
    self.__ospackages.extend(['git', 'git-lfs', 'make', 'ninja-build', 'doxygen'])

    if hpccm.config.g_ctype == hpccm.container_type.SINGULARITY:
      self.__ospackages.append('locales')
      self.__commands.extend(['echo "LC_ALL=en_US.UTF-8" >> /etc/environment',
                              'echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen',
                              'echo "LANG=en_US.UTF-8" > /etc/locale.conf',
                              'locale-gen en_US.UTF-8'])

    self.__commands.append('git lfs install')

    # Install CMake to /usr/local
    self.__commands.extend([
      self.download_step(
        url='https://cmake.org/files/v3.12/cmake-3.12.2-Linux-x86_64.tar.gz',
        directory=self.__wd),
      self.untar_step(
        tarball=os.path.join(self.__wd, 'cmake-3.12.2-Linux-x86_64.tar.gz'),
        directory='/usr/local',
        args='--strip-components=1')
    ])

    # Common directories
    self.__commands.append('mkdir -p /apps /scratch /lustre /work /projects')

  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
