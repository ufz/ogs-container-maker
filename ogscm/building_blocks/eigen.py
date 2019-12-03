# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Eigen building block"""

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


class eigen(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm,
            hpccm.templates.tar, hpccm.templates.wget):
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
        super(eigen, self).__init__()

        self.__baseurl = kwargs.get('baseurl',
                                    'http://bitbucket.org/eigen/eigen/get')
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/eigen')
        self.__version = kwargs.get('version', '3.3.4')

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""
        self += comment('Eigen version {}'.format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += generic_cmake(directory='eigen-eigen-*'.format(self.__version),
                              prefix=self.__prefix,
                              url='{0}/{1}.tar.gz'.format(
                                  self.__baseurl, self.__version))
        self += environment(variables={
            'Eigen3_ROOT': self.__prefix,
            'Eigen3_DIR': self.__prefix
        })

        # No runtime
