

# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""SCIF building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import os

from hpccm.building_blocks.packages import packages
from hpccm.common import container_type
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.label import label
from hpccm.primitives.raw import raw
from hpccm.primitives.runscript import runscript
from hpccm.primitives.shell import shell
import hpccm.config


class scif_app(object):
    """Documentation TBD"""

    def __init__(self, **kwargs):
        """Documentation TBD"""

        self.name = kwargs.get('name')
        self.run = kwargs.get('run')
        self.install = kwargs.get('install')
        self.labels = kwargs.get('labels')
        self.test = kwargs.get('test')

    def __str__(self):
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

        return instructions_string


class scif():
    """SCIF building block"""

    def __init__(self, **kwargs):
        """Initialize building block"""

        # Trouble getting MRO with kwargs working correctly, so just call
        # the parent class constructors manually for now.
        # super(python, self).__init__(**kwargs)

        self.__entrypoint = kwargs.get('entrypoint', False)

        self.instructions = [
            comment(__doc__, reformat=False),
            packages(ospackages=['python-pip', 'python-setuptools']),
            shell(commands=[
              'pip install wheel',
              'pip install scif'
            ])
        ]

        if self.__entrypoint:
            self.instructions.append(runscript(commands=['scif']))

    def __str__(self):
        """String representation of the building block"""

        return '\n'.join(str(x) for x in self.instructions)

    def install(self, app):
        out_dir = '_gen'
        scif_path = os.path.join(out_dir, '{}.scif'.format(app.name))
        scif_file = open(scif_path, "w")
        scif_file.write(str(app))
        scif_file.close()
        self.instructions.extend([
            copy(src=[scif_path], dest='/scif/recipes/', _mkdir=True),
            shell(commands=[
                'scif install /scif/recipes/{}.scif'.format(app.name)
            ])
        ])

    def runtime(self, _from='0'):
        """Install the runtime from a full build in a previous stage.  In this
           case there is no difference between the runtime and the
           full build."""
        return str(self)
