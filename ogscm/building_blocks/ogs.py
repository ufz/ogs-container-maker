# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import re

import hpccm.templates.rm

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
from hpccm.toolchain import toolchain

import ogscm
from ogscm.config import package_manager


class ogs(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm):
    """OGS building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(ogs, self).__init__(**kwargs)

        self.__cmake_args = kwargs.get('cmake_args', [])
        self.__ospackages = []
        self.__parallel = kwargs.get('parallel', 4)
        self.__prefix = kwargs.get('prefix', '/usr/local/ogs')
        self.__remove_dev = kwargs.get('remove_dev', False)
        self.__remove_build = kwargs.get('remove_build', False)
        self.__remove_source = kwargs.get('remove_source', False)
        self.__shared = kwargs.get('shared', True)
        self.__skip_lfs = kwargs.get('skip_lfs', False)
        self.__toolchain = kwargs.get('toolchain', toolchain())
        self.__version = kwargs.get('version', 'ufz/ogs@master')
        m = re.search('(.+/.*)@(.*)', self.__version)
        self.__repo = m.group(1)
        self.__branch = m.group(2)

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}
        self.__labels = {}

        self.__setup()

        # Fill in container instructions
        self.__instructions()

    def __instructions(self):
        self += comment('OpenGeoSys build from repo {0}, branch {1}'.format(
                        self.__repo, self.__branch))
        self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        self += runscript(commands=['ogs'])

        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)
        if self.__labels:
            self += label(metadata=self.__labels)


    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""
        conan = ogscm.config.g_package_manager == package_manager.CONAN

        # Get the source
        self.__commands.extend([
            'mkdir -p {0} && cd {0}'.format(self.__prefix),
            # TODO: --depth=1 --> ogs --version does not work
            '{}git clone --branch {} https://github.com/{} src'.format(
                'GIT_LFS_SKIP_SMUDGE=1 ' if self.__skip_lfs else '',
                self.__branch, self.__repo),
            "(cd src && git fetch --tags)"
        ])

        # Default CMake arguments
        self.__cmake_args.extend([
            "-G Ninja",
            "-DCMAKE_INSTALL_PREFIX={}".format(self.__prefix),
            "-DCMAKE_BUILD_TYPE=Release",
        ])

        self.__cmake_args.append('-DBUILD_SHARED_LIBS={}'.format(
            'ON' if self.__shared else 'OFF'
        ))
        if self.__skip_lfs:
            self.__cmake_args.append('-DBUILD_TESTING=OFF')
        if self.__toolchain.CC == 'mpicc':
            self.__cmake_args.append("-DOGS_USE_PETSC=ON")
            if conan == True:
                self.__cmake_args.append("-DOGS_CONAN_USE_SYSTEM_OPENMPI=ON")
        if conan == False:
            self.__cmake_args.append('-DOGS_USE_CONAN=OFF')

        # Configure and build
        self.__commands.append(self.configure_step(
            directory='{}/src'.format(self.__prefix),
            build_directory='{}/build'.format(self.__prefix),
            opts=self.__cmake_args,
            toolchain=self.__toolchain))
        self.__commands.append(self.build_step(
            target='install', parallel=self.__parallel))

        # Cleanup
        if self.__remove_build:
            # Remove whole src and build directories
            self.__commands.append(self.cleanup_step(
                items=[os.path.join(self.__prefix, 'build')]
            ))
        else:
            # Just run the clean-target
            self.__commands.append(self.build_step(target='clean'))
        if self.__remove_source:
            # Remove whole src and build directories
            self.__commands.append(self.cleanup_step(
                items=[os.path.join(self.__prefix, 'src')]
            ))

        # Environment
        self.__environment_variables['PATH'] = '{0}/bin:$PATH'.format(
            self.__prefix)

        # Labels
        self.__labels['version'] = self.__version
        self.__labels['cmake_args'] = '\'' + ' '.join(self.__cmake_args) + '\''

    def runtime(self, _from='0'):
        instructions = [
            comment('OpenGeoSys build from repo {0}, branch {1}'.format(
                self.__repo, self.__branch)),
            copy(_from=_from, src=self.__prefix,
                 dest=self.__prefix)
        ]
        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))
        return '\n'.join(str(x) for x in instructions)
