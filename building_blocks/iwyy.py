# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Include-what-you-use building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell
from hpccm.templates.CMakeBuild import CMakeBuild
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget

class iwyy(CMakeBuild, rm, tar, wget):
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

        CMakeBuild.__init__(self, **kwargs)
        rm.__init__(self, **kwargs)
        tar.__init__(self, **kwargs)
        wget.__init__(self, **kwargs)

        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/iwyy')
        self.__clang_version = kwargs.get('clang_version')

        self.__commands = []  # Filled in by __setup()
        self.__environment_variables = {}  # Filled in by __setup()
        self.__wd = '/var/tmp'  # working directory

        # Construct the series of steps to execute
        self.__setup()

    def __str__(self):
        """String representation of the building block"""

        instructions = []
        instructions.append(comment(
            'Include-what-you-use for clang version {}'.format(
                self.__clang_version)))
        instructions.append(packages(ospackages=self.__ospackages))
        instructions.append(shell(commands=self.__commands))
        if self.__environment_variables:
            instructions.append(environment(
                variables=self.__environment_variables))
        return '\n'.join(str(x) for x in instructions)

    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
           self.__commands"""

        self.__ospackages.extend([
            'libncurses5-dev',
            'zlib1g-dev',
            'llvm-{}-dev'.format(self.__clang_version),
            'libclang-{}-dev'.format(self.__clang_version)
        ])

        baseurl = "https://github.com/include-what-you-use/include-what-you-use/archive"
        tarball = 'clang_{}.tar.gz'.format(self.__clang_version)
        url = '{0}/{1}'.format(baseurl, tarball)
        directory = "include-what-you-use-clang_{0}".format(self.__clang_version)

        # Download source from web
        self.__commands.append(self.download_step(url=url,
                                                  directory=self.__wd))
        self.__commands.append(self.untar_step(
            tarball=os.path.join(self.__wd, tarball), directory=self.__wd))

        self.__commands.extend([
            self.configure_step(
                directory='{0}/{1}'.format(self.__wd, directory),
                build_directory='{}/build'.format(self.__wd),
                opts=[
                    '-DCMAKE_INSTALL_PREFIX={}'.format(self.__prefix),
                    '-DIWYU_LLVM_ROOT_PATH=/usr/lib/llvm-{}'.format(
                        self.__clang_version)]),
            self.build_step(target='install', parallel=self.__parallel)
        ])

        self.__environment_variables['PATH'] = '{}/bin:$PATH'.format(self.__prefix)

        # Cleanup tarball and directories
        self.__commands.append(self.cleanup_step(
            items=[os.path.join(self.__wd, tarball),
                   os.path.join(self.__wd, 'build'),
                   os.path.join(self.__wd, directory)]))

        # cleanup packages?
        # self.__commands.append(
        #     'apt remove -y {}'.format(' '.join(self.__ospackages))
        # )

    # no runtime
