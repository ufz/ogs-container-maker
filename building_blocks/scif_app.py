# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""SCIF app building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging
import os

from hpccm.common import container_type
from hpccm.primitives.copy import copy
from hpccm.primitives.label import label
from hpccm.primitives.raw import raw
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
import hpccm.config


class scif_app():
    """SCIF app building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        self.name = kwargs.get('name')
        self.run = kwargs.get('run')
        self.install = kwargs.get('install')
        self.labels = kwargs.get('labels')
        self.test = kwargs.get('test')

        # SCIF format is always in Singularity syntax
        ct = hpccm.config.g_ctype
        hpccm.config.g_ctype = container_type.SINGULARITY
        instructions = []
        if self.install:
            instructions.append(shell(commands=self.install, _app=self.name))
        if self.run:
            instructions.append(runscript(commands=[self.run], _app=self.name))
        if self.labels:
            instructions.append(label(metadata=self.labels, _app=self.name))
        if self.test:
            instructions.append(raw(singularity='%apptest {}\n    {}'.format(
                self.name, self.test)))
        instructions_string = '\n'.join(str(x) for x in instructions)
        hpccm.config.g_ctype = ct

        if hpccm.config.g_output_directory:
            self.__scif_path = os.path.join(hpccm.config.g_output_directory,
                                            '{}.scif'.format(self.name))
            scif_file = open(self.__scif_path, "w")
            scif_file.write(instructions_string)
            scif_file.close()
        else:
            logging.error('No output directory specified but it is necessary '
                          'for using scif_app()! Specify with --out argument.')

    def __str__(self):
        if hpccm.config.g_output_directory:
            instructions = [
                copy(src=[self.__scif_path], dest='/scif/recipes/',
                     _mkdir=True),
                shell(commands=[
                    'scif install /scif/recipes/{}.scif'.format(self.name)
                ])
            ]
            return '\n'.join(str(x) for x in instructions)
        return ''
