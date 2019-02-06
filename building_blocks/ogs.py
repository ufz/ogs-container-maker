# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.toolchain import toolchain
import base
import re


class ogs(CMakeBuild):
    """OGS building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        # super(python, self).__init__(**kwargs)
        CMakeBuild.__init__(self, **kwargs)

        self.__version = kwargs.get('version', 'ufz/ogs@master')
        m = re.search('(.+/.*)@(.*)', self.__version)
        self.__repo = m.group(1)
        self.__branch = m.group(2)

        self.__app = kwargs.get('app', 'ogs')
        self.__cmake_args = kwargs.get('cmake_args', '')
        self.__ospackages = []
        self.__parallel = kwargs.get('parallel', 4)
        self.__prefix = kwargs.get(
            'prefix', '/scif/apps/{}'.format(self.__app))
        self.__remove_dev = kwargs.get('remove_dev', False)
        self.__skip_lfs = kwargs.get('skip_lfs', False)
        self.__toolchain = kwargs.get('toolchain', toolchain())
        self.configure_opts = kwargs.get('configure_opts', [])

        self.__commands = []  # Filled in by __setup()

        self.__setup()

    def __str__(self):
        """String representation of the building block"""
        instructions = [comment(
            'OpenGeoSys build from repo {0}, branch {1}'.format(self.__repo,
                                                                self.__branch)
        ), packages(ospackages=self.__ospackages)]

        instructions.extend([
            shell(commands=self.__commands),
            environment(variables={'PATH': '/scif/apps/ogs/bin:$PATH'}),
            label(metadata={
                'org.opengeosys.version': self.__version,
                'org.opengeosys.configure_opts': '\'' +
                ' '.join(self.configure_opts) + '\''
            })
        ])

        return '\n'.join(str(x) for x in instructions)

    def __setup(self):
        spack = base.config.g_package_manager == base.config.package_manager.SPACK
        conan = base.config.g_package_manager == base.config.package_manager.CONAN
        system = base.config.g_package_manager == base.config.package_manager.SYSTEM
        self.__commands.extend([
            'mkdir -p {0} && cd {0}'.format(self.__prefix),
            # TODO: --depth=1 --> ogs --version does not work
            '{}git clone --branch {} https://github.com/{} src'.format(
                'GIT_LFS_SKIP_SMUDGE=1 ' if self.__skip_lfs else '',
                self.__branch, self.__repo),
            "(cd src && git fetch --tags)"
        ])
        self.configure_opts.extend([
            "-G Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX={}".format(self.__prefix),
        ])
        if self.__skip_lfs:
            self.configure_opts.append('-DOGS_BUILD_TESTS=OFF')
        if spack:
            self.__commands.extend([
                '. /opt/spack/share/spack/setup-env.sh',
                'spack load boost',
                'spack load eigen',
                'spack load vtk'
            ])
        if self.__toolchain.CC == 'mpicc':
            if spack:
                self.__commands.append('spack load petsc')
            self.configure_opts.append("-DOGS_USE_PETSC=ON")
            if conan:
                self.configure_opts.append("-DOGS_CONAN_USE_SYSTEM_OPENMPI=ON")
        self.configure_opts.append(self.__cmake_args)
        self.__commands.append(self.configure_step(
            directory='{}/src'.format(self.__prefix),
            build_directory='{}/build'.format(self.__prefix),
            opts=self.configure_opts,
            toolchain=self.__toolchain))
        self.__commands.append(self.build_step(
            target='install', parallel=self.__parallel))
        if self.__remove_dev:
            # Remove whole src and build directories
            self.__commands.append(
                'cd {} && rm -r src build'.format(self.__prefix))
        else:
            # Just run the clean-target
            self.__commands.append(self.build_step(target='clean'))

    def runtime(self, _from='0'):
        instructions = []
        instructions.append(comment(
            'OpenGeoSys build from repo {0}, branch {1}'.format(self.__repo,
                                                                self.__branch)))
        instructions.append(copy(_from=_from, src=self.__prefix,
                                dest=self.__prefix))
        instructions.append(environment(variables={'PATH': '/scif/apps/ogs/bin:$PATH'}))
        return '\n'.join(str(x) for x in instructions)
