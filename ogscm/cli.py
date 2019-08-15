#!/usr/bin/env python3

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0, 3.1.2
#  Eve: 1.8.8, 1.10.2, 2.1.1, 4.0.0
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import hashlib
import itertools
import json
import math
import multiprocessing
import os
import shutil

import requests
import subprocess
import sys

import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import packages, mlnx_ofed, knem, ucx, openmpi, \
    boost, pip, scif, llvm, gnu, ofed
from hpccm.primitives import comment, user, environment, raw, label, shell, \
    copy

import ogscm
from ogscm.config import package_manager
from ogscm.version import __version__
from ogscm.building_blocks import ccache, cppcheck, cvode, eigen, iwyy, \
    jenkins_node, ogs_base, ogs, osu_benchmarks, petsc, pm_conan, vtk, pm_spack


def main(): # pragma: no cover
    cli = argparse.ArgumentParser(
        description='Generate container image definitions.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    cli.add_argument('--version', action='version',
                     version='%(prog)s {version}'.format(version=__version__))
    cli.add_argument('--out', type=str, default='_out', help='Output directory')
    cli.add_argument('--file', type=str, default='', help='Overwrite output recipe file name')
    cli.add_argument('--print', '-P', dest='print', action='store_true',
                     help='Print the definition to stdout')
    options_g = cli.add_argument_group('Combinatorial options',
                                       'All combinations of the given options will '
                                       'be generated')
    options_g.add_argument('--format', nargs='*', type=str,
                           choices=['docker', 'singularity'],
                           default=['docker'])
    options_g.add_argument('--pm', nargs='*', type=str,
                           choices=['system', 'conan', 'spack', 'off'], default=['conan'],
                           help='Package manager to install third-party '
                                'dependencies')
    options_g.add_argument('--ompi', nargs='*', type=str,
                           default=['off'],
                           help='OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2')
    options_g.add_argument('--ogs', nargs='*', type=str,
                           default=['ufz/ogs@master'],
                           help='OGS GitHub repo in the form \'user/repo@branch\' '
                                'or \'off\' to disable OGS building')
    options_g.add_argument('--cmake_args', nargs='*', type=str, default=[''],
                           help='CMake argument sets have to be quoted and **must**'
                                ' start with a space. e.g. --cmake_args \' -DFIRST='
                                'TRUE -DFOO=BAR\' \' -DSECOND=TRUE\'')
    build_g = cli.add_argument_group('Image build options')
    build_g.add_argument('--build', '-B', dest='build', action='store_true',
                         help='Build the images from the definition files')
    build_g.add_argument('--upload', '-U', dest='upload', action='store_true',
                         help='Upload Docker image to registry')
    build_g.add_argument('--registry', type=str,
                         default='registry.opengeosys.org/ogs/ogs',
                         help='The docker registry the image is tagged and '
                              'uploaded to.')
    build_g.add_argument('--convert', '-C', dest='convert', action='store_true',
                         help='Convert Docker image to Singularity image')
    build_g.add_argument('--runtime-only', '-R', dest='runtime_only',
                         action='store_true',
                         help='Generate multi-stage Dockerfiles for small runtime '
                              'images')
    switches_g = cli.add_argument_group('Additional options')
    switches_g.add_argument('--base_image', type=str, default='ubuntu:18.04',
                            help='The base image. \'centos:7\' is supported too.')
    switches_g.add_argument('--compiler', type=str, default='gcc',
                            help='The compiler to use. Possible options: off, gcc, clang')
    switches_g.add_argument('--compiler_version', type=str, default='',
                            help='Compiler version.')
    switches_g.add_argument('--gui', dest='gui', action='store_true',
                            help='Builds the GUI (Data Explorer)')
    switches_g.add_argument('--docs', dest='docs', action='store_true',
                            help='Setup documentation requirements (Doxygen)')
    switches_g.add_argument('--jenkins', dest='jenkins', action='store_true',
                            help='Setup Jenkins slave')
    switches_g.add_argument('--cvode', dest='cvode', action='store_true',
                            help='Install and configure with cvode')
    switches_g.add_argument('--cppcheck', dest='cppcheck', action='store_true',
                            help='Install cppcheck')
    switches_g.add_argument('--iwyy', dest='iwyy', action='store_true',
                            help='Install include-what-you-use')
    switches_g.add_argument('--gcovr', dest='gcovr', action='store_true',
                            help='Install gcovr')
    switches_g.add_argument('--mpi_benchmarks', dest='mpi_benchmarks',
                            action='store_true', help='Installs OSU MPI '
                            'benchmarks as scif app and mpi_bw, mpi_ring,'
                            'mpi_hello')
    switches_g.add_argument('--dev', dest='dev', action='store_true',
                            help='Installs development tools (vim, gdb)')
    maint_g = cli.add_argument_group('Maintenance')
    maint_g.add_argument('--clean', dest='cleanup', action='store_true',
                         help='Cleans up generated files in default directories.')

    cli.set_defaults(build=False)
    cli.set_defaults(convert=False)
    cli.set_defaults(print=False)
    cli.set_defaults(runtime_only=False)
    cli.set_defaults(upload=False)
    cli.set_defaults(gui=False)
    cli.set_defaults(docs=False)
    cli.set_defaults(jenkins=False)
    cli.set_defaults(cvode=False)
    cli.set_defaults(cppcheck=False)
    cli.set_defaults(iwyy=False)
    cli.set_defaults(gcovr=False)
    cli.set_defaults(mpi_benchmarks=False)
    cli.set_defaults(dev=False)
    cli.set_defaults(cleanup=False)
    args = cli.parse_args()

    if args.jenkins:
        args.ogs = ['off']

    c = list(itertools.product(args.format, args.ogs, args.pm, args.ompi,
                               args.cmake_args))
    if not args.print and not args.cleanup:
        print('Creating {} image definition(s)...'.format(len(c)))
    for build in c:
        __format = build[0]
        ogs_version = build[1]
        ogscm.config.set_package_manager(build[2])
        ompi = build[3]
        cmake_args = build[4].strip().split(' ')

        scif_installed = False

        # args checking
        if len(c) > 1 and args.file != '':
            print('--file can only be used when generating a single image definition')
            quit(1)
        if ogs_version == 'off' and len(cmake_args) > 0 and cmake_args[0] != '':
            cmake_args = []
            print('--cmake_args cannot be used with --ogs off! Ignoring!')
        if __format == 'singularity':
            if args.runtime_only:
                args.runtime_only = False
                print('--runtime-only cannot be used with --format singularity! '
                      'Ignoring!')
            if args.upload:
                print('--upload cannot be used with --format singularity! '
                      'Ignoring!')
            if args.convert:
                print('--convert cannot be used with --format singularity! '
                      'Ignoring!')

        if len(cmake_args) > 0:
            cmake_args_hash = hashlib.md5(
                ' '.join(cmake_args).encode('utf-8')).hexdigest()
            cmake_args_hash_short = cmake_args_hash[:8]

        commit_hash = '0'
        ogs_tag = ''

        name_image = args.base_image.replace(':', '_')
        name_start = 'gcc'
        if ogs_version != 'off':
            # Get git commit hash and construct image tag name
            repo, branch = ogs_version.split("@")
            url = f"https://api.github.com/repos/{repo}/commits?sha={branch}"
            response = requests.get(url)
            response_data = json.loads(response.text)
            commit_hash = response_data[0]['sha']
            ogs_tag = ogs_version.replace('/', '.').replace('@', '.')
            name_start = f'ogs-{commit_hash[:8]}'
        if args.compiler == 'clang':
            name_start = 'clang'

        name_openmpi = 'serial'
        if ompi != 'off':
            name_openmpi = f"openmpi-{ompi}"

        img_file = f"{name_image}-{name_start}-{name_openmpi}-{ogscm.config.g_package_manager.name.lower()}"
        img_folder = f"{name_image}/{name_start}/{name_openmpi}/{ogscm.config.g_package_manager.name.lower()}"
        if len(cmake_args) > 0:
            img_file += f'-cmake-{cmake_args_hash_short}'
        if args.gui:
            img_file += '-gui'
        if args.docs:
            img_file += '-docs'
        if ogs_version != 'off' and not args.runtime_only:
            img_file += '-dev'
        docker_repo = img_file
        img_file += '.sif'

        tag = f"{args.registry}/{docker_repo}:latest"

        ### Paths ###

        # Change working dir to ogscm
        old_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        if args.cleanup:
            shutil.rmtree(os.path.join(old_cwd, '_out'), ignore_errors=True)
            shutil.rmtree('_out', ignore_errors=True)
            print('Cleaned up!')
            exit(0)

        if not os.path.exists("_out"):
            os.makedirs("_out") # For .scif files

        if args.file != '':
            out_dir = args.out
            definition_file = args.file
        else:
            out_dir = os.path.join(old_cwd, f"{args.out}/{__format}/{img_folder}")
            if len(cmake_args) > 0:
                out_dir += f'/cmake-{cmake_args_hash_short}'
            images_out_dir = os.path.join(old_cwd, f"{args.out}/images")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            if not os.path.exists(images_out_dir):
                os.makedirs(images_out_dir)
            definition_file = 'Dockerfile'
            if __format == 'singularity':
                definition_file = 'Singularity.def'
            # definition_file = os.path.join(out_dir, definition_file)

        # Create definition
        hpccm.config.set_container_format(__format)

        # ------------------------------ recipe ------------------------------------
        Stage0 = hpccm.Stage()
        if args.runtime_only:
            Stage0.name = 'stage0'
        Stage0.baseimage(image=args.base_image)
        centos = hpccm.config.g_linux_distro == linux_distro.CENTOS

        # Get git info
        # local_git_hash = subprocess.check_output([
        #     'git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        Stage0 += comment(
            # "Generated with https://github.com/ufz/ogs-container-maker/commit/{0}".format(
            #     local_git_hash),
            f"Generated with ogs-container-maker {__version__}",
            reformat=False)

        if centos:
            Stage0 += user(user='root')
            Stage0 += packages(ospackages=['epel-release'])
        Stage0 += packages(ospackages=['wget', 'tar', 'curl'])

        # base compiler
        if args.compiler != 'off':
            if args.compiler_version == '':
                if args.compiler == 'clang':
                    args.compiler_version = '7'
                else:
                    args.compiler_version = None # Use default
            if args.compiler == 'clang':
                compiler = llvm(extra_repository=True, version=args.compiler_version)
            else:
                compiler = gnu(fortran=False, extra_repository=True,
                               version=args.compiler_version)
            toolchain = compiler.toolchain
            Stage0 += compiler
            if args.compiler == 'clang':
                Stage0 += packages(
                    apt=["clang-tidy-{}".format(args.compiler_version),
                         "clang-format-{}".format(args.compiler_version)],
                    yum=["llvm-toolset-{}-clang-tools-extra".format(args.compiler_version)]
                )

        if ompi != 'off':
            # Stage0 += ofed() OR mlnx_ofed(); is installed later on from debian archive
            # Stage0 += knem()
            Stage0 += ucx(version='1.5.1', cuda=False) #  knem='/usr/local/knem'
            Stage0 += packages(ospackages=['libpmi2-0-dev']) # req. for --with-pmi
            # req. for --with-psm2
            Stage0 += packages(ospackages=['libnuma1'])
            psm_deb_url = 'http://snapshot.debian.org/archive/debian/20181231T220010Z/pool/main'
            psm2_version = '11.2.68-4'
            Stage0 += shell(commands=[
                'cd /tmp',
                f'wget -nv {psm_deb_url}/libp/libpsm2/libpsm2-2_{psm2_version}_amd64.deb',
                f'wget -nv {psm_deb_url}/libp/libpsm2/libpsm2-dev_{psm2_version}_amd64.deb',
                'dpkg --install *.deb'
            ])

            # libibverbs
            # Available versions: http://snapshot.debian.org/binary/ibacm/
            # ibverbs_version = '21.0-1'
            # works on eve, eve has 17.2-3 installed nut this version is not available in snapshot.debian
            ib_deb_url = 'http://snapshot.debian.org/archive/debian/20180430T215634Z/pool/main'
            ibverbs_version = '17.1-2'
            ibverbs_packages = [
                'ibacm',
                'ibverbs-providers',
                'ibverbs-utils',
                'libibumad-dev',
                'libibumad3',
                'libibverbs-dev',
                'libibverbs1',
                'librdmacm-dev',
                'librdmacm1',
                'rdma-core',
                'rdmacm-utils'
            ]
            ibverbs_cmds = ['cd /tmp']
            for package in ibverbs_packages:
                ibverbs_cmds.extend([
                    f'wget -nv {ib_deb_url}/r/rdma-core/{package}_{ibverbs_version}_amd64.deb'
                ])
            ibverbs_cmds.append('dpkg --install *.deb')
            Stage0 += packages(ospackages=[
                'libnl-3-200',
                'libnl-route-3-200',
                'libnl-route-3-dev',
                'udev',
                'perl'
            ])
            Stage0 += shell(commands=ibverbs_cmds)

            mpicc = openmpi(version=ompi, cuda=False, toolchain=toolchain,
                            ldconfig=True,
                            ucx='/usr/local/ucx',
                            configure_opts=[
                                '--disable-getpwuid',
                                '--sysconfdir=/mnt/0'
                                '--with-slurm',  # used on taurus
                                '--with-pmi=/usr/include/slurm-wlm',
                                'CPPFLAGS=\'-I /usr/include/slurm-wlm\'',
                                '--with-pmi-libdir=/usr/lib/x86_64-linux-gnu',
                                # '--with-pmix',
                                '--with-psm2',
                                '--disable-pty-support',
                                '--enable-mca-no-build=btl-openib,plm-slurm',
                                # eve:
                                '--with-sge',
                                '--enable-mpirun-prefix-by-default',
                                '--enable-orterun-prefix-by-default',
                            ])
            toolchain = mpicc.toolchain
            Stage0 += mpicc
            # OpenMPI expects this program to exist, even if it's not used. Default is
            # "ssh : rsh", but that's not installed.
            Stage0 += shell(commands=[
                'mkdir /mnt/0',
                "echo 'plm_rsh_agent = false' >> /mnt/0/openmpi-mca-params.conf"
            ])

            Stage0 += label(metadata={
                'org.opengeosys.mpi': 'openmpi',
                'org.opengeosys.mpi.version': ompi
            })

            if args.mpi_benchmarks:
                Stage0 += pip(packages=['scif'])  # SCI-F
                scif_installed = True

                osu_app = scif(name='osu', file="_out/osu.scif")
                osu_app += osu_benchmarks(toolchain=toolchain, prefix='/scif/apps/osu')
                Stage0 += osu_app
                Stage0 += copy(src='files/openmpi', dest='/usr/local/mpi-examples')
                Stage0 += shell(commands=[
                    'mpicc -o /usr/local/bin/mpi-hello /usr/local/mpi-examples/hello.c',
                    'mpicc -o /usr/local/bin/mpi-ring /usr/local/mpi-examples/ring.c',
                    'mpicc -o /usr/local/bin/mpi-bw /usr/local/mpi-examples/bw.c',
                ])

        if ogs_version != 'off' or args.jenkins:
            Stage0 += ogs_base()
        if args.gui:
            Stage0 += packages(ospackages=[
                'mesa-common-dev', 'libgl1-mesa-dev', 'libglu1-mesa-dev', 'libxt-dev'
            ])
        if ogscm.config.g_package_manager == package_manager.CONAN:
            conan_user_home = '/opt/conan'
            if args.dev:
                conan_user_home = ''
            Stage0 += pm_conan(user_home=conan_user_home)
            if not args.jenkins:
                Stage0 += environment(variables={'CONAN_SYSREQUIRES_SUDO': 0})
        elif ogscm.config.g_package_manager == package_manager.SPACK:
            vtk_variants = '+osmesa'
            if ompi == 'off':
                vtk_variants += ' -mpi'
            spack_packages = [
                # 'vtk@8.1.2' + vtk_variants,
                'eigen@3.3.4',
                'boost@1.68.0'
            ]
            Stage0 += pm_spack(packages=spack_packages,
                               # ospackages=['libgl1-mesa-dev'],
                               repo='https://github.com/bilke/spack',
                               branch='patch-1')
            Stage0 += shell(commands=[
                '/opt/spack/bin/spack install --only dependencies vtk@8.1.2 +osmesa'
            ])
        elif ogscm.config.g_package_manager == package_manager.SYSTEM:
            # Use ldconfig to set library search path (instead of
            # LD_LIBRARY_PATH) as host var overwrites container var. See
            # https://github.com/sylabs/singularity/pull/2669
            Stage0 += boost(version='1.66.0')  # header only?
            Stage0 += environment(variables={'BOOST_ROOT': '/usr/local/boost'})
            Stage0 += eigen()
            vtk_cmake_args = [
                '-DVTK_Group_StandAlone=OFF',
                '-DVTK_Group_Rendering=OFF',
                '-DModule_vtkIOXML=ON'
            ]
            Stage0 += vtk(cmake_args=vtk_cmake_args, toolchain=toolchain,
                          ldconfig=True)
            if ompi != 'off':
                Stage0 += petsc(ldconfig=True)
        if args.cvode:
            Stage0 += cvode()
        if args.cppcheck:
            Stage0 += cppcheck()
        if args.iwyy and args.compiler == 'clang':
            Stage0 += iwyy(clang_version=args.compiler_version)
        if args.docs:
            Stage0 += packages(
                ospackages=['doxygen', 'graphviz', 'texlive-base'])
        if args.gcovr:
            Stage0 += pip(pip='pip3', packages=['gcovr'])

        if args.dev:
            Stage0 += packages(ospackages=['neovim', 'gdb', 'silversearcher-ag',
                                           'ssh-client', 'less'])

        if ogs_version != 'off':
            if args.cvode:
                cmake_args.append('-DOGS_USE_CVODE=ON')
            if args.gui:
                cmake_args.append('-DOGS_BUILD_GUI=ON')

            if not scif_installed:
                Stage0 += pip(packages=['scif'])  # SCI-F
                scif_installed = True
            Stage0 += raw(docker='ARG OGS_COMMIT_HASH=0')
            ogs_app = scif(name='ogs', file="_out/ogs.scif")
            ogs_app += ogs(version=ogs_version, toolchain=toolchain,
                           prefix='/scif/apps/ogs',
                           cmake_args=cmake_args,
                           parallel=math.ceil(multiprocessing.cpu_count() / 2),
                           skip_lfs=True, remove_build=True,
                           remove_source=True)  # TODO: maybe only in runtime image?
            Stage0 += ogs_app

        if args.jenkins:
            Stage0 += ccache(cache_size='15G')
            Stage0 += jenkins_node()

        stages_string = str(Stage0)

        if args.runtime_only:
            Stage1 = hpccm.Stage()
            Stage1.baseimage(image=args.base_image)
            Stage1 += Stage0.runtime()
            if scif_installed:
                Stage1 += pip(packages=['scif'])  # Install scif in runtime too
            stages_string += "\n\n" + str(Stage1)

        # ---------------------------- recipe end ----------------------------------

        definition_file_path = os.path.join(out_dir, definition_file)
        with open(definition_file_path, 'w') as f:
            print(stages_string, file=f)
        if args.print:
            print(stages_string)
        else:
            print(f'Created definition {definition_file_path}')

        # Create image
        if not args.build:
            continue

        if __format == 'singularity':
            subprocess.run(f"sudo `which singularity` build --force {images_out_dir}/{img_file} "
                f"{definition_file_path}", shell=True)
            subprocess.run(f"sudo chown $USER:$USER {images_out_dir}/{img_file}", shell=True)
            continue

        build_cmd = (f"docker build --build-arg OGS_COMMIT_HASH={commit_hash} "
                     f"-t {tag} -f {definition_file_path} .")
        print(f"Running: {build_cmd}")
        subprocess.run(build_cmd, shell=True)
        if args.upload:
            subprocess.run(f"docker push {tag}", shell=True)
        if args.convert:
            subprocess.run(
                # Requires following entries in visudo:
                #   jenkins ALL = NOPASSWD: /usr/bin/singularity
                # Echo empty password because of
                #   sudo: no tty present and no askpass program specified
                #   See https://stackoverflow.com/a/29685946/80480
                f"echo '' | sudo -S singularity build --force {images_out_dir}/{img_file} docker-daemon:{tag}",
                shell=True)

if __name__ == "__main__": # pragma: no cover
    main()
