

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OSU benchmarks building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget
from hpccm.toolchain import toolchain


class osu_benchmarks(ConfigureMake, rm, tar, wget):
    """OSU benchmarks building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        ConfigureMake.__init__(self, **kwargs)
        rm.__init__(self, **kwargs)
        tar.__init__(self, **kwargs)
        wget.__init__(self, **kwargs)

        self.__ospackages = kwargs.get('ospackages', ['wget', 'tar'])
        self.prefix = kwargs.get('prefix', '/usr/local/osu-benchmarks')
        self.__version = kwargs.get('version', '5.4.2')
        self.__toolchain = toolchain(CC='mpicc', CXX='mpicxx')
        self.configure_opts = kwargs.get('configure_opts', [])
        self.__wd = '/var/tmp'  # working directory

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}
        self.__labels = {}

        self.__setup()


    def __str__(self):
        """String representation of the building block"""
        instructions = []
        instructions.append(comment('OSU benchmarks version {}'.format(self.__version)))
        instructions.append(packages(ospackages=self.__ospackages))
        instructions.append(shell(commands=self.__commands))
        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))

        return '\n'.join(str(x) for x in instructions)


    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""

        # Get the source
        directory = 'osu-micro-benchmarks-{}'.format(self.__version)
        tarball = '{}.tar.gz'.format(directory)
        self.__commands.append(self.download_step(
            url="http://mvapich.cse.ohio-state.edu/download/mvapich/{}".format(
                tarball),
            directory=self.__wd))
        self.__commands.append(self.untar_step(
            tarball=os.path.join(self.__wd, tarball), directory=self.__wd))

        # Configure, build, install
        self.__commands.append(self.configure_step(
            directory=os.path.join(self.__wd, directory),
            toolchain=self.__toolchain))
        self.__commands.append(self.build_step())
        self.__commands.append(self.install_step())

        # Cleanup
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, directory)]))

        # Environment
        self.__environment_variables['PATH'] = '{0}/bin:$PATH'.format(self.prefix)

        # Labels
        self.__labels['osu.version'] = self.__version

    def runtime(self, _from='0'):
        instructions = []
        instructions.append(comment('OSU benchmarks version {}'.format(self.__version)))
        instructions.append(copy(_from=_from, src=self.prefix,
                                dest=self.prefix))
        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))
        return '\n'.join(str(x) for x in instructions)
