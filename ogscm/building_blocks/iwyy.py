# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Include-what-you-use building block"""

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


class iwyy(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm,
           hpccm.templates.tar, hpccm.templates.wget):
    """
    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/iwyy`.

    clang_version: The installed clang version. Required!

    # Examples

    ```python
    iwyy(clang_version='5.0')
    ```

    """
    def __init__(self, **kwargs):
        """Initialize building block"""
        super(iwyy, self).__init__()

        self.__baseurl = kwargs.get(
            'baseurl',
            'https://github.com/include-what-you-use/include-what-you-use/'
            'archive'
        )
        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/iwyy')
        self.__clang_version = kwargs.get('clang_version')

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""

        self += comment('Include-what-you-use for clang version {}'.format(
            self.__clang_version))
        self.__ospackages.extend([
            'libncurses5-dev', 'zlib1g-dev',
            'llvm-{}-dev'.format(self.__clang_version),
            'libclang-{}-dev'.format(self.__clang_version)
        ])
        self += packages(ospackages=self.__ospackages)
        self += generic_cmake(
            cmake_opts=[
                '-D IWYU_LLVM_ROOT_PATH=/usr/lib/llvm-{}'.format(
                    self.__clang_version)
            ],
            directory="include-what-you-use-clang_{0}.0".format(
                self.__clang_version),
            prefix=self.__prefix,
            url='{0}/clang_{1}.0.tar.gz'.format(self.__baseurl,
                                                self.__clang_version))
        self += environment(
            variables={'PATH': '{0}/bin:$PATH'.format(self.__prefix)})

        # No runtime
