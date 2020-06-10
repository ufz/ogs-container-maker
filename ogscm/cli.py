#!/usr/bin/env python3

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0, 3.1.4, 4.0.1
#  Eve: 1.8.8, 1.10.2, 2.1.1, 4.0.0
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import itertools
import json
import os
import re
import requests
import subprocess
import sys
import yaml

from packaging import version

import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import packages, mlnx_ofed, knem, ucx, openmpi, \
    boost, pip, scif, llvm, gnu, ofed, cmake, slurm_pmi2, pmix
from hpccm.primitives import baseimage, comment, user, environment, raw, \
    label, shell, copy

import ogscm
from ogscm.cli_args import Cli_Args
from ogscm.config import package_manager
from ogscm.container_info import container_info
from ogscm.version import __version__
from ogscm.building_blocks import ccache, cppcheck, cvode, eigen, iwyy, \
    jenkins_node, ogs_base, ogs, osu_benchmarks, petsc, pm_conan, vtk, \
    pm_spack, paraview


def main():  # pragma: no cover
    cli = Cli_Args()
    args = cli.parse_args()

    if args.jenkins or args.gitlab:
        args.ogs = ['off']
    if args.deploy != '':
        args.build = True
        args.convert = True

    cwd = os.getcwd()

    c = list(
        itertools.product(args.format, args.ogs, args.pm, args.ompi,
                          args.cmake_args))
    if not args.print and not args.cleanup:
        print('Creating {} image definition(s)...'.format(len(c)))
    for build in c:
        __format = build[0]
        ogs_version = build[1]
        ogscm.config.set_package_manager(build[2])
        ompi = build[3]
        cmake_args = build[4].strip().split(' ')

        # args checking
        if len(c) > 1 and args.file != '':
            print(
                '--file can only be used when generating a single image definition'
            )
            quit(1)
        if (len(c) > 1 and args.sif_file != '') or (args.sif_file != '' and args.convert == False):
            print(
                '--sif_file can only be used when generating a single image '
                'definition and --convert is given'
            )
            quit(1)
        if ogs_version == 'off' and len(
                cmake_args) > 0 and cmake_args[0] != '':
            cmake_args = []
            print('--cmake_args cannot be used with --ogs off! Ignoring!')
        if __format == 'singularity':
            if args.runtime_only:
                args.runtime_only = False
                print(
                    '--runtime-only cannot be used with --format singularity! '
                    'Ignoring!')
            if args.upload:
                print('--upload cannot be used with --format singularity! '
                      'Ignoring!')
            if args.convert:
                print('--convert cannot be used with --format singularity! '
                      'Ignoring!')

        info = container_info(build, args)
        if args.cleanup:
            info.cleanup()
            exit(0)
        info.make_dirs()

        # Create definition
        hpccm.config.set_container_format(__format)

        # ------------------------------ recipe -------------------------------
        Stage0 = hpccm.Stage()
        Stage0 += raw(docker='# syntax=docker/dockerfile:experimental')

        if args.runtime_only:
            Stage0.name = 'build'
        Stage0 += baseimage(image=args.base_image, _as='build')

        Stage0 += comment(f"Generated with ogs-container-maker {__version__}",
                          reformat=False)

        Stage0 += packages(ospackages=['wget', 'tar', 'curl', 'make'])

        # base compiler
        if args.compiler != 'off':
            if args.compiler_version == '':
                if args.compiler == 'clang':
                    args.compiler_version = '8'
                else:
                    args.compiler_version = None  # Use default
            if args.compiler == 'clang':
                compiler = llvm(extra_repository=True,
                                extra_tools=True,
                                version=args.compiler_version)
            else:
                compiler = gnu(fortran=False,
                               extra_repository=True,
                               version=args.compiler_version)
            toolchain = compiler.toolchain
            Stage0 += compiler
            # Upgrade stdc++ lib after installing new compiler
            # https://stackoverflow.com/a/46613656/80480
            if args.compiler == 'gcc' and args.compiler_version is not None:
                Stage0 += packages(apt=['libstdc++6'])

        # Prepare runtime stage
        Stage1 = hpccm.Stage()
        Stage1.baseimage(image=args.base_image)

        # Install scif in all stages
        Stage0 += pip(packages=['scif'], pip='pip3')
        Stage1 += pip(packages=['scif'], pip='pip3')

        if ompi != 'off':
            mpicc = object
            if False:  # eve:
                # Stage0 += ofed() OR mlnx_ofed(); is installed later on from debian archive
                # Stage0 += knem()
                Stage0 += ucx(version='1.5.1',
                              cuda=False)  #  knem='/usr/local/knem'
                Stage0 += packages(ospackages=['libpmi2-0-dev'
                                               ])  # req. for --with-pmi
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
                    'ibacm', 'ibverbs-providers', 'ibverbs-utils',
                    'libibumad-dev', 'libibumad3', 'libibverbs-dev',
                    'libibverbs1', 'librdmacm-dev', 'librdmacm1', 'rdma-core',
                    'rdmacm-utils'
                ]
                ibverbs_cmds = ['cd /tmp']
                for package in ibverbs_packages:
                    ibverbs_cmds.extend([
                        f'wget -nv {ib_deb_url}/r/rdma-core/{package}_{ibverbs_version}_amd64.deb'
                    ])
                ibverbs_cmds.append('dpkg --install *.deb')
                Stage0 += packages(ospackages=[
                    'libnl-3-200', 'libnl-route-3-200', 'libnl-route-3-dev',
                    'udev', 'perl'
                ])
                Stage0 += shell(commands=ibverbs_cmds)

                mpicc = openmpi(
                    version=ompi,
                    cuda=False,
                    toolchain=toolchain,
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
            else:
                Stage0 += ucx(version='1.6.1' ,cuda=False)
                Stage0 += slurm_pmi2(version='17.02.11')
                pmix_version = True
                if version.parse(ompi) >= version.parse('4'):
                    Stage0 += pmix()
                    pmix_version = '/usr/local/pmix'

                mpicc = openmpi(version=ompi,
                                cuda=False,
                                infiniband=False,
                                pmi='/usr/local/slurm-pmi2',
                                pmix=pmix_version,
                                ucx='/usr/local/ucx')

            toolchain = mpicc.toolchain
            Stage0 += mpicc
            # OpenMPI expects this program to exist, even if it's not used.
            # Default is "ssh : rsh", but that's not installed.
            Stage0 += shell(commands=[
                'mkdir /mnt/0',
                "echo 'plm_rsh_agent = false' >> /mnt/0/openmpi-mca-params.conf"
            ])

            Stage0 += label(
                metadata={
                    'org.opengeosys.mpi': 'openmpi',
                    'org.opengeosys.mpi.version': ompi
                })

            if args.mpi_benchmarks:
                osu_app = scif(name='osu', file="_out/osu.scif")
                osu_app += osu_benchmarks(toolchain=toolchain,
                                          prefix='/scif/apps/osu')
                Stage0 += osu_app
                Stage0 += copy(src='ogscm/files/openmpi',
                               dest='/usr/local/mpi-examples')
                Stage0 += shell(commands=[
                    'mpicc -o /usr/local/bin/mpi-hello /usr/local/mpi-examples/hello.c',
                    'mpicc -o /usr/local/bin/mpi-ring /usr/local/mpi-examples/ring.c',
                    'mpicc -o /usr/local/bin/mpi-bw /usr/local/mpi-examples/bw.c',
                ])
                Stage1 += copy(_from='build',
                               src='/usr/local/bin/mpi_*',
                               dest='/usr/local/bin/')

        Stage0 += ogs_base()
        if args.gui:
            Stage0 += packages(ospackages=[
                'mesa-common-dev', 'libgl1-mesa-dev', 'libglu1-mesa-dev',
                'libxt-dev'
            ])
        if ogscm.config.g_package_manager == package_manager.CONAN:
            Stage0 += cmake(eula=True, version='3.16.6')
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
            Stage0 += pm_spack(
                packages=spack_packages,
                # ospackages=['libgl1-mesa-dev'],
                repo='https://github.com/bilke/spack',
                branch='patch-1')
            Stage0 += shell(commands=[
                '/opt/spack/bin/spack install --only dependencies vtk@8.1.2 +osmesa'
            ])
        elif ogscm.config.g_package_manager == package_manager.SYSTEM:
            Stage0 += cmake(eula=True, version='3.16.6')
            # Use ldconfig to set library search path (instead of
            # LD_LIBRARY_PATH) as host var overwrites container var. See
            # https://github.com/sylabs/singularity/pull/2669
            # Stage0 += boost(version='1.66.0')  # header only?
            Stage0 += packages(apt=['libboost-dev'], yum=['boost-devel'], epel=True)
            # Stage0 += environment(variables={'BOOST_ROOT': '/usr/local/boost'})
            Stage0 += eigen()
            vtk_cmake_args = [
                '-DModule_vtkIOXML=ON',
                '-DVTK_Group_Rendering=OFF',
                '-DVTK_Group_StandAlone=OFF'
            ]
            if args.gui:
                Stage0 += packages(apt=[
                        'libgeotiff-dev',
                        'libshp-dev',
                        'libqt5x11extras5-dev',
                        'libqt5xmlpatterns5-dev',
                        'qt5-default'
                    ],
                    yum=[
                        'libgeotiff-devel',
                        'shapelib-devel',
                        'qt5-qtbase',
                        'qt5-qtxmlpatterns',
                        'qt5-qtx11extras'
                    ])
                vtk_cmake_args = [
                    '-DVTK_BUILD_QT_DESIGNER_PLUGIN=OFF',
                    '-DVTK_Group_Qt=ON',
                    '-DVTK_QT_VERSION=5'
                ]
            if args.insitu:
                if args.gui:
                    print('--gui can not be used with --insitu!')
                    exit(1)
                Stage0 += paraview(cmake_args=['-D PARAVIEW_USE_PYTHON=ON'],
                                   edition='CATALYST',
                                   ldconfig=True,
                                   toolchain=toolchain)
            else:
                Stage0 += vtk(cmake_args=vtk_cmake_args,
                              toolchain=toolchain,
                              ldconfig=True)
            if ompi != 'off':
                Stage0 += petsc(version='3.11.3', ldconfig=True)
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
            Stage0 += packages(ospackages=[
                'neovim', 'gdb', 'silversearcher-ag', 'ssh-client', 'less'
            ])

        if args.pip:
            Stage0 += pip(packages=args.pip, pip='pip3')
            Stage1 += pip(packages=args.pip, pip='pip3')

        if args.packages:
            Stage0 += packages(ospackages=args.packages)

        definition_file_path = os.path.join(info.out_dir, info.definition_file)
        if ogs_version != 'off':
            mount_args = ''
            if args.ccache:
                Stage0 += ccache(cache_size='15G')
                mount_args = f'{mount_args} --mount=type=cache,target=/opt/ccache,id=ccache'
            if args.cvode:
                cmake_args.append('-DOGS_USE_CVODE=ON')
            if args.gui:
                cmake_args.append('-DOGS_BUILD_GUI=ON')
            if args.insitu:
                cmake_args.append('-DOGS_INSITU=ON')

            Stage0 += raw(docker=f"ARG OGS_COMMIT_HASH={info.commit_hash}")

            scif_file = f"{info.out_dir}/ogs.scif"
            if info.ogsdir:
                context_path_size = len(ogs_version)
                print(f"chdir to {ogs_version}")
                os.chdir(ogs_version)
                mount_args = f'{mount_args} --mount=type=bind,target=/scif/apps/ogs/src,rw'
                scif_file = f"{info.out_dir[context_path_size+1:]}/ogs.scif"
                definition_file_path = f"{info.out_dir[context_path_size+1:]}/{info.definition_file}"

            ogs_app = scif(_arguments=mount_args, name='ogs', file=scif_file)
            ogs_app += ogs(repo=info.repo,
                           branch=info.branch,
                           commit=info.commit_hash,
                           git_version=info.git_version,
                           toolchain=toolchain,
                           prefix='/scif/apps/ogs',
                           cmake_args=cmake_args,
                           parallel=args.parallel,
                           skip_lfs=True,
                           remove_build=True,
                           remove_source=True)
            Stage0 += ogs_app

        if args.jenkins:
            Stage0 += ccache(cache_size='15G')
            Stage0 += jenkins_node()

        stages_string = str(Stage0)

        if args.runtime_only:
            Stage1 += Stage0.runtime()
            if args.compiler == 'gcc' and args.compiler_version != None:
                Stage1 += packages(apt=['libstdc++6'])
            stages_string += "\n\n" + str(Stage1)

        # ---------------------------- recipe end -----------------------------
        with open(definition_file_path, 'w') as f:
            print(stages_string, file=f)
        if args.print:
            print(stages_string)
        else:
            print(f'Created definition {os.path.abspath(definition_file_path)}')

        # Create image
        if not args.build:
            continue

        if __format == 'singularity':
            subprocess.run(
                f"sudo `which singularity` build --force {info.images_out_dir}/{info.img_file}.sif"
                f"{definition_file_path}",
                shell=True)
            subprocess.run(
                f"sudo chown $USER:$USER {info.images_out_dir}/{info.img_file}.sif",
                shell=True)
            # TODO: adapt this to else
            continue

        build_cmd = (f"DOCKER_BUILDKIT=1 docker build "
                     f"-t {info.tag} -f {definition_file_path} .")
        print(f"Running: {build_cmd}")
        subprocess.run(build_cmd, shell=True)
        inspect_out = subprocess.check_output(
            f"docker inspect {info.tag} | grep Id",
            shell=True).decode(sys.stdout.encoding)
        image_id = re.search('sha256:(\w*)', inspect_out).group(1)
        image_id_short = image_id[0:12]
        if args.upload:
            subprocess.run(f"docker push {info.tag}", shell=True)
        if args.sif_file:
            image_file = f'{info.images_out_dir}/{args.sif_file}'
        else:
            image_file = f'{info.images_out_dir}/{info.img_file}-{image_id_short}.sif'
        if args.convert and not os.path.exists(image_file):
            subprocess.run(
                f"cd {cwd} && singularity build --force {image_file} docker-daemon:{info.tag}",
                shell=True)

        # Deploy image
        if not args.deploy:
            continue

        deploy_config_filename = f'{cwd}/config/deploy_hosts.yml'
        if not os.path.isfile(deploy_config_filename):
            print(
                f'ERROR: {deploy_config_filename} not found but required for deploying!'
            )
            exit(1)

        with open(deploy_config_filename, 'r') as ymlfile:
            deploy_config = yaml.load(ymlfile, Loader=yaml.FullLoader)
        if not args.deploy == 'ALL' and not args.deploy in deploy_config:
            print(f'ERROR: Deploy host "{args.deploy}" not found in config!')
            exit(1)
        deploy_hosts = {}
        if args.deploy == 'ALL':
            deploy_hosts = deploy_config
        else:
            deploy_hosts[args.deploy] = deploy_config[args.deploy]
        for deploy_host in deploy_hosts:
            deploy_info = deploy_hosts[deploy_host]
            print(f'Deploying to {deploy_info} ...')
            proxy_cmd = ''
            user_cmd = ''
            if 'user' in deploy_info:
                user_cmd = f"{deploy_info['user']}@"
            if 'proxy' in deploy_info:
                proxy_cmd = f"-e 'ssh -A -J {user_cmd}{deploy_info['proxy']}'"
                print(proxy_cmd)
            print(
                subprocess.check_output(
                    f"rsync -c -v {proxy_cmd} {image_file} {user_cmd}{deploy_info['host']}:{deploy_info['dest_dir']}",
                    shell=True).decode(sys.stdout.encoding))


if __name__ == "__main__":  # pragma: no cover
    main()
