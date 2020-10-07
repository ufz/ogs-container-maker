# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OSU benchmarks building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
from hpccm.toolchain import toolchain


class osu_benchmarks(
    bb_base,
    hpccm.templates.ConfigureMake,
    hpccm.templates.rm,
    hpccm.templates.tar,
    hpccm.templates.wget,
):
    """OSU benchmarks building block"""

    def __init__(self, **kwargs):
        super(osu_benchmarks, self).__init__()

        self.__ospackages = kwargs.get("ospackages", ["wget", "tar"])
        self.prefix = kwargs.get("prefix", "/usr/local/osu-benchmarks")
        self.__version = kwargs.get("version", "5.4.2")
        self.__toolchain = toolchain(CC="mpicc", CXX="mpicxx")
        self.configure_opts = kwargs.get("configure_opts", [])
        self.__wd = "/var/tmp"  # working directory

        # Filled in by __setup():
        self.__commands = []
        self.__environment_variables = {}
        self.__labels = {}

        self.__setup()

        self.__instructions()

    def __instructions(self):
        self += comment("OSU benchmarks version {}".format(self.__version))
        self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)
        if self.__labels:
            self += label(metadata=self.__labels)

    def __setup(self):
        """Construct the series of shell commands, i.e., fill in
        self.__commands"""

        # Get the source
        directory = "osu-micro-benchmarks-{}".format(self.__version)
        tarball = "{}.tar.gz".format(directory)
        self.__commands.append(
            self.download_step(
                url="http://mvapich.cse.ohio-state.edu/download/mvapich/{}".format(
                    tarball
                ),
                directory=self.__wd,
            )
        )
        self.__commands.append(
            self.untar_step(
                tarball=os.path.join(self.__wd, tarball), directory=self.__wd
            )
        )

        # Configure, build, install
        self.__commands.append(
            self.configure_step(
                directory=os.path.join(self.__wd, directory),
                opts=[
                    "CC={}".format(self.__toolchain.CC),
                    "CXX={}".format(self.__toolchain.CXX),
                ],
            )
        )
        self.__commands.append(self.build_step())
        self.__commands.append(self.install_step())

        # Cleanup
        self.__commands.append(
            self.cleanup_step(
                items=[
                    os.path.join(self.__wd, tarball),
                    os.path.join(self.__wd, directory),
                ]
            )
        )

        # Environment
        libexec_path = "{0}/libexec/osu-micro-benchmarks/mpi".format(self.prefix)
        self.__environment_variables[
            "PATH"
        ] = "{0}/collective:{0}/one-sided:{0}/pt2pt:{0}/startup::$PATH".format(
            libexec_path
        )

        # Labels
        self.__labels["osu.version"] = self.__version

    def runtime(self, _from="0"):
        instructions = []
        instructions.append(comment("OSU benchmarks version {}".format(self.__version)))
        instructions.append(copy(_from=_from, src=self.prefix, dest=self.prefix))
        if self.__environment_variables:
            instructions.append(environment(variables=self.__environment_variables))
        if self.__labels:
            instructions.append(label(metadata=self.__labels))
        return "\n".join(str(x) for x in instructions)
