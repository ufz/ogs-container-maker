"""Recipe base class"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import

import hpccm
from hpccm import linux_distro
import hpccm.base_object
from hpccm.building_blocks import packages
from hpccm.primitives import comment, user

from ogscm.config import package_manager
from ogscm.version import __version__

class recipe_base(hpccm.base_object):
    """Base class for building blocks."""

    def __init__(self, **kwargs):
        """Initialize building block base class"""

        super(recipe_base, self).__init__(**kwargs)

        self.__args = kwargs.get('args')
        self.__baseimage = kwargs.get('base_image')
        self.__Stage0 = hpccm.Stage()

        if self.__args.runtime_only:
            self.__Stage0.name = 'stage0'

        self.__Stage0.baseimage(image=self.__baseimage)
        centos = hpccm.config.g_linux_distro == linux_distro.CENTOS

        # Get git info
        # local_git_hash = subprocess.check_output([
        #     'git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        self.__Stage0 += comment(
            # "Generated with https://github.com/ufz/ogs-container-maker/commit/{0}".format(
            #     local_git_hash),
            f"Generated with ogs-container-maker {__version__}",
            reformat=False)

        if centos:
            self.__Stage0 += user(user='root')
            self.__Stage0 += packages(ospackages=['epel-release'])
        self.__Stage0 += packages(ospackages=['wget', 'tar', 'curl'])

    def __str__(self):
        return str(self.__Stage0)
