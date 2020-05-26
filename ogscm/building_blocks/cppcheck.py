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
from hpccm.building_blocks.generic_cmake import generic_cmake


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

        self.__baseurl = kwargs.get(
            'baseurl', 'https://github.com/danmar/cppcheck/archive')
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/cppcheck')
        self.__version = kwargs.get('version', '809a769c690d8ab6fef293e41a29c8490512866e')

        self.__instructions()

    def __instructions(self):
        self += comment('cppcheck version {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += generic_cmake(cmake_opts=['-D CMAKE_BUILD_TYPE=Release'],
                              directory='cppcheck-{}'.format(self.__version),
                              prefix=self.__prefix,
                              url='{0}/{1}.tar.gz'.format(
                                  self.__baseurl, self.__version))
        self += environment(
            variables={'PATH': '{0}/bin:$PATH'.format(self.__prefix)})

        # No runtime
