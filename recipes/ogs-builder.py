"""This example demonstrates user arguments.
The OpenMPI version can be specified on the command line.
Note: no validation is performed on the user supplied information.
Usage:
$ hpccm.py --recipe ogs-builder.py --userarg ompi=2.1.3 centos=true \
  repo=https://github.com/bilke/ogs branch=singularity \
  cmake="-DOGS_BUILD_UTILS;ON"

Other options:
- ogs=false Builds a MPI test container
- infiniband=false Disables infiniband
"""
# pylint: disable=invalid-name, undefined-variable, used-before-assignment
import hpccm
import logging
import math
import multiprocessing
import subprocess

from building_blocks.ccache import ccache
from building_blocks.cppcheck import cppcheck
from building_blocks.cvode import cvode
from building_blocks.eigen import eigen
from building_blocks.iwyy import iwyy
from building_blocks.jenkins_node import jenkins_node
from building_blocks.ogs import ogs
from building_blocks.ogs_base import ogs_base
from building_blocks.osu_benchmarks import osu_benchmarks
from building_blocks.petsc import petsc
from building_blocks.pm_conan import pm_conan
from building_blocks.vtk import vtk
from base.config import package_manager
from hpccm.common import linux_distro, container_type

singularity = hpccm.config.g_ctype == container_type.SINGULARITY
docker = hpccm.config.g_ctype == container_type.DOCKER


# ---- Tools ----
def str2bool(v):
    if isinstance(v, (bool)):
        return v
    return v.lower() in ("yes", "true", "t", "1")


# ---- Options ----
centos = str2bool(USERARG.get('centos', 'False'))
clang = str2bool(USERARG.get('clang', 'False'))
ogs_version = USERARG.get('ogs', 'ufz/ogs@master')
infiniband = str2bool(USERARG.get('infiniband', 'True'))
benchmarks = str2bool(USERARG.get('benchmarks', 'True'))
jenkins = str2bool(USERARG.get('jenkins', 'False'))
pm = package_manager.set(pm=USERARG.get('pm', 'system'))
ompi_version = USERARG.get('ompi', 'off')
ompi = True
if ompi_version == "off":
    ompi = False
    infiniband = False
if jenkins:
    ogs_version = 'off'

repo = USERARG.get('repo', 'https://github.com/ufz/ogs')
branch = USERARG.get('branch', 'master')
# Use : instead of = e.g. -DCMAKE_BUILD_TYPE:Release
cmake_args = USERARG.get('cmake_args', '')
cmake_args = cmake_args.replace(":", "=")
cmake_args = cmake_args.split(' ')

_cvode = str2bool(USERARG.get('cvode', 'False'))
_cppcheck = str2bool(USERARG.get('cppcheck', 'False'))
_iwyy = str2bool(USERARG.get('iwyy', 'False'))
gui = str2bool(USERARG.get('gui', False))
docs = str2bool(USERARG.get('docs', False))
gcovr = str2bool(USERARG.get('gcovr', False))

if pm == 'spack' and not ompi:
    logging.error('spack needs mpi!')

# Get git info
local_git_hash = subprocess.check_output([
    'git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()

######
# Devel stage
######

# Choose between either Ubuntu 17.10 (default) or CentOS 7
# Add '--userarg centos=true' to the command line to select CentOS
image = 'ubuntu:17.10'
if centos:
    image = 'centos:7'

Stage0.baseimage(image=image)
Stage0 += comment("Generated with https://github.com/ufz/ogs-container-maker/commit/{0}".format(local_git_hash), reformat=False)
if centos:
    Stage0 += user(user='root')
    Stage0 += packages(ospackages=['epel-release'])
Stage0 += packages(ospackages=['wget', 'tar', 'curl'])

# base compiler
gcc_version = '6'
clang_version = '5.0'
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
Stage0 += compiler
if clang:
    Stage0 += packages(
        apt=["clang-tidy-{}".format(clang_version),
             "clang-format-{}".format(clang_version)],
        yum=["llvm-toolset-{}-clang-tools-extra".format(clang_version)]
    )

if infiniband:
    Stage0 += mlnx_ofed(version='3.4-1.0.0.0')

if ompi:
    mpicc = openmpi(version=ompi_version, cuda=False, infiniband=infiniband,
                    toolchain=toolchain)
    toolchain = mpicc.toolchain
    Stage0 += mpicc

    Stage0 += label(metadata={
        'org.opengeosys.mpi': 'openmpi',
        'org.opengeosys.mpi.version': ompi_version,
        'org.opengeosys.infiniband': infiniband
    })

    if benchmarks:
        Stage0 += osu_benchmarks()

Stage0 += ogs_base()
if gui:
    Stage0 += packages(ospackages=[
        'mesa-common-dev', 'libgl1-mesa-dev', 'libxt-dev'
    ])
if pm == package_manager.CONAN:
    Stage0 += pm_conan()
    if not jenkins:
      Stage0 += environment(variables={'CONAN_SYSREQUIRES_SUDO': 0})
elif pm == package_manager.SYSTEM:
    Stage0 += boost()  # header only?
    Stage0 += environment(variables={'BOOST_ROOT': '/usr/local/boost'})
    Stage0 += eigen()
    vtk_cmake_args = [
        '-DVTK_Group_StandAlone=OFF',
        '-DVTK_Group_Rendering=OFF',
        '-DModule_vtkIOXML=ON'
    ]
    Stage0 += vtk(cmake_args=vtk_cmake_args, toolchain=toolchain)
    if ompi:
        Stage0 += petsc()
if _cvode:
    Stage0 += cvode()
if _cppcheck:
    Stage0 += cppcheck()
if _iwyy and clang:
    Stage0 += iwyy(clang_version = clang_version)
if docs:
    Stage0 += packages(
        ospackages=['doxygen', 'graphviz', 'texlive-base'])
if gcovr:
    Stage0 += pip(pip='pip3', packages=['gcovr'])

if ogs_version != 'off':
    if _cvode:
        cmake_args.append('-DOGS_USE_CVODE=ON')
    Stage0 += raw(docker='ARG OGS_COMMIT_HASH=0')
    Stage0 += ogs(version=ogs_version, toolchain=toolchain,
                  cmake_args=cmake_args, parallel=math.ceil(multiprocessing.cpu_count()/2),
                  app='ogs', skip_lfs=True, remove_dev=True)

if jenkins:
    Stage0 += ccache(cache_size='15G')
    Stage0 += packages(ospackages=['sudo'])  # For user switching back to root
    Stage0 += jenkins_node()

######
# Runtime image
######
Stage1.baseimage(image=image)
Stage1 += Stage0.runtime()