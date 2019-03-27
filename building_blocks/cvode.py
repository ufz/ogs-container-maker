# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""CVode building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell

class cvode(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm,
            hpccm.templates.tar, hpccm.templates.wget):
    """The `cvode` building block downloads and installs the
    [CVode](https://computation.llnl.gov/projects/sundials/cvode) component.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/cvode`.

    version: The version of CVode source to download.  The default
    value is `2.8.2`. Currently only works for 2.8.2

    """

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(cvode, self).__init__()

        self.__baseurl = kwargs.get('baseurl',
                                    'https://github.com/ufz/cvode/archive')
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/cvode')
        self.__version = kwargs.get('version', '2.8.2')

        self.__commands = [] # Filled in by __setup()
        self.__environment_variables = {} # Filled in by __setup()
        self.__wd = '/var/tmp' # working directory

        # Construct the series of steps to execute
        self.__setup()

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""
        self += comment('CVode version {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)

    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""

        tarball = '{}.tar.gz'.format(self.__version)
        url = '{0}/{1}'.format(self.__baseurl, tarball)

        # Download source from web
        self.__commands.append(self.download_step(url=url,
                                                  directory=self.__wd))
        self.__commands.append(self.untar_step(
            tarball=os.path.join(self.__wd, tarball), directory=self.__wd))

        self.__commands.extend([
            self.configure_step(
            directory='{0}/cvode-{1}'.format(self.__wd, self.__version),
            build_directory='{}/build'.format(self.__wd),
            opts=['-DCMAKE_INSTALL_PREFIX={0}'.format(self.__prefix),
                  '-DEXAMPLES_INSTALL=OFF', '-DBUILD_SHARED_LIBS=OFF',
                  '-DCMAKE_POSITION_INDEPENDENT_CODE=ON']),
        self.build_step(target='install', parallel=self.__parallel)
        ])

        # Set library path
        self.__environment_variables['CVODE_ROOT'] = self.__prefix

        # Cleanup tarball and directories
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, 'build'),
                   os.path.join(self.__wd,
                                'cvode-{}'.format(self.__version))]))

    # No runtime
