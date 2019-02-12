# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Package manager Conan building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell


class ccache(object):
    """Package manager Conan building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        self.__cache_dir = kwargs.get('cache_dir', '/opt/cache')
        self.__cache_size = kwargs.get('cache_size', '5G')


    def __str__(self):
        """String representation of the building block"""
        commands = []
        instructions = [comment(__doc__, reformat=False)]
        commands.extend([
            # Create ccache cache dir writable by all users
            'mkdir -p {0} && chmod 777 {0}'.format(self.__cache_dir)
        ])
        instructions.append(packages(ospackages=['ccache']))
        instructions.append(shell(commands=commands))
        instructions.append(environment(variables={
            'CCACHE_DIR': self.__cache_dir,
            'CCACHE_MAXSIZE': self.__cache_size,
            'CCACHE_SLOPPINESS': 'pch_defines,time_macros'
        }))
        instructions.append(label(metadata={
            'ccache.dir': self.__cache_dir,
            'ccache.size': self.__cache_size
        }))

        return '\n'.join(str(x) for x in instructions)

    # No runtime
