# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Lmod building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os

from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell
from hpccm.templates.ConfigureMake import ConfigureMake
from hpccm.templates.rm import rm
from hpccm.templates.tar import tar
from hpccm.templates.wget import wget


class lmod(ConfigureMake, rm, tar, wget):
    """Lmod building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        # super(python, self).__init__(**kwargs)
        ConfigureMake.__init__(self, **kwargs)
        rm.__init__(self, **kwargs)
        tar.__init__(self, **kwargs)
        wget.__init__(self, **kwargs)

        self.__commands = []  # Filled in by __setup()
        self.__wd = "/var/tmp"  # working directory
        self.prefix = "/opt/apps"
        self.version = kwargs.get("version", "7.8.6")

    def __str__(self):
        """String representation of the building block"""
        tarfile = "{}.tar.gz".format(self.version)
        source = os.path.join(self.__wd, "Lmod-{}".format(self.version))
        instructions = []
        instructions.extend(
            [
                comment(__doc__, reformat=False),
                # For Doxygen diagrams and bibtex references
                packages(
                    ospackages=[
                        "liblua5.1-0",
                        "liblua5.1-0-dev",
                        "lua-filesystem-dev",
                        "lua-posix-dev",
                        "lua5.1",
                        "tclsh",
                    ]
                ),
                shell(
                    commands=[
                        self.download_step(
                            url="https://github.com/TACC/Lmod/archive/{}".format(
                                tarfile
                            ),
                            directory=self.__wd,
                        ),
                        self.untar_step(
                            tarball=os.path.join(self.__wd, tarfile),
                            directory=self.__wd,
                        ),
                        self.configure_step(directory=source),
                        self.install_step(),
                        "ln -s /opt/apps/lmod/lmod/init/profile /etc/profile.d/z00_lmod.sh",
                        "ln -s /opt/apps/lmod/lmod/init/cshrc   /etc/profile.d/z00_lmod.csh",
                    ]
                ),
                environment(
                    variables={"MODULEPATH": "/opt/easybuild/modules/all:$MODULEPATH"}
                ),
            ]
        )

        return "\n".join(str(x) for x in instructions)

    def runtime(self, _from="0"):
        """Install the runtime from a full build in a previous stage.  In this
        case there is no difference between the runtime and the
        full build."""
        return str(self)
