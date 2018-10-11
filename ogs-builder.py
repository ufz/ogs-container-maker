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
import sys
sys.path.append(os.getcwd())
import hpccm

import config
from config import package_manager
from building_blocks.jenkins_node import jenkins_node
from building_blocks.ogs import ogs
from building_blocks.ogs_base import ogs_base
from building_blocks.pm_conan import pm_conan
from building_blocks.pm_easybuild import pm_easybuild
from building_blocks.pm_spack import pm_spack
from building_blocks.osu_benchmarks import osu_benchmarks
from hpccm.common import linux_distro, container_type

singularity = hpccm.config.g_ctype == container_type.SINGULARITY
docker = hpccm.config.g_ctype == container_type.DOCKER


# ---- Tools ----
def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")


# ---- Options ----
centos = str2bool(USERARG.get('centos', 'False'))
clang = str2bool(USERARG.get('clang', 'False'))
build_ogs = str2bool(USERARG.get('ogs', 'True'))
infiniband = str2bool(USERARG.get('infiniband', 'True'))
benchmarks = str2bool(USERARG.get('benchmarks', 'True'))
jenkins = str2bool(USERARG.get('jenkins', 'False'))
pm = package_manager.set(pm=USERARG.get('pm', 'conan'))
ompi_version = USERARG.get('ompi', 'off')
ompi = True
if ompi_version == "off":
    ompi = False
    infiniband = False
    benchmarks = False
if jenkins:
    build_ogs = False

repo = USERARG.get('repo', 'https://github.com/ufz/ogs')
branch = USERARG.get('branch', 'master')
cmake_args = USERARG.get('cmake', '')

######
# Devel stage
######

# Stage0 += comment(__doc__, reformat=False)

# Choose between either Ubuntu 16.04 (default) or CentOS 7
# Add '--userarg centos=true' to the command line to select CentOS
image = 'ubuntu:16.04'
if centos:
    image = 'centos:7'

Stage0.baseimage(image=image)
if centos:
    Stage0 += user(user='root')
    Stage0 += packages(ospackages=['epel-release'])
Stage0 += packages(ospackages=['wget', 'tar', 'curl'])

# base compiler
gcc_version = '4.9'
clang_version = '6.0'
if hpccm.config.g_linux_distro == linux_distro.CENTOS:
    gcc_version = '6'  # installs devtoolset-6 which is gcc-6.3.1
    clang_version = '7'  # installs llvm-toolset-7-clang which is clang 5.0.1
if clang:
    compiler = llvm(extra_repository=True, version=clang_version)
else:
    fortran = False
    if True:
        fortran = True
    compiler = gnu(fortran=fortran, extra_repository=True, version=gcc_version)
toolchain = compiler.toolchain
if pm != config.package_manager.EASYBUILD:
  Stage0 += compiler
if clang:
    Stage0 += packages(
        apt=["clang-tidy-{}".format(clang_version)],
        yum=["llvm-toolset-{}-clang-tools-extra".format(clang_version)]
    )

if infiniband:
    Stage0 += mlnx_ofed(version='3.4-1.0.0.0')

if ompi:
    mpicc = openmpi(version=ompi_version, cuda=False, infiniband=infiniband, toolchain=toolchain)
    toolchain = mpicc.toolchain
    Stage0 += mpicc

    app = 'mpi-bandwidth'
    Stage0 += shell(commands=[
        'wget -q -nc --no-check-certificate -P /var/tmp https://computing.llnl.gov/tutorials/mpi/samples/C/mpi_bandwidth.c',
        'mpicc -o bin/mpi-bandwidth /var/tmp/mpi_bandwidth.c'], _app=app, _appenv=True)
    if singularity:
      Stage0 += runscript(commands=['/scif/apps/mpi-bandwidth/bin/mpi-bandwidth "$@"'], _app=app)
    Stage0 += raw(singularity='\
%apphelp {0}\n    This app provides a MPI bandwidth test program\n\n\
%apptest {0}\n    mpirun -np 2 /scif/apps/mpi-bandwidth/bin/mpi-bandwidth "$@"\n\n'.format(app))

    Stage0 += label(metadata={
        'openmpi.version': ompi_version,
        'infiniband': infiniband
    })

Stage0 += ogs_base()
if pm == config.package_manager.CONAN:
    Stage0 += pm_conan()
    if not jenkins:
      Stage0 += environment(variables={'CONAN_SYSREQUIRES_SUDO': 0})
elif pm == config.package_manager.SPACK:
    Stage0 += pm_spack()
    Stage0 += copy(src='files/spack/packages.yaml', dest='/etc/spack/packages.yaml')
    Stage0 += copy(src='files/spack/spack-repo', dest='/opt/spack/var/spack/repos/ogs')
    Stage0 += shell(commands=['spack repo add /opt/spack/var/spack/repos/ogs'])
    Stage0 += packages(yum=['mesa-libGL-devel'], apt=['libgl1-mesa-dev', 'libxt-dev'])
    Stage0 += shell(commands=[
      'spack install eigen@3.2.9',
      'spack install boost@1.64.0',
      'spack install ogs.vtk@8.1.1{}'.format('+mpi' if ompi else ''),
      'spack install petsc@3.8.3',
      'spack clean --all'
    ])

elif pm == config.package_manager.EASYBUILD:
    pm_instance = pm_easybuild()
    Stage0 += pm_instance
    Stage0 += pm_instance.install(
      ospackages=['libibverbs-dev', 'libncurses5-dev'],
      configs=[
        'Eigen-3.3.4.eb',
        'Boost-1.66.0-foss-2018a.eb',
        # 'VTK-8.1.0-foss-2018a-Python-3.6.4.eb'
    ])
    Stage0 += pm_instance.install(configs=[
      'Python-3.6.4-foss-2018a.eb'
    ])
    Stage0 += pm_instance.install(configs=[
      'VTK-8.1.0-foss-2018a-Python-3.6.4.eb'
    ])
elif pm == config.package_manager.GUIX:
    print('guix not implemented.')

if build_ogs:
    Stage0 += ogs(repo=repo, branch=branch, toolchain=toolchain, parallel=2)

if benchmarks:
    Stage0 += osu_benchmarks()

if jenkins:
    Stage0 += jenkins_node()

######
# Runtime image
######
