# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes

"""salome building block"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import logging # pylint: disable=unused-import
import os

import hpccm.config
import hpccm.templates.rm
import hpccm.templates.tar
import hpccm.templates.wget

from hpccm.building_blocks.base import bb_base
from hpccm.building_blocks.packages import packages
from hpccm.common import linux_distro
from hpccm.primitives.comment import comment
from hpccm.primitives.copy import copy
from hpccm.primitives.environment import environment
from hpccm.primitives.shell import shell

class salome(bb_base, hpccm.templates.rm, hpccm.templates.tar,
             hpccm.templates.wget):
    """The `salome` building block configures, builds, and installs
    [Salome](https://www.salome-platform.org).

    As a side effect, this building block modifies `PATH` to include
    the salome build.

    If GPU rendering will be used then a
    [opengl](https://hub.docker.com/r/nvidia/opengl) base image is
    recommended, e.g. nvidia/opengl:1.0-glvnd-runtime-ubuntu18.04

    # Parameters
    ospackages: Too many to list here...

    prefix: The top level install location.  The default value is
    `/usr/local/salome`.

    version: The version of salome source to download.  The default
    value is `9.2.1`.

    # Examples

    ```python
    salome(prefix='/opt/salome', version='8.5.0')
    ```

    """

    def __init__(self, **kwargs):
        """Initialize building block"""

        super(salome, self).__init__(**kwargs)

        self.__ospackages = kwargs.get('ospackages', [])
        self.__parallel = kwargs.get('parallel', '$(nproc)')
        self.__prefix = kwargs.get('prefix', '/usr/local/salome')
        self.__runtime_ospackages = [] # Filled in by __distro()
        self.__version = kwargs.get('version', '9.2.1')
        self.__url = r'http://files.salome-platform.org/Salome/Salome{0}/'
        self.__tarball = r'SALOME-{0}-{1}-SRC.tgz'

        self.__commands = [] # Filled in by __setup()
        self.__environment_variables = {
            'PATH': '{}:$PATH'.format(os.path.join(self.__prefix, 'bin'))}
        self.__wd = '/var/tmp/salome' # working directory

        # Set the Linux distribution specific parameters
        self.__distro()

        # Construct the series of steps to execute
        self.__setup()

        # Fill in container instructions
        self.__instructions()

    def __instructions(self):
        """Fill in container instructions"""

        self += comment('salome version {}'.format(self.__version))
        # self += packages(ospackages=self.__ospackages)
        self += shell(commands=self.__commands)
        if self.__environment_variables:
            self += environment(variables=self.__environment_variables)

    def __distro(self):
        """Based on the Linux distribution, set values accordingly.  A user
        specified value overrides any defaults."""

        if hpccm.config.g_linux_distro == linux_distro.UBUNTU:
            if not self.__ospackages:
                self.__ospackages = [
                    'python3',
                    'bash-completion',
                    'binutils',
                    'coreutils',
                    'sudo',
                    'module-init-tools',
                    'iputils-ping',
                    'net-tools',
                    'libglu1-mesa',
                    'libxmu6',
                    'libpng16-16',
                    'zlib1g-dev',
                    'libboost-python-dev',
                    'liblapack-dev',
                    'python-numpy',
                    'python-dev',
                    'python',
                    'cmake',
                    'gfortran',
                    'g++',
                    'gcc',
                    'wget',
                    'rsync',
                    'build-essential',
                    'ca-certificates',
                    'locales',
                    'openssh-client',
                    'python-apt',
                    'git',
                    'dvipng',
                    'libfftw3-dev',
                    'libreadline-dev',
                    'libhdf5-dev',
                    'hdf5-tools',
                    'gfortran',
                    'automake',
                    'autoconf',
                    'libtool',
                    'python',
                    'libboost-all-dev',
                    'swig',
                    'libcgal-dev',
                    'libomniorb4-dev',
                    'graphviz-dev',
                    'libgl1-mesa-dev',
                    'libglu1-mesa-dev',
                    'libxmu-dev',
                    'omniidl',
                    'omniidl-python',
                    'omniorb-nameserver',
                    'libcos4-dev',
                    'python-omniorb',
                    'liblapack-dev',
                    'python-numpy',
                    'python-scipy',
                    'graphviz',
                    'doxygen',
                    'libxml2',
                    'libxslt1-dev',
                    'python-lxml',
                    'python-setuptools',
                    'python-pygments',
                    'python-jinja2',
                    'python-docutils',
                    'python-sphinx',
                    'libtbb-dev',
                    'libfreetype6-dev',
                    'libfreeimage-dev',
                    'python-sip-dev',
                    'metis',
                    'libmetis-dev',
                    'scotch',
                    'libscotch-dev',
                    'libtogl-dev',
                    'tcl8.5-dev',
                    'tk8.5-dev',
                    'tix-dev',
                    'libcgns-dev',
                    'libopencv-dev',
                    'libcppunit-dev',
                    'python-pkgconfig',
                    'cython',
                    'python-h5py',
                    'tralics',
                    'libmuparser-dev',
                    'libcgal-dev',
                    'python-pil',
                    'python-gnuplot',
                    'libnlopt-dev',
                    'libfontconfig1',
                    'libglib2.0-0',
                    'libglu1-mesa',
                    'libxmu6',
                    'libxrender1',
                    'mesa-utils',
                    'net-tools',
                    'dbus-x11',
                    'fonts-dejavu',
                    'fonts-liberation',
                    'hicolor-icon-theme',
                    'libcanberra-gtk3-0',
                    'libcanberra-gtk-module',
                    'libcanberra-gtk3-module',
                    'libglib2.0',
                    'libgtk2.0-0',
                    'libdbus-glib-1-2',
                    'libxt6',
                    'libexif12',
                    'libgl1-mesa-glx',
                    'libgl1-mesa-dri',
                    'xserver-xorg-video-intel',
                    'msttcorefonts',
                    'fonts-liberation',
                    'ttf-dejavu'
                ]
        elif hpccm.config.g_linux_distro == linux_distro.CENTOS:
            if not self.__ospackages:
                self.__ospackages = ['gzip', 'make', 'patch', 'tar', 'wget',
                                     'which', 'zlib-devel', 'libXt-devel',
                                     'libglvnd-devel', 'mesa-libGL-devel',
                                     'mesa-libGLU-devel']
            self.__runtime_ospackages = ['libXt', 'libglvnd', 'mesa-libGL',
                                         'mesa-libGLU', 'zlib']
        else: # pragma: no cover
            raise RuntimeError('Unknown Linux distribution')

    def __setup(self):
        platform = 'UB18.04'
        tarball = self.__tarball.format(self.__version, platform)
        url = self.__url.format(self.__version) + tarball


        # Download source from web
        self.__commands.extend([
            self.download_step(url=url, directory=self.__wd),
            self.untar_step(tarball=os.path.join(self.__wd, tarball),
                            directory=self.__wd,
                            args=["--strip-components=1"]),
            self.cleanup_step(items=[os.path.join(self.__wd)])
        ])

    # def runtime(self, _from='0'):
        # TODO: same as stage0
