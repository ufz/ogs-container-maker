

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Jenkins Node building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import os
import hpccm.config

from hpccm.building_blocks.gnu import gnu
from hpccm.building_blocks.packages import packages
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.primitives.user import user
from hpccm.primitives.workdir import workdir
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget
from hpccm.toolchain import toolchain


class jenkins_node(rm, tar, wget):
  """Jenkins Node building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    #super(python, self).__init__(**kwargs)
    ConfigureMake.__init__(self, **kwargs)
    rm.__init__(self, **kwargs)
    tar.__init__(self, **kwargs)
    wget.__init__(self, **kwargs)

    self.__commands = [] # Filled in by __setup()
    self.__wd = '/var/tmp' # working directory


  def __str__(self):
    """String representation of the building block"""
    ccache_dir = '/home/jenkins/cache/ccache'
    instructions = []
    instructions.extend([
      comment('Jenkins node'),
      # For Doxygen diagrams and bibtex references
      packages(ospackages=['graphviz', 'biber', 'texlive-binaries', 'sudo']),
      shell(commands=[
        'adduser --uid 500 --disabled-password --gecos "" jenkins',
        'echo "jenkins ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers',
        'echo "jenkins:jenkins" | chpasswd'
      ]),
      user(user='jenkins'),
      workdir(directory='/home/jenkins'),
      shell(commands=[
        "mkdir -p {0}".format(ccache_dir),
        'conan user'
      ]),
      environment(variables={
        'CCACHE_DIR': ccache_dir,
        'CCACHE_MAXSIZE': '15G',
        'CCACHE_SLOPPINESS': 'pch_defines,time_macros'
      })
    ])
    logging.warning("Changed user to jenkins!")

    return '\n'.join(str(x) for x in instructions)


  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
