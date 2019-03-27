# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""OGS base building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hpccm.config

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.cmake import cmake
from hpccm.building_blocks.packages import packages
from hpccm.building_blocks.pip import pip
from hpccm.building_blocks.python import python
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.shell import shell


class ogs_base(bb_base):
    """OGS base building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""
        super(ogs_base, self).__init__()

        self.__ospackages = kwargs.get('ospackages', [])

        self.__commands = []  # Filled in by __setup()
        self.__wd = '/var/tmp'  # working directory

        self.__setup()

        self.__instructions()

    def __instructions(self):
        """String representation of the building block"""
        self += comment(__doc__, reformat=False)
        self += python(devel=True)
        self += pip(pip='pip3', upgrade=True)
        self += pip(pip='pip3', packages=['virtualenv'])
        self += cmake(eula=True, version='3.13.4')
        self += packages(ospackages=self.__ospackages,
                         apt_ppas=['ppa:git-core/ppa'], epel=True)
        self += shell(commands=self.__commands)


    def __setup(self):
        self.__ospackages.extend(['git', 'git-lfs', 'make', 'ninja-build'])

        dist = 'deb'
        if hpccm.config.g_linux_distro == linux_distro.CENTOS:
            dist = 'rpm'
        if hpccm.config.g_linux_distro == linux_distro.UBUNTU:
            self.__commands.append("apt-get update")
        self.__commands.append(
            "curl -s https://packagecloud.io/install/repositories/github/"
            "git-lfs/script.{0}.sh | bash".format(dist))

        if hpccm.config.g_ctype == hpccm.container_type.SINGULARITY:
            self.__ospackages.append('locales')
            self.__commands.extend(
                ['echo "LC_ALL=en_US.UTF-8" >> /etc/environment',
                 'echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen',
                 'echo "LANG=en_US.UTF-8" > /etc/locale.conf',
                 'locale-gen en_US.UTF-8'])

        self.__commands.append('git lfs install')

        # Common directories
        self.__commands.append(
            'mkdir -p /apps /scratch /lustre /work /projects')

    def runtime(self, _from='0'):
        p = python(python2=False)
        instructions = [
            comment(__doc__, reformat=False),
            p.runtime(),
            shell(commands=[
                'mkdir -p /apps /scratch /lustre /work /projects'
            ])
        ]

        return '\n'.join(str(x) for x in instructions)
