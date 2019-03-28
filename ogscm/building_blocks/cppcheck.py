# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""cppcheck building block"""

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


class cppcheck(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm,
               hpccm.templates.tar, hpccm.templates.wget):
    """The `cvode` building block downloads and installs the
    [cppcheck](https://computation.llnl.gov/projects/sundials/cvode) component.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/cppcheck`.

    version: The version of cppcheck source to download.  The default
    value is `1.83`.
    """

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(cppcheck, self).__init__()

        self.__baseurl = kwargs.get('baseurl',
                                    'https://github.com/danmar/cppcheck/archive')
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/cppcheck')
        self.__version = kwargs.get('version', '1.87')

        self.__commands = [] # Filled in by __setup()
        self.__environment_variables = {} # Filled in by __setup()
        self.__wd = '/var/tmp' # working directory

        # Construct the series of steps to execute
        self.__setup()

        self.__instructions()

    def __instructions(self):
        self += comment('cppcheck version {}'.format(self.__version))
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
            directory='{0}/cppcheck-{1}'.format(self.__wd, self.__version),
            build_directory='{}/build'.format(self.__wd),
            opts=['-DCMAKE_INSTALL_PREFIX={0}'.format(self.__prefix),
                '-DCMAKE_BUILD_TYPE=RELEASE']),
        self.build_step(target='install', parallel=self.__parallel)
        ])

        self.__environment_variables['PATH'] = '{0}/bin:$PATH'.format(self.__prefix)

        # Cleanup tarball and directories
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, 'build'),
                   os.path.join(self.__wd,
                                'cppcheck-{}'.format(self.__version))]))

    # No runtime
