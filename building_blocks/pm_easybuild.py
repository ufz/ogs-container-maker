# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Package manager easybuild building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from building_blocks.lmod import lmod
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.templates.git import git


class pm_easybuild():
  """Package manager easybuild building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""

    # Trouble getting MRO with kwargs working correctly, so just call
    # the parent class constructors manually for now.
    #super(python, self).__init__(**kwargs)

    self.__ospackages = kwargs.get('ospackages', [])

    self.__commands = [] # Filled in by __setup()
    self.__wd = '/var/tmp' # working directory

    self.__setup()

  def __str__(self):
    """String representation of the building block"""
    instructions = [comment(__doc__, reformat=False)]
    instructions.append(packages(ospackages=self.__ospackages))
    instructions.append(lmod(version='7.8.6'))
    instructions.append(shell(commands=self.__commands))
    # Without the FORCE_UNSAFE_CONFIGURE env var some spack package
    # installations may fail due to running as root.
    instructions.append(environment(variables={
      'MODULEPATH': '/opt/easybuild/modules/all:/home/easybuild/.local/easybuild/modules/all:$MODULEPATH',
      'FORCE_UNSAFE_CONFIGURE': '1'
    }))
    instructions.append(label(metadata={'PACKAGE_MANAGER': 'easybuild'}))

    return '\n'.join(str(x) for x in instructions)

  def __setup(self):
    self.__ospackages.extend([
      'build-essential', 'bzip2', 'file', 'git', 'gzip',
      'libssl-dev', 'libtool', 'make', 'openssh-client',
      'patch', 'python-pip', 'python-setuptools', 'rsh-client',
      'tar', 'wget', 'unzip', 'xz-utils'
    ])
    self.__commands.extend([
      'useradd -m easybuild',
      'mkdir -p /opt/easybuild',
      'chown easybuild:easybuild /opt/easybuild',
      'easy_install easybuild==3.7.0'
    ])

  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)

  def install(self, ospackages=None, configs=None):
    instructions = []
    if ospackages:
      instructions.append(packages(ospackages=ospackages))
    commands = []
    for config in configs:
      commands.append(
        'runuser easybuild -l -c "eb {} -r --installpath /opt/easybuild"'.format(config)
      )
    instructions.append(shell(commands=commands))

    return '\n'.join(str(x) for x in instructions)
