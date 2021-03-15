from copy import copy

import json
import math
import multiprocessing
import re
import requests

from ogscm.building_blocks.ogs_base import ogs_base
from hpccm.building_blocks import (
    boost,
    cmake,
    generic_autotools,
    generic_cmake,
    hdf5,
    mkl,
    packages,
    pip,
    scif,
)
from ogscm.building_blocks.pm_conan import pm_conan

import hpccm
from ogscm.building_blocks.paraview import paraview
from ogscm.building_blocks.ccache import ccache
from hpccm.primitives import comment, copy, environment, raw, shell
from hpccm import linux_distro
import os
from ogscm.building_blocks.ogs import ogs
import subprocess
import hashlib

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)
parse_g.add_argument(
    "--pm",
    type=str,
    choices=["system", "conan", "off"],
    default="system",
    help="Package manager to install third-party " "dependencies",
)
parse_g.add_argument(
    "--ogs",
    type=str,
    default="ogs/ogs@master",
    help="OGS repo on gitlab.opengeosys.org in the form 'user/repo@branch' "
    "OR 'user/repo@@commit' to checkout a specific commit "
    "OR a path to a local subdirectory to the git cloned OGS sources "
    "OR 'off' to disable OGS building "
    "OR 'clean' to disable OGS and all its dev dependencies",
)
parse_g.add_argument(
    "--cmake_args",
    type=str,
    default="",
    help="CMake argument set has to be quoted and **must**"
    " start with a space. e.g. --cmake_args ' -DFIRST="
    "TRUE -DFOO=BAR'",
)
parse_g.add_argument(
    "--ccache",
    dest="ccache",
    action="store_true",
    help="Enables ccache build caching.",
)
parse_g.add_argument(
    "--parallel",
    "-j",
    type=str,
    default=math.ceil(multiprocessing.cpu_count() / 2),
    help="The number of cores to use for compilation.",
)
parse_g.add_argument(
    "--gui",
    dest="gui",
    action="store_true",
    help="Builds the GUI (Data Explorer)",
)
parse_g.add_argument(
    "--docs",
    dest="docs",
    action="store_true",
    help="Setup documentation requirements (Doxygen)",
)
parse_g.add_argument(
    "--cvode",
    dest="cvode",
    action="store_true",
    help="Install and configure with cvode",
)
parse_g.add_argument(
    "--cppcheck", dest="cppcheck", action="store_true", help="Install cppcheck"
)
parse_g.add_argument("--gcovr", dest="gcovr", action="store_true", help="Install gcovr")
parse_g.add_argument(
    "--mfront",
    dest="mfront",
    action="store_true",
    help="Install tfel and build OGS with -DOGS_USE_MFRONT=ON",
)
parse_g.add_argument(
    "--insitu",
    dest="insitu",
    action="store_true",
    help="Builds with insitu capabilities",
)
parse_g.add_argument(
    "--dev",
    dest="dev",
    action="store_true",
    help="Installs development tools (vim, gdb)",
)
parse_g.add_argument(
    "--mkl",
    dest="mkl",
    action="store_true",
    help="Use MKL. By setting this option, you agree to the [Intel End User License Agreement](https://software.intel.com/en-us/articles/end-user-license-agreement).",
)
parse_g.add_argument("--version_file", type=str, help="OGS versions.json file")

# Parse local args
local_args = parser.parse_known_args()[0]

branch_is_release = False
git_version = ""
name_start = ""
repo = None
versions = None

if local_args.ogs not in ["off", "clean"]:  # != "off" and local_args.ogs != "clean":
    if os.path.isdir(local_args.ogs):
        repo = "local"
        commit_hash = subprocess.run(
            ["cd {} && git rev-parse HEAD".format(local_args.ogs)],
            capture_output=True,
            text=True,
            shell=True,
        ).stdout.rstrip()
        with open(f"{local_args.ogs}/web/data/versions.json") as fp:
            versions = json.load(fp)
        if "GITLAB_CI" in os.environ:
            if "CI_COMMIT_BRANCH" in os.environ:
                branch = os.environ["CI_COMMIT_BRANCH"]
            elif "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME" in os.environ:
                branch = os.environ["CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"]
            if "OGS_VERSION" in os.environ:
                git_version = os.environ["OGS_VERSION"]
        else:
            branch = subprocess.run(
                [
                    "cd {} && git branch | grep \* | cut -d ' ' -f2".format(
                        local_args.ogs
                    )
                ],
                capture_output=True,
                text=True,
                shell=True,
            ).stdout
            git_version = subprocess.run(
                ["cd {} && git describe --tags".format(local_args.ogs)],
                capture_output=True,
                text=True,
                shell=True,
            ).stdout[0]
    else:
        # Get git commit hash and construct image tag name
        repo, branch, *commit = local_args.ogs.split("@")
        if commit:
            commit_hash = commit[0]
            if branch == "":
                branch = "master"
            versions = json.loads(
                requests.get(
                    f"https://gitlab.opengeosys.org/{repo}/-/raw/{commit_hash}/web/data/versions.json"
                ).text
            )
        else:
            if re.search(r"[\d.]+", branch):
                branch_is_release = True
            repo_split = repo.split("/")
            response = requests.get(
                f"https://gitlab.opengeosys.org/api/v4/projects/{repo.replace('/', '%2F')}/repository/commits?ref_name={branch}"
            )
            response_data = json.loads(response.text)
            commit_hash = response_data[0]["id"]
            # ogs_tag = args.ogs.replace('/', '.').replace('@', '.')
            versions = json.loads(
                requests.get(
                    f"https://gitlab.opengeosys.org/{repo}/-/raw/{branch}/web/data/versions.json"
                ).text
            )

        if branch_is_release:
            name_start = f"ogs-{branch}"
        else:
            name_start = f"ogs-{commit_hash[:8]}"

if local_args.version_file:
    with open(local_args.version_file) as fp:
        versions = json.load(fp)
if versions == None:
    versions = json.loads(
        requests.get(
            f"https://gitlab.opengeosys.org/ogs/ogs/-/raw/master/web/data/versions.json"
        ).text
    )

folder = f"/{name_start}/{local_args.pm}".replace("//", "/")

if len(local_args.cmake_args) > 0:
    cmake_args_hash = hashlib.md5(
        " ".join(local_args.cmake_args).encode("utf-8")
    ).hexdigest()
    cmake_args_hash_short = cmake_args_hash[:8]
    folder += f"/cmake-{cmake_args_hash_short}"

# set image file name
img_file += folder.replace("/", "-")

if local_args.gui:
    img_file += "-gui"
if local_args.ogs != "off" and not args.runtime_only:
    img_file += "-dev"

# Optionally set out_dir
out_dir += folder

if repo == "local":
    scif_file = f"{out_dir}/ogs.scif"  # TODO
else:
    scif_file = f"{out_dir}/ogs.scif"

# Implement recipe
Stage0 += comment(f"--- Begin {filename} ---")

cmake_args = local_args.cmake_args.strip().split(" ")

Stage0 += ogs_base()
if local_args.gui:
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
if local_args.ogs != "clean":
    if local_args.pm == "conan":
        Stage0 += cmake(eula=True, version="3.19.4")
        conan_user_home = "/opt/conan"
        if local_args.dev:
            conan_user_home = ""
        Stage0 += pm_conan(
            user_home=conan_user_home, version=versions["minimum_version"]["conan"]
        )
        Stage0 += environment(variables={"CONAN_SYSREQUIRES_SUDO": 0})
    elif local_args.pm == "system":
        Stage0 += cmake(eula=True, version="3.19.4")
        Stage0 += boost(
            version=versions["minimum_version"]["boost"],
            bootstrap_opts=["--with-toolset=clang"] if toolchain.CC == "clang" else [],
            b2_opts=["headers"],
        )
        Stage0 += environment(variables={"BOOST_ROOT": "/usr/local/boost"})
        Stage0 += packages(apt=["libxml2-dev"], yum=["libxml2-devel"])
        vtk_cmake_args = [
            "-DModule_vtkIOXML=ON",
            "-DModule_vtkIOLegacy=ON",
            "-DVTK_Group_Rendering=OFF",
            "-DVTK_Group_StandAlone=OFF",
        ]
        if local_args.gui:
            Stage0 += packages(
                apt=[
                    "libgeotiff-dev",
                    "libshp-dev",
                    "libnetcdf-c++4-dev",
                ],
                yum=[
                    "libgeotiff-devel",
                    "shapelib-devel",
                    "netcdf-devel",
                ],
            )
            Stage1 += packages(
                apt=[
                    "geotiff-bin",
                    "shapelib",
                    "libnetcdf-c++4",
                    "libglib2.0-0",
                    "libdbus-1-3",
                    "libexpat1",
                    "libfontconfig1",
                    "libfreetype6",
                    "libgl1-mesa-glx",
                    "libglib2.0-0",
                    "libx11-6",
                    "libx11-xcb1",
                    "libxkbcommon-x11-0",
                ],
                # TODO: Add runtime packages for centos
                yum=[
                    "libgeotiff",
                    "shapelib",
                    "netcdf",
                ],
            )
            # TODO: will not work with clang
            qt_install_dir = "/opt/qt"
            qt_version = versions["minimum_version"]["qt"]
            qt_dir = f"{qt_install_dir}/{qt_version}/gcc_64"
            Stage0 += pip(pip="pip3", packages=["aqtinstall"])
            Stage0 += shell(
                commands=[
                    f"aqt install --outputdir {qt_install_dir} {qt_version} linux desktop -m xmlpatterns,x11extras"
                ]
            )
            Stage1 += copy(_from="0", src=qt_install_dir, dest=qt_install_dir)
            Stage0 += environment(
                variables={
                    "LD_LIBRARY_PATH": f"{qt_dir}/lib:$LD_LIBRARY_PATH",
                    "PATH": f"{qt_dir}/bin:$PATH",
                    "QTDIR": qt_dir,
                }
            )
            Stage1 += environment(
                variables={
                    "LD_LIBRARY_PATH": f"{qt_dir}/lib:$LD_LIBRARY_PATH",
                    "PATH": f"{qt_dir}/bin:$PATH",
                    "QTDIR": qt_dir,
                }
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
        if local_args.insitu:
            if local_args.gui:
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
                        "-DModule_vtkIOParallelXML=ON",
                        "-DModule_vtkParallelMPI=ON",
                    ]
                )
            vtk_version = versions["minimum_version"]["vtk"]
            Stage0 += generic_cmake(
                cmake_opts=vtk_cmake_args,
                devel_environment={"VTK_ROOT": "/usr/local/vtk"},
                directory=f"VTK-{vtk_version}",
                ldconfig=True,
                prefix="/usr/local/vtk",
                toolchain=toolchain,
                url=f"https://www.vtk.org/files/release/{vtk_version[:-2]}/VTK-{vtk_version}.tar.gz",
            )
        if toolchain.CC == "mpicc":
            Stage0 += packages(yum=["diffutils"])
            petsc_version = versions["minimum_version"]["petsc"]
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
                directory=f"petsc-{petsc_version}",
                ldconfig=True,
                preconfigure=["sed -i -- 's/python/python3/g' configure"],
                prefix="/usr/local/petsc",
                toolchain=toolchain,
                url=f"http://ftp.mcs.anl.gov/pub/petsc/release-snapshots/petsc-lite-{petsc_version}.tar.gz",
            )

        eigen_version = versions["minimum_version"]["eigen"]
        Stage0 += generic_cmake(
            devel_environment={
                "Eigen3_ROOT": "/usr/local/eigen",
                "Eigen3_DIR": "/usr/local/eigen",
            },
            directory=f"eigen-{eigen_version}",
            prefix="/usr/local/eigen",
            url=f"https://gitlab.com/libeigen/eigen/-/archive/{eigen_version}/eigen-{eigen_version}.tar.gz",
        )
        Stage0 += hdf5(
            configure_opts=["--enable-cxx"],
            toolchain=toolchain,
            version=versions["minimum_version"]["hdf5"],
        )
if local_args.cvode:
    # TODO version
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

if local_args.cppcheck:
    Stage0 += generic_cmake(
        devel_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
        directory="cppcheck-809a769c690d8ab6fef293e41a29c8490512866e",
        prefix="/usr/local/cppcheck",
        runtime_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
        url="https://github.com/danmar/cppcheck/archive/809a769c690d8ab6fef293e41a29c8490512866e.tar.gz",
    )

if local_args.docs:
    Stage0 += packages(ospackages=["doxygen", "graphviz", "texlive-base"])
if local_args.gcovr:
    Stage0 += pip(pip="pip3", packages=["gcovr"])

if local_args.dev:
    Stage0 += packages(
        ospackages=["neovim", "gdb", "silversearcher-ag", "ssh-client", "less"]
    )

if local_args.mfront:
    Stage0 += generic_cmake(
        directory="tfel-TFEL-3.3.0",
        ldconfig=True,
        url="https://github.com/thelfer/tfel/archive/TFEL-3.3.0.tar.gz",
        prefix="/usr/local/tfel",
    )
    Stage0 += environment(variables={"TFELHOME": "/usr/local/tfel"})
    cmake_args.append("-DOGS_USE_MFRONT=ON")

if local_args.mkl:
    Stage0 += mkl(eula=True)
    cmake_args.append("-DOGS_USE_MKL=ON")

if local_args.ccache:
    Stage0 += ccache(cache_size="15G")
if local_args.ogs != "off" and local_args.ogs != "clean":
    mount_args = ""
    if local_args.ccache:
        mount_args += f" --mount=type=cache,target=/opt/ccache,id=ccache"
    if local_args.cvode:
        cmake_args.append("-DOGS_USE_CVODE=ON")
    if local_args.gui:
        cmake_args.append("-DOGS_BUILD_GUI=ON")
    if local_args.insitu:
        cmake_args.append("-DOGS_INSITU=ON")

    Stage0 += raw(docker=f"ARG OGS_COMMIT_HASH={commit_hash}")

    if repo == "local":
        print(f"chdir to {local_args.ogs}")
        os.chdir(local_args.ogs)
        mount_args += f" --mount=type=bind,target=/scif/apps/ogs/src,rw"

    ogs_app = scif(_arguments=mount_args, name="ogs", file=scif_file)
    ogs_app += ogs(
        repo=repo,
        branch=branch,
        commit=commit_hash,
        conan=(True if local_args.pm == "conan" else False),
        git_version=git_version,
        toolchain=toolchain,
        prefix="/scif/apps/ogs",
        cmake_args=cmake_args,
        parallel=local_args.parallel,
        remove_build=True,
        remove_source=True,
    )
    # Install scif in all stages
    Stage0 += pip(packages=["scif"], pip="pip3")
    Stage1 += pip(packages=["scif"], pip="pip3")
    Stage0 += ogs_app
