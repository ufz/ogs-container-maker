# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""PETSc building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.toolchain import toolchain
from hpccm.building_blocks.generic_autotools import generic_autotools


class petsc(bb_base, hpccm.templates.ConfigureMake, hpccm.templates.ldconfig,
            hpccm.templates.rm, hpccm.templates.tar, hpccm.templates.wget):
    """The `PETSc` building block downloads and installs the
    [VTK](https://vtk.org/) component.

    Requires python3.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/petsc`.

    version: The version of PETSc source to download.  The default
    value is `3.8.4`.

    # Examples

    ```python
    petsc(version='3.8.1')
    ```

    """
    def __init__(self, **kwargs):
        super(petsc, self).__init__(**kwargs)

        self.__ospackages = kwargs.get('ospackages', [])
        self.parallel = 1
        self.__prefix = kwargs.get('prefix', '/usr/local/petsc')
        self.__toolchain = toolchain(CC='mpicc', CXX='mpicxx')
        self.configure_opts = kwargs.get('configure_opts', [])
        self.__version = kwargs.get('version', '3.8.4')
        self.__wd = '/var/tmp'  # working directory
        self.__baseurl = kwargs.get(
            'baseurl', 'http://ftp.mcs.anl.gov/pub/petsc/release-snapshots')
        self.__environment_variables = {}

        self.__instructions()

    def __instructions(self):
        self += comment('PETSc {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += generic_autotools(
            directory='petsc-{}'.format(self.__version),
            preconfigure=["sed -i -- 's/python/python3/g' configure"],
            prefix=self.__prefix,
            toolchain=self.__toolchain,
            url='{0}/petsc-lite-{1}.tar.gz'.format(self.__baseurl,
                                                   self.__version),
            configure_opts=[
                'CC={}'.format(self.__toolchain.CC),
                'CXX={}'.format(self.__toolchain.CXX), '--CFLAGS=\'-O3\'',
                '--CXXFLAGS=\'-O3\'', '--FFLAGS=\'-O3\'',
                '--with-debugging=no', '--with-fc=0',
                '--download-f2cblaslapack=1'
            ])
        self.__environment_variables['PETSC_DIR'] = self.__prefix
        # Set library path
        libpath = os.path.join(self.__prefix, 'lib')
        if self.ldconfig:
            self += shell(commands=[self.ldcache_step(directory=libpath)])
        else:
            self.__environment_variables[
                'LD_LIBRARY_PATH'] = '{}:$LD_LIBRARY_PATH'.format(libpath)

        self += environment(variables=self.__environment_variables)
        self += label(metadata={'petsc.version': self.__version})

    def runtime(self, _from='0'):
        instructions = []
        instructions.append(comment('PETSc {}'.format(self.__version)))
        instructions.append(
            copy(_from=_from, src=self.__prefix, dest=self.__prefix))

        if self.ldconfig:
            libpath = os.path.join(self.__prefix, 'lib')
            instructions.append(
                shell(commands=[self.ldcache_step(directory=libpath)]))

        instructions.append(
            environment(variables=self.__environment_variables))
        instructions.append(label(metadata={'petsc.version': self.__version}))
        return '\n'.join(str(x) for x in instructions)

