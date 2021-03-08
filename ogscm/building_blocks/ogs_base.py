# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""OGS base building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hpccm.config

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.pip import pip
from hpccm.building_blocks.python import python
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.shell import shell
from hpccm.primitives.environment import environment


class ogs_base(bb_base):
    """OGS base building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(ogs_base, self).__init__()

        self.__ospackages = kwargs.get("ospackages", [])

        self.__commands = []  # Filled in by __setup()
        self.__wd = "/var/tmp"  # working directory

        self.__setup()

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""
        self += comment(__doc__, reformat=False)
        self += python(devel=True, python2=False)
        self += pip(pip="pip3", packages=["virtualenv", "pre-commit", "cmake-format"])
        self += packages(
            ospackages=self.__ospackages, apt_ppas=["ppa:git-core/ppa"], epel=True
        )
        self += shell(commands=self.__commands)
        self += environment(
            variables={
                "CMAKE_GENERATOR": "Ninja",
                "PATH": "/usr/local/poetry/bin:$PATH",
            }
        )

    def __setup(self):
        self.__ospackages.extend(["git"])

        dist = "deb"
        if hpccm.config.g_linux_distro == linux_distro.CENTOS:
            dist = "rpm"
            self.__commands.extend(
                [
                    "wget https://github.com/ninja-build/ninja/releases/download/v1.10.0/ninja-linux.zip",
                    "unzip ninja-linux.zip",
                    "mv ninja /usr/local/bin",
                    "rm ninja-linux.zip",
                ]
            )
        else:
            self.__ospackages.extend(["ninja-build"])

        if hpccm.config.g_ctype == hpccm.container_type.SINGULARITY:
            self.__ospackages.append("locales")
            self.__commands.extend(
                [
                    'echo "LC_ALL=en_US.UTF-8" >> /etc/environment',
                    'echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen',
                    'echo "LANG=en_US.UTF-8" > /etc/locale.conf',
                    "locale-gen en_US.UTF-8",
                ]
            )

        # Common directories
        self.__commands.append("mkdir -p /apps /scratch /lustre /work /projects /data")

        # Poetry
        if hpccm.config.g_linux_distro == linux_distro.UBUNTU:
            self.__ospackages.append("python3-venv")
        else:
            self.__ospackages.append("python3-virtualenv")
        self.__commands.extend(
            [
                """curl -sSL \
                https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py \
                | POETRY_HOME=/usr/local/poetry POETRY_VERSION=1.1.2 python3""",
                "chmod +x /usr/local/poetry/bin/poetry",
            ]
        )

    def runtime(self, _from="0"):
        instructions = [
            comment(__doc__, reformat=False),
            python(devel=True, python2=False).runtime(),
            pip(pip="pip3", packages=["virtualenv"]),
            shell(commands=["mkdir -p /apps /scratch /lustre /work /projects"]),
        ]

        return "\n".join(str(x) for x in instructions)
