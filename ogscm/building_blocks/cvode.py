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
from hpccm.building_blocks.generic_cmake import generic_cmake


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

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""
        self += comment('CVode version {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += generic_cmake(cmake_opts=[
            '-D CMAKE_INSTALL_PREFIX={0}'.format(self.__prefix),
            '-D EXAMPLES_INSTALL=OFF', '-D BUILD_SHARED_LIBS=OFF',
            '-D CMAKE_POSITION_INDEPENDENT_CODE=ON'
        ],
                              directory='cvode-{}'.format(self.__version),
                              prefix=self.__prefix,
                              url='{0}/{1}.tar.gz'.format(
                                  self.__baseurl, self.__version))
        self += environment(variables={'CVODE_ROOT': self.__prefix})

        # No runtime
