# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""Jenkins Node building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging  # pylint: disable=unused-import
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.primitives.comment import comment
from hpccm.primitives.shell import shell
from hpccm.primitives.user import user
from hpccm.primitives.workdir import workdir


class jenkins_node(bb_base, hpccm.templates.rm, hpccm.templates.tar,
                   hpccm.templates.wget):
  """Jenkins Node building block"""

  def __init__(self, **kwargs):
    """Initialize building block"""
    super(jenkins_node, self).__init__()

    self.__commands = []  # Filled in by __setup()
    self.__wd = '/var/tmp'  # working directory

    self.__instructions()

  def __instructions(self):
    self += comment('Jenkins node')
    self += shell(commands=[
        'groupadd --gid 1001 jenkins',
        'adduser --uid 500 --gid 1001 --disabled-password --gecos "" jenkins',
        'echo "jenkins ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers',
        'echo "jenkins:jenkins" | chpasswd'
    ])
    self += user(user='jenkins')
    self += workdir(directory='/home/jenkins')

    logging.warning("Changed user to jenkins!")


  def runtime(self, _from='0'):
    """Install the runtime from a full build in a previous stage.  In this
       case there is no difference between the runtime and the
       full build."""
    return str(self)
