import ogscm
from ogscm.building_blocks.ogs_base import ogs_base
from ogscm.config import package_manager
from hpccm.building_blocks import (
    boost,
    cmake,
    generic_autotools,
    generic_cmake,
    packages,
    pip,
    scif,
)
from ogscm.building_blocks.pm_conan import pm_conan

import hpccm
from hpccm import linux_distro
from hpccm.primitives import environment, raw
from ogscm.building_blocks.paraview import paraview
from ogscm.building_blocks.ccache import ccache
import os
from ogscm.building_blocks.ogs import ogs


class ogs_recipe(object):
    def __init__(self, Stage0, Stage1, args, info, toolchain, **kwargs):

        cmake_args = args.cmake_args.strip().split(" ")

        if args.ogs != "clean":
            Stage0 += ogs_base()
        if args.gui:
            Stage0 += packages(
                apt=[
                    "mesa-common-dev",
                    "libgl1-mesa-dev",
                    "libglu1-mesa-dev",
                    "libxt-dev",
                ],
                yum=[
                    "mesa-libOSMesa-devel",
                    "mesa-libGL-devel",
                    "mesa-libGLU-devel",
                    "libXt-devel",
                ],
            )
            Stage1 += packages(
                apt=[
                    "libosmesa6",
                    "libgl1-mesa-glx",
                    "libglu1-mesa",
                    "libxt6",
                    "libopengl0",
                ],
                yum=["mesa-libOSMesa", "mesa-libGL", "mesa-libGLU", "libXt"],
            )
        if args.ogs != "clean":
            if ogscm.config.g_package_manager == package_manager.CONAN:
                Stage0 += cmake(eula=True, version="3.16.6")
                conan_user_home = "/opt/conan"
                if args.dev:
                    conan_user_home = ""
                Stage0 += pm_conan(user_home=conan_user_home)
                Stage0 += environment(variables={"CONAN_SYSREQUIRES_SUDO": 0})
            elif ogscm.config.g_package_manager == package_manager.SYSTEM:
                Stage0 += cmake(eula=True, version="3.16.6")
                Stage0 += boost(version="1.66.0", bootstrap_opts=["headers"])
                Stage0 += environment(variables={"BOOST_ROOT": "/usr/local/boost"})
                vtk_cmake_args = [
                    "-DModule_vtkIOXML=ON",
                    "-DVTK_Group_Rendering=OFF",
                    "-DVTK_Group_StandAlone=OFF",
                ]
                if args.gui:
                    Stage0 += packages(
                        apt=[
                            "libgeotiff-dev",
                            "libshp-dev",
                            "libnetcdf-c++4-dev",
                            "libqt5x11extras5-dev",
                            "libqt5xmlpatterns5-dev",
                            "qt5-default",
                        ],
                        yum=[
                            "libgeotiff-devel",
                            "shapelib-devel",
                            "netcdf-devel",
                            "qt5-qtbase-devel",
                            "qt5-qtxmlpatterns-devel",
                            "qt5-qtx11extras-devel",
                        ],
                    )
                    Stage1 += packages(
                        apt=[
                            "geotiff-bin",
                            "shapelib",
                            "libnetcdf-c++4",
                            "libqt5x11extras5",
                            "libqt5xmlpatterns5",
                            "qt5-default",
                        ],
                        yum=[
                            "libgeotiff",
                            "shapelib",
                            "netcdf",
                            "qt5-qtbase",
                            "qt5-qtxmlpatterns",
                            "qt5-qtx11extras",
                        ],
                    )
                    vtk_cmake_args = [
                        "-DVTK_BUILD_QT_DESIGNER_PLUGIN=OFF",
                        "-DVTK_Group_Qt=ON",
                        "-DVTK_QT_VERSION=5",
                    ]
                if hpccm.config.g_linux_distro == linux_distro.CENTOS:
                    # otherwise linker error, maybe due to gcc 10?
                    vtk_cmake_args.extend(
                        [
                            "-DBUILD_SHARED_LIBS=OFF",
                            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",
                        ]
                    )
                if args.insitu:
                    if args.gui:
                        print("--gui can not be used with --insitu!")
                        exit(1)
                    Stage0 += paraview(
                        cmake_args=["-DPARAVIEW_USE_PYTHON=ON"],
                        edition="CATALYST",
                        ldconfig=True,
                        toolchain=toolchain,
                        version="v5.8.1",
                    )
                else:
                    if toolchain.CC == "mpicc":
                        vtk_cmake_args.extend(
                            [
                                "-D Module_vtkIOParallelXML=ON",
                                "-D Module_vtkParallelMPI=ON",
                            ]
                        )
                    Stage0 += generic_cmake(
                        cmake_opts=vtk_cmake_args,
                        devel_environment={"VTK_ROOT": "/usr/local/vtk"},
                        directory="VTK-8.2.0",
                        ldconfig=True,
                        prefix="/usr/local/vtk",
                        toolchain=toolchain,
                        url="https://www.vtk.org/files/release/8.2/VTK-8.2.0.tar.gz",
                    )
                if args.ompi != "off":
                    Stage0 += packages(yum=["diffutils"])
                    Stage0 += generic_autotools(
                        configure_opts=[
                            f"CC={toolchain.CC}",
                            f"CXX={toolchain.CXX}",
                            "--CFLAGS='-O3'",
                            "--CXXFLAGS='-O3'",
                            "--FFLAGS='-O3'",
                            "--with-debugging=no",
                            "--with-fc=0",
                            "--download-f2cblaslapack=1",
                        ],
                        devel_environment={"PETSC_DIR": "/usr/local/petsc"},
                        directory="petsc-3.11.3",
                        ldconfig=True,
                        preconfigure=["sed -i -- 's/python/python3/g' configure"],
                        prefix="/usr/local/petsc",
                        toolchain=toolchain,
                        url="http://ftp.mcs.anl.gov/pub/petsc/release-snapshots/"
                        "petsc-lite-3.11.3.tar.gz",
                    )

                Stage0 += generic_cmake(
                    devel_environment={
                        "Eigen3_ROOT": "/usr/local/eigen",
                        "Eigen3_DIR": "/usr/local/eigen",
                    },
                    directory="eigen-3.3.7",
                    prefix="/usr/local/eigen",
                    url="https://gitlab.com/libeigen/eigen/-/archive/3.3.7/eigen-3.3.7.tar.gz",
                )
        if args.cvode:
            Stage0 += generic_cmake(
                cmake_opts=[
                    "-D EXAMPLES_INSTALL=OFF",
                    "-D BUILD_SHARED_LIBS=OFF",
                    "-D CMAKE_POSITION_INDEPENDENT_CODE=ON",
                ],
                devel_environment={"CVODE_ROOT": "/usr/local/cvode"},
                directory="cvode-2.8.2",
                prefix="/usr/local/cvode",
                url="https://github.com/ufz/cvode/archive/2.8.2.tar.gz",
            )

        if args.cppcheck:
            Stage0 += generic_cmake(
                devel_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
                directory="cppcheck-809a769c690d8ab6fef293e41a29c8490512866e",
                prefix="/usr/local/cppcheck",
                runtime_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
                url="https://github.com/danmar/cppcheck/archive/809a769c690d8ab6fef293e41a29c8490512866e.tar.gz",
            )

        if args.iwyy and args.compiler == "clang":
            Stage0 += packages(
                ospackages=[
                    "libncurses5-dev",
                    "zlib1g-dev",
                    f"llvm-{args.compiler_version}-dev",
                    f"libclang-{args.compiler_version}-dev",
                ]
            )
            Stage0 += generic_cmake(
                cmake_opts=[
                    f"-D IWYU_LLVM_ROOT_PATH=/usr/lib/llvm-{args.compiler_version}"
                ],
                devel_environment={"PATH": "/usr/local/iwyy/bin:$PATH"},
                directory=f"include-what-you-use-clang_{args.compiler_version}.0",
                prefix="/usr/local/iwyy",
                runtime_environment={"PATH": "/usr/local/iwyy/bin:$PATH"},
                url="https://github.com/include-what-you-use/include-what-"
                f"you-use/archive/clang_{args.compiler_version}.0.tar.gz",
            )
        if args.docs:
            Stage0 += packages(ospackages=["doxygen", "graphviz", "texlive-base"])
        if args.gcovr:
            Stage0 += pip(pip="pip3", packages=["gcovr"])

        if args.dev:
            Stage0 += packages(
                ospackages=["neovim", "gdb", "silversearcher-ag", "ssh-client", "less"]
            )

        if args.pip:
            Stage0 += pip(packages=args.pip, pip="pip3")
            Stage1 += pip(packages=args.pip, pip="pip3")

        if args.packages:
            Stage0 += packages(ospackages=args.packages)

        if args.tfel:
            Stage0 += generic_cmake(
                directory="tfel-TFEL-3.3.0",
                ldconfig=True,
                url="https://github.com/thelfer/tfel/archive/TFEL-3.3.0.tar.gz",
                prefix="/usr/local/tfel",
            )
            Stage0 += environment(variables={"TFELHOME": "/usr/local/tfel"})

        if args.ccache:
            Stage0 += ccache(cache_size="15G")
        if args.ogs != "off" and args.ogs != "clean":
            mount_args = ""
            if args.ccache:
                mount_args = (
                    f"{mount_args} --mount=type=cache,target=/opt/ccache,id=ccache"
                )
            if args.cvode:
                cmake_args.append("-DOGS_USE_CVODE=ON")
            if args.gui:
                cmake_args.append("-DOGS_BUILD_GUI=ON")
            if args.insitu:
                cmake_args.append("-DOGS_INSITU=ON")

            Stage0 += raw(docker=f"ARG OGS_COMMIT_HASH={info.commit_hash}")

            if info.ogsdir:
                print(f"chdir to {args.ogs}")
                os.chdir(args.ogs)
                mount_args = (
                    f"{mount_args} --mount=type=bind,target=/scif/apps/ogs/src,rw"
                )

            ogs_app = scif(_arguments=mount_args, name="ogs", file=info.scif_file)
            ogs_app += ogs(
                repo=info.repo,
                branch=info.branch,
                commit=info.commit_hash,
                git_version=info.git_version,
                toolchain=toolchain,
                prefix="/scif/apps/ogs",
                cmake_args=cmake_args,
                parallel=args.parallel,
                remove_build=True,
                remove_source=True,
            )
            Stage0 += ogs_app
