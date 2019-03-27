# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""VTK building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import re
import os
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell
from hpccm.toolchain import toolchain


class vtk(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm,
          hpccm.templates.tar, hpccm.templates.wget):
    """The `VTK` building block downloads and installs the
    [VTK](https://vtk.org/) component.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/vtk`.

    version: The version of VTK source to download.  The default
    value is `8.2.0`.

    # Examples

    ```python
    vtk(version='7.1.1')
    ```

    """
    def __init__(self, **kwargs):
        super(vtk, self).__init__()

        self.__cmake_args = kwargs.get('cmake_args', [])
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/vtk')
        self.__shared = kwargs.get('shared', True)
        self.__toolchain = kwargs.get('toolchain', toolchain())
        self.__version = kwargs.get('version', '8.2.0')
        self.__wd = '/var/tmp' # working directory
        match = re.match(r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<revision>\d+)',
                         self.__version)
        short_version = '{0}.{1}'.format(match.groupdict()['major'], match.groupdict()['minor'])
        self.__baseurl = kwargs.get('baseurl',
                                    'https://www.vtk.org/files/release/{0}'.format(short_version))

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}

        self.__setup()

        self.__instructions()

    def __instructions(self):
        self += comment('VTK {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)


    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""

        tarball = 'VTK-{}.tar.gz'.format(self.__version)
        url = '{0}/{1}'.format(self.__baseurl, tarball)

        # Default CMake arguments
        self.__cmake_args.extend([
          '-DCMAKE_INSTALL_PREFIX={0}'.format(self.__prefix),
          '-DCMAKE_BUILD_TYPE=Release'
        ])
        if not self.__shared:
            self.__cmake_args.append('-DBUILD_SHARED_LIBS=OFF')
        if self.__toolchain.CC == 'mpicc':
            self.__cmake_args.extend([
                '-DModule_vtkIOParallelXML=ON',
                '-DModule_vtkParallelMPI=ON'])

        # Download source from web
        self.__commands.append(self.download_step(url=url,
                                                  directory=self.__wd))
        self.__commands.append(self.untar_step(
            tarball=os.path.join(self.__wd, tarball), directory=self.__wd))

        # Configure and build
        self.__commands.extend([
            self.configure_step(
              directory='{0}/VTK-{1}'.format(self.__wd, self.__version),
              build_directory='{}/build'.format(self.__wd),
              opts=self.__cmake_args,
              toolchain=self.__toolchain),
            self.build_step(target='install', parallel=self.__parallel)
        ])

        # Set library path
        self.__environment_variables['VTK_ROOT'] = '{}'.format(self.__prefix)
        libpath = os.path.join(self.__prefix, 'lib')
        if self.__shared:
            self.__environment_variables['LD_LIBRARY_PATH'] = '{}:$LD_LIBRARY_PATH'.format(libpath)

        # Cleanup tarball and directory
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, 'build'),
                   os.path.join(self.__wd,
                                'VTK-{}'.format(self.__version))]))

    def runtime(self, _from='0'):
        if not self.__shared:
            return str(comment('VTK (empty)'))
        instructions = []
        instructions.append(comment('VTK {}'.format(self.__version)))
        instructions.append(copy(_from=_from, src=self.__prefix,
                                 dest=self.__prefix))

        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        return '\n'.join(str(x) for x in instructions)
