# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Package manager Conan building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hpccm.config

from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell


class pm_conan():
    """Package manager Conan building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        # super(python, self).__init__(**kwargs)

    def __str__(self):
        """String representation of the building block"""
        commands = []
        instructions = [comment(__doc__, reformat=False)]
        conan_version = "1.8.4"
        if hpccm.config.g_linux_distro == linux_distro.CENTOS:
            commands.append('easy_install-3.4 pip')
            # Conan 1.7 requires newer Python than 3.4
            conan_version = "1.6.1"
        commands.extend([
            "python3 -m pip install --upgrade pip",
            "python3 -m pip install conan=={0}".format(conan_version),
            # Create Conan cache dir writable by all users
            'mkdir -p /opt/conan',
            'chmod 777 /opt/conan'
        ])
        instructions.append(shell(commands=commands))
        instructions.append(environment(variables={
            'CONAN_USER_HOME': '/opt/conan'
        }))
        instructions.append(label(metadata={
            'org.opengeosys.pm': 'conan',
            'org.opengeosys.pm.conan.version': conan_version,
            'org.opengeosys.pm.conan.user_home': '/opt/conan'
        }))

        return '\n'.join(str(x) for x in instructions)

    def runtime(self, _from='0'):
        """Install the runtime from a full build in a previous stage.  In this
           case there is no difference between the runtime and the
           full build."""
        return str(self)
