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
)

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
    choices=["system", "off"],
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
    "--cmake_preset",
    type=str,
    default="release",
    help="A CMake configuration preset to use.",
)
parse_g.add_argument(
    "--cmake_preset_file",
    type=str,
    default=None,
    help="A CMake (user) presets file as a local file path.",
)
parse_g.add_argument(
    "--ccache",
    dest="ccache",
    action="store_true",
    help="Enables ccache build caching. (Docker-only)",
)
parse_g.add_argument(
    "--cpmcache",
    dest="cpmcache",
    action="store_true",
    help="Enables CPM source caching. (Docker-only)",
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
if toolchain.CC == "mpicc":
    parse_g.add_argument(
        "--petsc_configure_args",
        type=str,
        default="--with-fc=0 --download-f2cblaslapack=1",
        help="PETSc configuration arguments; has to be quoted.",
    )
parse_g.add_argument("--version_file", type=str, help="OGS versions.json file")
parse_g.add_argument(
    "--boost-sourceforge",
    dest="boost_sourceforge",
    action="store_true",
    help="Boolean flag to specify whether Boost should be downloaded from SourceForge rather than the current Boost repository.",
)
parse_g.add_argument(
    "--keep-ogs-source",
    dest="keep_source",
    action="store_true",
    help="Boolean flag to specify whether the OGS source directory should be preserved.",
)
parse_g.add_argument(
    "--keep-ogs-build",
    dest="keep_build",
    action="store_true",
    help="Boolean flag to specify whether the OGS build directory should be preserved.",
)
parse_g.add_argument(
    "--run-ctest",
    dest="run_ctest",
    action="store_true",
    help="Boolean flag to specify whether to run the OGS ctest-target.",
)

# Parse local args
local_args = parser.parse_known_args()[0]

branch_is_release = False
git_version = ""
name_start = ""
repo = None
versions = None
versions_master = json.loads(
    requests.get(
        f"https://gitlab.opengeosys.org/ogs/ogs/-/raw/master/web/data/versions.json?inline=false"
    ).text
)

if local_args.ogs not in ["off", "clean"]:  # != "off" and local_args.ogs != "clean":
    if os.path.isdir(local_args.ogs):
        if local_args.run_ctest and args.format == "docker":
            print("`--run_ctest` can not be used with `--ogs local/path`")
            exit(1)
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
            if "CI_COMMIT_TAG" in os.environ:
                branch = "master"
            elif "CI_COMMIT_BRANCH" in os.environ:
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
            ).stdout.strip()
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

if local_args.cmake_preset_file:
    # Make path absolute
    local_args.cmake_preset_file = os.path.abspath(
        os.path.expanduser(os.path.expandvars(local_args.cmake_preset_file))
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
    cmake_version = versions_master["tested_version"]["cmake"]
    if "cmake" in versions["tested_version"]:
        cmake_version = versions["tested_version"]["cmake"]
    Stage0 += cmake(eula=True, version=cmake_version)
    if local_args.pm == "system":
        boost_bootsrap_opts = []
        if local_args.mfront:
            # for mfront python bindings
            boost_bootsrap_opts = ["--with-python=python3"]
        if toolchain.CC == "clang":
            boost_bootsrap_opts.append("--with-toolset=clang")
        Stage0 += boost(
            b2_opts=["headers"],
            bootstrap_opts=boost_bootsrap_opts,
            ldconfig=True,
            sourceforge=local_args.boost_sourceforge,
            version=versions["minimum_version"]["boost"],
        )
        Stage0 += environment(variables={"BOOST_ROOT": "/usr/local/boost"})
        Stage0 += packages(
            apt=["libxml2-dev", "xsltproc"], yum=["libxml2-devel", "libxslt"]
        )
        vtk_cmake_args = []
        if "libraries" in versions:
            for option in versions["libraries"]["vtk"]["options"]:
                if eval(option["condition"]["ogscm"]):
                    for cmake_option in option["cmake"]:
                        vtk_cmake_args.append(f"-D{cmake_option}")
            # Reverse so the VTK_GROUP_ vars are at the end of the list, otherwise they have no effect.
            vtk_cmake_args = vtk_cmake_args[::-1]
        else:
            vtk_cmake_args = [
                "-DModule_vtkIOXML=ON",
                "-DModule_vtkIOLegacy=ON",
                "-DVTK_Group_Rendering=OFF",
                "-DVTK_Group_StandAlone=OFF",
            ]
            if local_args.gui:
                vtk_cmake_args = [
                    "-DVTK_BUILD_QT_DESIGNER_PLUGIN=OFF",
                    "-DVTK_Group_Qt=ON",
                    "-DVTK_QT_VERSION=5",
                ]
            if toolchain.CC == "mpicc":
                vtk_cmake_args.extend(
                    [
                        "-DModule_vtkIOParallelXML=ON",
                        "-DModule_vtkParallelMPI=ON",
                    ]
                )

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
                # TODO: Add runtime packages for yum
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
            Stage0 += pip(pip="pip3", packages=["aqtinstall==1.2.5"])
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
            petsc_args = local_args.petsc_configure_args.strip().split(" ")
            petsc_configure_opts = [
                f"CC={toolchain.CC}",
                f"CXX={toolchain.CXX}",
                f"FC={toolchain.FC}",
                f"F77={toolchain.F77}",
                f"F90={toolchain.F90}",
                "--CFLAGS='-O3'",
                "--CXXFLAGS='-O3'",
                "--FFLAGS='-O3'",
                "--with-debugging=no",
            ]
            petsc_configure_opts.extend(petsc_args)
            Stage0 += generic_autotools(
                configure_opts=petsc_configure_opts,
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
            toolchain=toolchain,
            url=f"https://gitlab.com/libeigen/eigen/-/archive/{eigen_version}/eigen-{eigen_version}.tar.gz",
        )
        hdf5_cofigure_opts = ["--enable-cxx"]
        if toolchain.CC == "mpicc":
            hdf5_cofigure_opts = ["--enable-parallel", "--enable-shared"]
        hdf5_version = versions_master["minimum_version"]["hdf5"]
        if "hdf5" in versions["minimum_version"]:
            hdf5_version = versions["minimum_version"]["hdf5"]
        Stage0 += hdf5(
            configure_opts=hdf5_cofigure_opts,
            ldconfig=True,
            toolchain=toolchain,
            version=hdf5_version,
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
        toolchain=toolchain,
        url="https://github.com/ufz/cvode/archive/2.8.2.tar.gz",
    )

if local_args.cppcheck:
    Stage0 += generic_cmake(
        devel_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
        directory="cppcheck-809a769c690d8ab6fef293e41a29c8490512866e",
        prefix="/usr/local/cppcheck",
        runtime_environment={"PATH": "/usr/local/cppcheck/bin:$PATH"},
        toolchain=toolchain,
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

if local_args.mfront and local_args.pm == "system":
    tfel_version = versions_master["minimum_version"]["tfel-rliv"]
    if "tfel-rliv" in versions["minimum_version"]:
        tfel_version = versions["minimum_version"]["tfel-rliv"]
    Stage0 += generic_cmake(
        cmake_opts=["-Denable-python-bindings=ON"],
        directory=f"tfel-rliv-{tfel_version}",
        ldconfig=True,
        url=f"https://github.com/thelfer/tfel/archive/refs/heads/rliv-{tfel_version}.zip",
        prefix="/usr/local/tfel",
        runtime_environment={"PATH": "/usr/local/tfel/bin:$PATH"},
        devel_environment={"PATH": "/usr/local/tfel/bin:$PATH"},
        toolchain=toolchain,
    )
    tfel_env = environment(
        variables={
            "TFELHOME": "/usr/local/tfel",
            # TODO: Don't hard-code python version
            "PYTHONPATH": "/usr/local/tfel/lib/python3.8/site-packages:$PYTHONPATH",
        }
    )
    Stage0 += tfel_env
    Stage1 += tfel_env
    cmake_args.append("-DOGS_USE_MFRONT=ON")

if local_args.mkl:
    Stage0 += mkl(eula=True, mklvars=False)
    # For 32-bit mkl_link_tool:
    Stage0 += packages(apt=["lib32stdc++6"], yum=["libstdc++.i686"])
    cmake_args.append("-DOGS_USE_MKL=ON")

if local_args.ccache:
    Stage0 += ccache(cache_size="15G")
if local_args.ogs != "off" and local_args.ogs != "clean":
    mount_args = ""
    if local_args.ccache:
        mount_args += f" --mount=type=cache,target=/opt/ccache"
    if local_args.cpmcache:
        mount_args += f" --mount=type=cache,target=/opt/cpmcache,sharing=locked"
        cmake_args.append("-DCPM_SOURCE_CACHE=/opt/cpmcache")
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

    Stage0 += ogs(
        repo=repo,
        branch=branch,
        commit=commit_hash,
        git_version=git_version,
        toolchain=toolchain,
        cmake_args=cmake_args,
        cmake_preset=local_args.cmake_preset,
        cmake_preset_file=local_args.cmake_preset_file,
        parallel=local_args.parallel,
        remove_build=not local_args.keep_build,
        remove_source=not local_args.keep_source,
        mount_args=mount_args,
        run_ctest=local_args.run_ctest,
    )

# Required for vtk from Python (for notebooks, VTUInterface)
# https://github.com/Kaggle/docker-python/pull/358
Stage0 += packages(apt=["libgl1"], yum=["mesa-libGL"])
Stage1 += packages(apt=["libgl1"], yum=["mesa-libGL"])
