# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""OGS building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import re
import subprocess

import hpccm.templates.rm

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
from hpccm.toolchain import toolchain

import ogscm
from ogscm.config import package_manager


class ogs(bb_base, hpccm.templates.CMakeBuild, hpccm.templates.rm):
    """OGS building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(ogs, self).__init__(**kwargs)

        self.__cmake_args = kwargs.get("cmake_args", [])
        self.__cmake_preset = kwargs.get("cmake_preset", "release")
        self.__cmake_preset_file = kwargs.get("cmake_preset_file", None)
        self.__ospackages = []
        self.__parallel = kwargs.get("parallel", 4)
        self.__prefix = kwargs.get("prefix", "/usr/local/ogs")
        self.__remove_dev = kwargs.get("remove_dev", False)
        self.__remove_build = kwargs.get("remove_build", False)
        self.__remove_source = kwargs.get("remove_source", False)
        self.__shared = kwargs.get("shared", True)
        self.__skip_clone = kwargs.get("skip_clone", False)
        self.__toolchain = kwargs.get("toolchain", toolchain())
        self.__repo = kwargs.get("repo", "ufz/ogs.git")
        self.__branch = kwargs.get("branch", "master")
        self.__commit = kwargs.get("commit")
        self.__git_version = kwargs.get("git_version")
        self.__shell_args = kwargs.get("mount_args", "")
        self.__run_ctest = kwargs.get("run_ctest", False)

        if self.__repo == "local":
            self.__skip_clone = True
            self.__remove_source = False
            self.__shell_args += " --mount=type=bind,target={}/src,rw".format(
                self.__prefix
            )

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}
        self.__labels = {}

        self.__setup()

        # Fill in container instructions
        self.__instructions()

    def __instructions(self):
        self += comment(
            "OpenGeoSys build from repo {0}, branch {1}".format(
                self.__repo, self.__branch
            )
        )
        self += packages(ospackages=self.__ospackages)
        self += shell(
            commands=self.__commands,
            _arguments=self.__shell_args,
        )

        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)
        if self.__labels:
            self += label(metadata=self.__labels)

    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
        self.__commands"""
        # Get the source
        if self.__skip_clone:
            self.__cmake_args.append("-DOGS_VERSION={}".format(self.__git_version))
        else:
            self.__commands.extend(
                [
                    "mkdir -p {0} && cd {0}".format(self.__prefix),
                    "git clone --filter=blob:limit=100k --branch {} https://gitlab.opengeosys.org/{} src".format(
                        self.__branch, self.__repo
                    ),
                ]
            )
            if self.__commit:
                self.__commands.append(
                    "(cd src && git reset --hard {})".format(self.__commit)
                )
            self.__commands.append("(cd src && git fetch --tags)")
        if self.__cmake_preset_file:
            f = open(self.__cmake_preset_file, "r")
            contents = f.read()
            contents = contents.replace("\n", "\\n")
            self.__commands.append(
                f"echo '{contents}' >> /usr/local/ogs/src/CMakeUserPresets.json"
            )

        # Default CMake arguments
        self.__cmake_args.extend(
            [
                "-G Ninja",
                "-DCMAKE_INSTALL_PREFIX={}".format(self.__prefix),
                "-DOGS_CPU_ARCHITECTURE=OFF",  # optimization handled via --cpu-target argument
                "-DOGS_INSTALL_EXTERNAL_DEPENDENCIES=ON",
            ]
        )

        self.__cmake_args.append(
            "-DBUILD_SHARED_LIBS={}".format("ON" if self.__shared else "OFF")
        )
        if self.__toolchain.CC == "mpicc":
            self.__cmake_args.append("-DOGS_USE_PETSC=ON")

        build_directory = "{}/build".format(self.__prefix)
        self.__cmake_args.extend(
            [f"--preset={self.__cmake_preset}", "-B", build_directory]
        )

        # Configure and build
        self.__commands.append(
            self.configure_step(
                directory="{}/src".format(self.__prefix),
                build_directory=build_directory,
                opts=self.__cmake_args,
                toolchain=self.__toolchain,
            )
        )

        self.__commands.append(
            self.build_step(target="install", parallel=self.__parallel)
        )

        # ctest
        if self.__run_ctest:
            self.__commands.append(self.build_step(target="ctest"))

        # Cleanup
        if self.__remove_build:
            self.__commands.append(
                self.cleanup_step(items=[os.path.join(self.__prefix, "build")])
            )
        else:
            # Just run the clean-target
            self.__commands.append(self.build_step(target="clean"))
        if self.__remove_source:
            self.__commands.append(
                self.cleanup_step(items=[os.path.join(self.__prefix, "src")])
            )

        # Environment
        self.__environment_variables["PATH"] = "{0}/bin:$PATH".format(self.__prefix)

        # Labels
        if self.__repo == "local":
            self.__labels["version"] = self.__git_version
        else:
            self.__labels["version"] = "'{0}@{1} ({2})'".format(
                self.__repo, self.__branch, self.__commit
            )
        self.__labels["cmake_args"] = "'" + " ".join(self.__cmake_args) + "'"

    def runtime(self, _from="0"):
        instructions = [
            comment(
                "OpenGeoSys build from repo {0}, branch {1}".format(
                    self.__repo, self.__branch
                )
            ),
            copy(_from=_from, src=self.__prefix, dest=self.__prefix),
        ]
        if self.__environment_variables:
            instructions.append(environment(variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))
        return "\n".join(str(x) for x in instructions)
