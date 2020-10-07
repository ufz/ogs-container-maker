# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""ccache building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell


class ccache(bb_base):
    """ccache building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(ccache, self).__init__()
        self.__cache_dir = kwargs.get("cache_dir", "/opt/ccache")
        self.__cache_size = kwargs.get("cache_size", "5G")

        self.__instructions()

    def __instructions(self):
        self += comment(__doc__, reformat=False)
        self += packages(ospackages=["ccache"])
        self += shell(
            commands=["mkdir -p {0} && chmod 777 {0}".format(self.__cache_dir)]
        )
        self += environment(
            variables={
                "CCACHE_DIR": self.__cache_dir,
                "CCACHE_MAXSIZE": self.__cache_size,
                "CCACHE_SLOPPINESS": "pch_defines,time_macros",
            }
        )
        self += label(
            metadata={"ccache.dir": self.__cache_dir, "ccache.size": self.__cache_size}
        )

    # No runtime
