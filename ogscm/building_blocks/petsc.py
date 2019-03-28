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


class petsc(bb_base, hpccm.templates.ConfigureMake, hpccm.templates.rm,
            hpccm.templates.tar, hpccm.templates.wget):
    """The `PETSc` building block downloads and installs the
    [VTK](https://vtk.org/) component.

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
        super(petsc, self).__init__()

        self.__ospackages = kwargs.get('ospackages', [])
        self.parallel = 1
        self.prefix = kwargs.get('prefix', '/usr/local/petsc')
        self.__toolchain = toolchain(CC='mpicc', CXX='mpicxx')
        self.configure_opts = kwargs.get('configure_opts', [])
        self.__version = kwargs.get('version', '3.8.4')
        self.__wd = '/var/tmp' # working directory
        self.__baseurl = kwargs.get('baseurl', 'http://ftp.mcs.anl.gov/pub/petsc/release-snapshots')

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}
        self.__labels = {}

        self.__setup()

        self.__instructions()

    def __instructions(self):
        self += comment('PETSc {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)
        if self.__labels:
            self += label(metadata=self.__labels)


    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""

        # Get the source
        directory = 'petsc-{}'.format(self.__version)
        tarball = 'petsc-lite-{}.tar.gz'.format(self.__version)
        url = '{0}/{1}'.format(self.__baseurl, tarball)

        self.__commands.append(self.download_step(url=url,
                                                  directory=self.__wd))
        self.__commands.append(self.untar_step(
            tarball=os.path.join(self.__wd, tarball), directory=self.__wd))

        # Default configure opts
        self.configure_opts.extend([
            'CC={}'.format(self.__toolchain.CC),
            'CXX={}'.format(self.__toolchain.CXX),
            '--CFLAGS=\'-O3\'',
            '--CXXFLAGS=\'-O3\'',
            '--FFLAGS=\'-O3\'',
            '--with-debugging=no',
            '--with-fc=0',
            '--download-f2cblaslapack=1'
        ])

        # Configure, build, install
        self.__commands.append(self.configure_step(
            directory=os.path.join(self.__wd, directory)))
        self.__commands.append(self.build_step())
        self.__commands.append(self.install_step())

        # Cleanup tarball and directory
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, directory)]))

        # Environment
        self.__environment_variables['PETSC_DIR'] = '{}'.format(self.prefix)
        libpath = os.path.join(self.prefix, 'lib')
        self.__environment_variables['LD_LIBRARY_PATH'] = '{}:$LD_LIBRARY_PATH'.format(libpath)

        # Labels
        self.__labels['petsc.version'] = self.__version

    def runtime(self, _from='0'):
        instructions = []
        instructions.append(comment('PETSc {}'.format(self.__version)))
        instructions.append(copy(_from=_from, src=self.prefix,
                                 dest=self.prefix))

        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))
        return '\n'.join(str(x) for x in instructions)
