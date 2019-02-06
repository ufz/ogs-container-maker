# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Eigen building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import re
import os

import hpccm.config

from hpccm.building_blocks.packages import packages
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget

class eigen(CMakeBuild, rm, tar, wget):
    """The `eigen` building block downloads and installs the
    [Eigen](http://eigen.tuxfamily.org) component.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/eigen`.

    version: The version of Eigen source to download.  The default
    value is `3.3.4`.

    # Examples

    ```python
    eigen(version='3.2.9')
    ```

    """

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        #super(boost, self).__init__(**kwargs)
        CMakeBuild.__init__(self, **kwargs)
        rm.__init__(self, **kwargs)
        tar.__init__(self, **kwargs)
        wget.__init__(self, **kwargs)

        self.__baseurl = kwargs.get('baseurl',
                                    'http://bitbucket.org/eigen/eigen/get')
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/eigen')
        self.__version = kwargs.get('version', '3.3.4')

        self.__commands = [] # Filled in by __setup()
        self.__environment_variables = {} # Filled in by __setup()
        self.__wd = '/var/tmp' # working directory

        # Construct the series of steps to execute
        self.__setup()

    def __str__(self):
        """String representation of the building block"""

        instructions = []
        instructions.append(comment(
            'Eigen version {}'.format(self.__version)))
        instructions.append(packages(ospackages=self.__ospackages))
        instructions.append(shell(commands=self.__commands))
        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        return '\n'.join(str(x) for x in instructions)

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
        self.__commands.append('mv {0}/eigen-* {0}/eigen-{1}'.format(self.__wd, self.__version))

        self.__commands.extend([
            self.configure_step(
            directory='{0}/eigen-{1}'.format(self.__wd, self.__version),
            build_directory='{}/build'.format(self.__wd),
            opts=['-DCMAKE_INSTALL_PREFIX={0}'.format(self.__prefix)]),
        self.build_step(target='install', parallel=self.__parallel)
        ])

        # Set library path
        self.__environment_variables['Eigen3_ROOT'] = '{}'.format(self.__prefix)
        self.__environment_variables['Eigen3_DIR'] = '{}'.format(self.__prefix)

        # Cleanup tarball and directories
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, 'build'),
                   os.path.join(self.__wd,
                                'eigen-{}'.format(self.__version))]))

    # def runtime(self, _from='0'):
        # """Generate the set of instructions to install the runtime specific
        # components from a build in a previous stage.
        # """
        # instructions = []
        # instructions.append(comment('Eigen'))
        # instructions.append(copy(_from=_from, src=self.__prefix,
                                #  dest=self.__prefix))
#
        # if self.__environment_variables:
            # instructions.append(environment(
                # variables=self.__environment_variables))
        # return '\n'.join(str(x) for x in instructions)
