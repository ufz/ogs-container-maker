# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Package manager Conan building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hpccm.config

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.pip import pip
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell


class pm_conan(bb_base):
    """Package manager Conan building block"""

    def __init__(self, **kwargs):
        super(pm_conan, self).__init__()

        self.__user_home = kwargs.get("user_home", "")
        self.__version = kwargs.get("version", "")

        self.__commands = []

        self.__setup()

        self.__instructions()

    def __instructions(self):
        self += comment(__doc__, reformat=False)
        # https://github.com/bincrafters/community/issues/880
        self += packages(ospackages=["pkg-config"])
        # For building curl:
        self += packages(ospackages=["autoconf-archive", "libtool"])

        self += pip(pip="pip3", packages=[f"conan=={self.__version}"])
        self += shell(commands=self.__commands)
        if self.__user_home != "":
            self += environment(variables={"CONAN_USER_HOME": self.__user_home})
        self += label(
            metadata={
                "org.opengeosys.pm": "conan",
                "org.opengeosys.pm.conan.version": self.__version,
            }
        )
        if self.__user_home != "":
            self += label(
                metadata={"org.opengeosys.pm.conan.user_home": self.__user_home}
            )

    def __setup(self):
        if self.__user_home != "":
            self.__commands.extend(
                [
                    # Create Conan cache dir writable by all users
                    # TODO: does not work in Singularity: Read-only file system
                    "mkdir -p /opt/conan",
                    "chmod 777 /opt/conan",
                ]
            )

    # No runtime
