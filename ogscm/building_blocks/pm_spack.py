# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Package manager spack building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.primitives import copy
from hpccm.primitives.comment import comment
from hpccm.primitives.environment import environment
from hpccm.primitives.label import label
from hpccm.primitives.shell import shell
import hpccm.templates.wget


class pm_spack(bb_base, hpccm.templates.git):
    """Package manager spack building block"""

    def __init__(self, **kwargs):
        super(pm_spack, self).__init__()


        self.__ospackages = kwargs.get('ospackages', [])
        self.__packages = kwargs.get('packages', [])
        self.__repo = kwargs.get('repo', 'https://github.com/spack/spack')
        self.__branch = kwargs.get('branch', 'devel')

        self.__commands = []  # Filled in by __setup()
        self.__environment_variables = {}
        self.__labels = {}


        self.__wd = '/var/tmp'  # working directory

        self.__setup()

        self.__instructions()


    def __instructions(self):
        self += comment(__doc__, reformat=False)
        self += packages(ospackages=self.__ospackages)
        self += packages(yum=['xz'], apt=['xz-utils'])
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)
        if self.__labels:
            self += label(metadata=self.__labels)
        if self.__packages:
            self += copy(src='files/spack/packages.yml', dest='/etc/spack/packages.yaml')
            install_cmds = []
            for package in self.__packages:
                install_cmds.append('/opt/spack/bin/spack install {0}'.format(package))
            install_cmds.append('/opt/spack/bin/spack clean --all')
            self += shell(commands=install_cmds)


    def __setup(self):
        self.__ospackages.extend(['patch', 'less', 'curl', 'bzip2'])
        self.__commands.extend([
            self.clone_step(repository=self.__repo, branch=self.__branch,
                            path='/opt'),
            '/opt/spack/bin/spack bootstrap',
            # TODO: There is no init system inside the container -> files are
            #       not sourced!
            'ln -s /opt/spack/share/spack/setup-env.sh /etc/profile.d/spack.sh',
            'ln -s /opt/spack/share/spack/spack-completion.bash /etc/profile.d',
            '/opt/spack/bin/spack clean --all'
        ])

        # Environment
        self.__environment_variables['PATH'] = '/opt/spack/bin:$PATH'
        self.__environment_variables['FORCE_UNSAFE_CONFIGURE'] = '1'

        # Labels
        self.__labels['org.opengeosys.pm'] = 'spack'


    def runtime(self, _from='0'):
        """Install the runtime from a full build in a previous stage.  In this
           case there is no difference between the runtime and the
           full build."""
        return str(self)
