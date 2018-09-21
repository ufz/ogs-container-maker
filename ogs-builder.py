"""This example demonstrates user arguments.
The OpenMPI version can be specified on the command line.
Note: no validation is performed on the user supplied information.
Usage:
$ hpccm.py --recipe ogs-builder.py --userarg ompi=2.1.3 centos=true \
  repo=https://github.com/bilke/ogs branch=singularity \
  cmake="-DOGS_BUILD_UTILS=ON -DOGS_BUILD_TESTS=OFF"

Other options:
- ogs=false Builds a MPI test container
- infiniband=false Disables infinband
"""
# pylint: disable=invalid-name, undefined-variable, used-before-assignment

import os
from hpccm.templates.git import git

singularity = hpccm.config.g_ctype == container_type.SINGULARITY
docker = hpccm.config.g_ctype == container_type.DOCKER


##### Tools #####
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

##### Options #####
centos =     str2bool(USERARG.get('centos',     'True'))
ogs =        str2bool(USERARG.get('ogs',        'True'))
infiniband = str2bool(USERARG.get('infiniband', 'True'))
ompi_version =        USERARG.get('ompi',       '3.0.2')
benchmarks = str2bool(USERARG.get('benchmarks', 'True'))

repo =                USERARG.get('repo',       'https://github.com/ufz/ogs')
branch =              USERARG.get('branch',     'master')
cmake_args =          USERARG.get('cmake',      '')

######
# Devel stage
######

Stage0 += comment(__doc__, reformat=False)

# Choose between either Ubuntu 16.04 (default) or CentOS 7
# Add '--userarg centos=true' to the command line to select CentOS
image = 'ubuntu:16.04'
if centos:
  image = 'centos/devtoolset-6-toolchain-centos7'

Stage0.baseimage(image=image)

if centos:
  Stage0 += user(user='root')
  Stage0 += packages(ospackages=['epel-release'])

# Common directories
Stage0 += shell(commands=['mkdir -p /apps /scratch /lustre /work /projects'])

# Common packages
Stage0 += packages(ospackages=['curl', 'ca-certificates'])

if singularity:
  Stage0 += packages(ospackages=['locales'])
  Stage0 += shell(commands=['echo "LC_ALL=en_US.UTF-8" >> /etc/environment',
                            'echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen',
                            'echo "LANG=en_US.UTF-8" > /etc/locale.conf',
                            'locale-gen en_US.UTF-8'])

# Python
if centos:
  Stage0 += packages(ospackages=['python34-setuptools'])
  Stage0 += shell(commands=['easy_install-3.4 pip'])
else:
  Stage0 += packages(ospackages=['python3-setuptools', 'python3-pip'])
Stage0 += shell(commands=['python3 -m pip install --upgrade pip'])

# GNU compilers
if not centos:
  Stage0 += gnu(fortran=False)

# Mellanox OFED
if infiniband:
  Stage0 += mlnx_ofed(version='3.4-1.0.0.0')

# OpenMPI
Stage0 += openmpi(version=ompi_version, cuda=False, infiniband=infiniband)

# SCI-F: mpi-bandwidth
# scif_mpi = scif(
  # name = 'mpi-bandwidth',
  # install = ['wget -q -nc --no-check-certificate -P /var/tmp https://computing.llnl.gov/tutorials/mpi/samples/C/mpi_bandwidth.c',
            #  'mpicc -o bin/mpi-bandwidth /var/tmp/mpi_bandwidth.c'],
  # run = 'exec /scif/apps/mpi-bandwidth/bin/mpi-bandwidth "\$@"',
  # help = 'This app provides a MPI bandwidth test program',
  # test = 'mpirun -np 2 /scif/apps/mpi-bandwidth/bin/mpi-bandwidth "\$@"'
# )
# Stage0 += scif_mpi.install()

app = 'mpi-bandwidth'
Stage0 += shell(commands=[
    'wget -q -nc --no-check-certificate -P /var/tmp https://computing.llnl.gov/tutorials/mpi/samples/C/mpi_bandwidth.c',
    'mpicc -o bin/mpi-bandwidth /var/tmp/mpi_bandwidth.c'], _app=app, _appenv=True)
Stage0 += runscript(commands=['/scif/apps/mpi-bandwidth/bin/mpi-bandwidth "$@"'], _app=app)
Stage0 += raw(singularity='\
%apphelp {0}\n    This app provides a MPI bandwidth test program\n\n\
%apptest {0}\n    mpirun -np 2 /scif/apps/mpi-bandwidth/bin/mpi-bandwidth "$@"\n\n'.format(app))

### OGS ###
if ogs:
  Stage0 += shell(commands=['python3 -m pip install cmake conan==1.6.1']) # Conan 1.7 requires newer Python than 3.4
  if centos:
    Stage0 += shell(commands=['curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | bash'])
  else:
    Stage0 += packages(ospackages=['software-properties-common'])
    Stage0 += shell(commands=['cd ~',
                              'add-apt-repository ppa:git-core/ppa',
                              'curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash'])
  Stage0 += packages(ospackages=['git', 'git-lfs'])
  Stage0 += shell(commands=['git lfs install'])

  Stage0 += shell(commands=[
    git().clone_step(repository=repo, branch=branch, path='/scif/apps/ogs',
                       directory='src', lfs=centos),
    'cd /scif/apps/ogs/src && git fetch --tags',
    'mkdir -p /scif/apps/ogs/build',
    'cd /scif/apps/ogs/build',
    ('CONAN_SYSREQUIRES_SUDO=0 CC=mpicc CXX=mpic++ cmake /scif/apps/ogs/src ' +
     '-DCMAKE_BUILD_TYPE=Release ' +
     '-DCMAKE_INSTALL_PREFIX=/scif/apps/ogs ' +
     '-DOGS_USE_PETSC=ON ' +
     '-DOGS_USE_CONAN=ON ' +
     '-DOGS_CONAN_USE_SYSTEM_OPENMPI=ON ' +
     cmake_args
     ),
    'make -j',
    'make install'
  ], _app='ogs', _appenv=True)
  Stage0 += runscript(commands=['/scif/apps/ogs/bin/ogs "$@"'], _app='ogs')
  Stage0 += label(metadata={'REPOSITORY': repo, 'BRANCH': branch}, _app='ogs')
  Stage0 += raw(singularity='%apptest ogs\n    /scif/apps/ogs/bin/ogs --help')
  
  # Is also default runscript
  Stage0 += runscript(commands=['/scif/apps/ogs/bin/ogs "$@"'])
  
### OSU Benchmarks
if benchmarks:
  Stage0 += shell(commands=[
    'OSU_VERSION=5.4.2',
    'wget http://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-${OSU_VERSION}.tar.gz --no-check-certificate',
    'tar -xf osu-micro-benchmarks-${OSU_VERSION}.tar.gz',
    'cd osu-micro-benchmarks-${OSU_VERSION}/',
    './configure ' +
    'CC=mpicc CXX=mpicxx ' +
    '--prefix=/scif/apps/osu',
    'make -j',
    'make install',
    'cd ../',
    'rm -fr osu-micro-benchmarks-${OSU_VERSION}*',
  ], _app='osu', _appenv=True)

Stage0 += label(metadata={
  'openmpi.version': ompi_version,
  'infiniband': infiniband
})
######
# Runtime image
######