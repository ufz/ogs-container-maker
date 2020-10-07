# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""paraview building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import re
import os
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.generic_cmake import generic_cmake
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.toolchain import toolchain
from hpccm.primitives.shell import shell
from hpccm.common import linux_distro


class paraview(
    bb_base,
    hpccm.templates.CMakeBuild,
    hpccm.templates.ldconfig,
    hpccm.templates.rm,
    hpccm.templates.tar,
    hpccm.templates.wget,
):
    """The `paraview` building block downloads and installs the
    [paraview](https://paraview.org/) component.

    # Parameters

    prefix: The top level installation location.  The default value
    is `/usr/local/paraview`.

    version: The version of paraview source to download.  The default
    value is `master`.

    # Examples

    ```python
    paraview()
    ```

    """

    def __init__(self, **kwargs):
        super(paraview, self).__init__(**kwargs)

        self.__cmake_args = kwargs.get("cmake_args", [])
        self.__edition = kwargs.get("edition", "CANONICAL")
        self.__ospackages = kwargs.get("ospackages", [])
        self.__parallel = kwargs.get("parallel", "$(nproc)")
        self.__prefix = kwargs.get("prefix", "/usr/local/paraview")
        self.__shared = kwargs.get("shared", True)
        self.__toolchain = kwargs.get("toolchain", toolchain())
        self.__version = kwargs.get("version", "master")
        self.__modules = kwargs.get("modules", [])

        # TODO:
        if False:
            match = re.match(
                r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<revision>\d+)", self.__version
            )
            short_version = "{0}.{1}".format(
                match.groupdict()["major"], match.groupdict()["minor"]
            )
            self.__baseurl = kwargs.get(
                "baseurl",
                "https://www.paraview.org/files/release/{0}".format(short_version),
            )
        self.__environment_variables = {}

        self.__instructions()

    def __instructions(self):
        self += comment("paraview {}".format(self.__version))

        if hpccm.config.g_linux_distro == linux_distro.CENTOS:
            dist = "rpm"
            self += shell(
                commands=[
                    "wget https://github.com/ninja-build/ninja/releases/download/v1.10.0/ninja-linux.zip",
                    "unzip ninja-linux.zip",
                    "mv ninja /usr/local/bin",
                    "rm ninja-linux.zip",
                ]
            )
        else:
            self.__ospackages.extend(["ninja-build"])

        self.__cmake_args.extend(
            [
                "-G Ninja",
                "-DCMAKE_BUILD_TYPE=Release",
                "-DPARAVIEW_BUILD_EDITION={}".format(self.__edition),
            ]
        )
        if not self.__shared:
            self.__cmake_args.append("-DBUILD_SHARED_LIBS=OFF")
        if self.__toolchain.CC == "mpicc":
            self.__cmake_args.append("-DPARAVIEW_USE_MPI=ON")
        for module in self.__modules:
            self.__cmake_args.append("-DVTK_MODULE_ENABLE_{}=YES".format(module))

        # TODO: Install dependencies for rendering editions (ospackages)

        self += generic_cmake(
            branch=self.__version,
            cmake_opts=self.__cmake_args,
            prefix=self.__prefix,
            toolchain=self.__toolchain,
            recursive=True,
            repository="https://gitlab.kitware.com/paraview/paraview.git",
        )
        self.__environment_variables["ParaView_DIR"] = self.__prefix
        # Set library path
        if self.__shared:
            libpath = os.path.join(self.__prefix, "lib")
            if hpccm.config.g_linux_distro == linux_distro.CENTOS:
                libpath += "64"
            if self.ldconfig:
                self += shell(commands=[self.ldcache_step(directory=libpath)])
            else:
                self.__environment_variables[
                    "LD_LIBRARY_PATH"
                ] = "{}:$LD_LIBRARY_PATH".format(libpath)

        self += environment(variables=self.__environment_variables)

    def runtime(self, _from="0"):
        if not self.__shared:
            return str(comment("ParaView (empty)"))
        instructions = []
        instructions.append(comment("ParaView {}".format(self.__version)))
        instructions.append(copy(_from=_from, src=self.__prefix, dest=self.__prefix))
        if self.ldconfig:
            libpath = os.path.join(self.__prefix, "lib")
            if hpccm.config.g_linux_distro == linux_distro.CENTOS:
                libpath += "64"
            instructions.append(shell(commands=[self.ldcache_step(directory=libpath)]))

        instructions.append(environment(variables=self.__environment_variables))
        return "\n".join(str(x) for x in instructions)
