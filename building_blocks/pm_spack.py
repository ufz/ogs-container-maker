# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Package manager spack building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.templates.git import git


class pm_spack(object):
    """Package manager spack building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        # super(python, self).__init__(**kwargs)

        self.__ospackages = kwargs.get('ospackages', [])

        self.__commands = []  # Filled in by __setup()
        self.__wd = '/var/tmp'  # working directory

        self.__setup()

    def __str__(self):
        """String representation of the building block"""
        instructions = [comment(__doc__, reformat=False),
                        packages(ospackages=self.__ospackages),
                        packages(yum=['xz'], apt=['xz-utils']),
                        environment(variables={
                            'PATH': '/opt/spack/bin:$PATH',
                            'FORCE_UNSAFE_CONFIGURE': '1'
                        }), shell(commands=self.__commands),
                        label(metadata={'org.opengeosys.pm': 'spack'})]
        # Without the FORCE_UNSAFE_CONFIGURE env var some spack package
        # installations may fail due to running as root.

        return '\n'.join(str(x) for x in instructions)

    def __setup(self):
        self.__ospackages.extend(['patch'])
        self.__commands.extend([
            git().clone_step(repository='https://github.com/spack/spack',
                             branch='develop', path='/opt'),
            'spack bootstrap',
            # TODO: There is no init system inside the container -> files are
            #       not sourced!
            'ln -s /opt/spack/share/spack/setup-env.sh /etc/profile.d/spack.sh',
            'ln -s /opt/spack/share/spack/spack-completion.bash /etc/profile.d',
            'spack clean --all'
        ])

    def runtime(self, _from='0'):
        """Install the runtime from a full build in a previous stage.  In this
           case there is no difference between the runtime and the
           full build."""
        return str(self)
