# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""self Arguments"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import argparse

from ogscm.version import __version__


class Cli_Args(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        """Initialize"""
        argparse.ArgumentParser.__init__(self)
        self.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        self.add_argument(
            '--version',
            action='version',
            version='%(prog)s {version}'.format(version=__version__))
        self.add_argument('--out',
                          type=str,
                          default='_out',
                          help='Output directory')
        self.add_argument('--file',
                          type=str,
                          default='',
                          help='Overwrite output recipe file name')
        self.add_argument('--print',
                          '-P',
                          dest='print',
                          action='store_true',
                          help='Print the definition to stdout')
        options_g = self.add_argument_group(
            'Combinatorial options',
            'All combinations of the given options will '
            'be generated')
        options_g.add_argument('--format',
                               nargs='*',
                               type=str,
                               choices=['docker', 'singularity'],
                               default=['docker'])
        options_g.add_argument('--pm',
                               nargs='*',
                               type=str,
                               choices=['system', 'conan', 'spack', 'off'],
                               default=['conan'],
                               help='Package manager to install third-party '
                               'dependencies')
        options_g.add_argument(
            '--ompi',
            nargs='*',
            type=str,
            default=['off'],
            help='OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2')
        options_g.add_argument(
            '--ogs',
            nargs='*',
            type=str,
            default=['ufz/ogs@master'],
            help='OGS GitHub repo in the form \'user/repo@branch\' '
            'OR \'user/repo@@commit\' to checkout a specific commit '
            'OR a path to a local subdirectory to the git cloned OGS sources'
            'OR \'off\' to disable OGS building')
        options_g.add_argument(
            '--cmake_args',
            nargs='*',
            type=str,
            default=[''],
            help='CMake argument sets have to be quoted and **must**'
            ' start with a space. e.g. --cmake_args \' -DFIRST='
            'TRUE -DFOO=BAR\' \' -DSECOND=TRUE\'')
        build_g = self.add_argument_group('Image build options')
        build_g.add_argument('--build',
                             '-B',
                             dest='build',
                             action='store_true',
                             help='Build the images from the definition files')
        build_g.add_argument('--upload',
                             '-U',
                             dest='upload',
                             action='store_true',
                             help='Upload Docker image to registry')
        build_g.add_argument(
            '--registry',
            type=str,
            default='registry.opengeosys.org/ogs/ogs',
            help='The docker registry the image is tagged and '
            'uploaded to.')
        build_g.add_argument('--convert',
                             '-C',
                             dest='convert',
                             action='store_true',
                             help='Convert Docker image to Singularity image')
        build_g.add_argument(
            '--runtime-only',
            '-R',
            dest='runtime_only',
            action='store_true',
            help='Generate multi-stage Dockerfiles for small runtime '
            'images')
        switches_g = self.add_argument_group('Additional options')
        switches_g.add_argument(
            '--base_image',
            type=str,
            default='ubuntu:18.04',
            help='The base image.')
        switches_g.add_argument(
            '--compiler',
            type=str,
            default='gcc',
            help='The compiler to use. Possible options: off, gcc, clang')
        switches_g.add_argument('--compiler_version',
                                type=str,
                                default='',
                                help='Compiler version.')
        switches_g.add_argument('--gui',
                                dest='gui',
                                action='store_true',
                                help='Builds the GUI (Data Explorer)')
        switches_g.add_argument(
            '--docs',
            dest='docs',
            action='store_true',
            help='Setup documentation requirements (Doxygen)')
        switches_g.add_argument('--jenkins',
                                dest='jenkins',
                                action='store_true',
                                help='Setup Jenkins slave')
        switches_g.add_argument('--cvode',
                                dest='cvode',
                                action='store_true',
                                help='Install and configure with cvode')
        switches_g.add_argument('--cppcheck',
                                dest='cppcheck',
                                action='store_true',
                                help='Install cppcheck')
        switches_g.add_argument('--iwyy',
                                dest='iwyy',
                                action='store_true',
                                help='Install include-what-you-use')
        switches_g.add_argument('--gcovr',
                                dest='gcovr',
                                action='store_true',
                                help='Install gcovr')
        switches_g.add_argument('--mpi_benchmarks',
                                dest='mpi_benchmarks',
                                action='store_true',
                                help='Installs OSU MPI '
                                'benchmarks as scif app and mpi_bw, mpi_ring,'
                                'mpi_hello')
        switches_g.add_argument('--dev',
                                dest='dev',
                                action='store_true',
                                help='Installs development tools (vim, gdb)')
        maint_g = self.add_argument_group('Maintenance')
        maint_g.add_argument(
            '--clean',
            dest='cleanup',
            action='store_true',
            help='Cleans up generated files in default directories.')
