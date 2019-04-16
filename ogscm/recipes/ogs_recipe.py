import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import llvm, gnu, packages, mlnx_ofed, knem, ucx, \
    openmpi
from hpccm.primitives import label

import ogscm
from ogscm.building_blocks import osu_benchmarks, ogs_base
from ogscm.recipes import recipe_base


class ogs_recipe(recipe_base):

    def __init__(self, **kwargs):
        super(ogs_recipe, self).__init__()

        # base compiler
        if self.__args.compiler_version == '':
            if self.__args.clang:
                if hpccm.config.g_linux_distro == linux_distro.CENTOS:
                    # installs llvm-toolset-7-clang which is clang 5.0.1
                    self.__args.compiler_version = '7'
                else:
                    self.__args.compiler_version = '5.0'
            else:
                self.__args.compiler_version = '6'
        if self.__args.clang:
            compiler = llvm(extra_repository=True, version=self.__args.compiler_version)
        else:
            compiler = gnu(fortran=False, extra_repository=True,
                           version=self.__args.compiler_version)
        toolchain = compiler.toolchain
        self.__Stage0 += compiler
        if self.__args.clang:
            self.__Stage0 += packages(
                apt=["clang-tidy-{}".format(self.__args.compiler_version),
                     "clang-format-{}".format(self.__args.compiler_version)],
                yum=["llvm-toolset-{}-clang-tools-extra".format(self.__args.compiler_version)]
            )

        if ompi != 'off':
            self.__Stage0 += mlnx_ofed()  # version='3.4-1.0.0.0'
            self.__Stage0 += knem()
            self.__Stage0 += ucx(cuda=False, knem='/usr/local/knem')

            mpicc = openmpi(version=ompi, cuda=False, ucx='/usr/local/ucx',
                            configure_opts=[
                                '--with-slurm',
                                '--enable-mca-no-build=btl-openib,plm-slurm'
                            ],
                            # ospackages=['libslurm-dev'],
                            toolchain=toolchain)
            toolchain = mpicc.toolchain
            self.__Stage0 += mpicc

            self.__Stage0 += label(metadata={
                'org.opengeosys.mpi': 'openmpi',
                'org.opengeosys.mpi.version': ompi
            })

            if True:  # TODO configurable?
                self.__Stage0 += osu_benchmarks()

        self.__Stage0 += ogs_base()
        if self.__args.gui:
            self.__Stage0 += packages(ospackages=[
                'mesa-common-dev', 'libgl1-mesa-dev', 'libxt-dev'
            ])
        if ogscm.config.g_package_manager == package_manager.CONAN:
            conan_user_home = '/opt/conan'
            if self.__args.dev:
                conan_user_home = ''
            self.__Stage0 += pm_conan(user_home=conan_user_home)
            if not self.__args.jenkins:
                self.__Stage0 += environment(variables={'CONAN_SYSREQUIRES_SUDO': 0})
        elif ogscm.config.g_package_manager == package_manager.SYSTEM:
            self.__Stage0 += boost()  # header only?
            self.__Stage0 += environment(variables={'BOOST_ROOT': '/usr/local/boost'})
            self.__Stage0 += eigen()
            vtk_cmake_args = [
                '-DVTK_Group_StandAlone=OFF',
                '-DVTK_Group_Rendering=OFF',
                '-DModule_vtkIOXML=ON'
            ]
            self.__Stage0 += vtk(cmake_args=vtk_cmake_args, toolchain=toolchain)
            if ompi != 'off':
                self.__Stage0 += petsc()
        if self.__args.cvode:
            self.__Stage0 += cvode()
        if self.__args.cppcheck:
            self.__Stage0 += cppcheck()
        if self.__args.iwyy and self.__args.clang:
            self.__Stage0 += iwyy(clang_version=self.__args.compiler_version)
        if self.__args.docs:
            self.__Stage0 += packages(
                ospackages=['doxygen', 'graphviz', 'texlive-base'])
        if self.__args.gcovr:
            self.__Stage0 += pip(pip='pip3', packages=['gcovr'])

        if self.__args.dev:
            self.__Stage0 += packages(ospackages=['neovim', 'gdb', 'silversearcher-ag',
                                           'ssh-client', 'less'])

        if ogs_version != 'off':
            if self.__args.cvode:
                cmake_args.append('-DOGS_USE_CVODE=ON')
            if self.__args.gui:
                cmake_args.append('-DOGS_BUILD_GUI=ON')

            self.__Stage0 += pip(packages=['scif'])  # SCI-F
            self.__Stage0 += raw(docker='ARG OGS_COMMIT_HASH=0')
            ogs_app = scif(name='ogs')
            ogs_app += ogs(version=ogs_version, toolchain=toolchain,
                           prefix='/scif/apps/ogs',
                           cmake_args=cmake_args,
                           parallel=math.ceil(multiprocessing.cpu_count() / 2),
                           skip_lfs=True, remove_build=True,
                           remove_source=True)  # TODO: maybe only in runtime image?
            self.__Stage0 += ogs_app

        if self.__args.jenkins:
            self.__Stage0 += ccache(cache_size='15G')
            self.__Stage0 += packages(
                ospackages=['sudo'])  # For user switching back to root
            self.__Stage0 += jenkins_node()
