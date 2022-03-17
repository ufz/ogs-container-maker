# OGS Container Maker

[![PyPI version](https://badge.fury.io/py/ogscm.svg)](https://badge.fury.io/py/ogscm)

## General usage

### Installation

```bash
virtualenv ~/.venv/ogs-container-maker
source ~/.venv/ogs-container-maker/bin/activate
pip install ogscm
```

### Generate container definition

OGS Container Maker has builtin *recipes*. You need to specify the recipes to use as command arguments. Each of recipes adds options to the tool. Typically you want to start with a compiler. Add the `compiler.py` recipe and the `--help`-flag to get more options:

```bash
$ ogscm compiler.py --help
...
compiler.py:
  --compiler COMPILER   The compiler to use. Possible options: off, gcc,
                        clang (default: gcc)
  --compiler_version COMPILER_VERSION
                        Compiler version. (default: )
  --iwyy                Install include-what-you-use (requires clang
                        compiler) (default: False)
```

After specifying the compiler recipe (and optionally setting a non-default compiler and version) you may want to add the `ogs.py` recipe:

```bash
$ ogscm compiler.py ogs.py --help
...
ogs.py:
  --pm {system,off}
                        Package manager to install third-party dependencies
                        (default: conan)
  --ogs OGS             OGS repo on gitlab.opengeosys.org in the form
                        'user/repo@branch' OR 'user/repo@@commit' to
                        checkout a specific commit OR a path to a local
                        subdirectory to the git cloned OGS sources OR 'off'
                        to disable OGS building OR 'clean' to disable OGS
                        and all its dev dependencies (default:
                        ogs/ogs@master)
  --cmake_args CMAKE_ARGS
                        CMake argument set has to be quoted and **must**
                        start with a space. e.g. --cmake_args '
                        -DFIRST=TRUE -DFOO=BAR' (default: )
...
```

Please note that the order of the recipes given on the command line is important. The typical order for the current builtin recipes is `compiler.py mpi.py ogs.py ogs_jupyter.py`.

To generate a Dockerfile with the default parameters:

```bash
$ ogscm compiler.py ogs.py
Evaluating compiler.py
Evaluating ogs.py
Created definition _out/docker/gcc/default/ogs-d18c786e/conan/Dockerfile
```

With some options (and the `mpi.py`-recipe):

```bash
$ ogscm compiler.py mpi.py ogs.py --ompi 4.0.5 --cmake_args ' -DOGS_BUILD_PROCESSES=LiquidFlow'
Evaluating compiler.py
Evaluating mpi.py
Evaluating ogs.py
Created definition _out/docker/gcc/10/openmpi/4.0.5/ogs-d18c786e/conan/cmake-702517b3/Dockerfile
```

### Build image

Add the `--build`-flag.

Convert Docker image to Singularity image:

Add the `--convert`-flag (requires Singularity 3.x).

### Run

```bash
docker run --it --rm ogs-ompi-2.1.3
# in container:
ogs --version
```

```bash
singularity shell ogs-ompi-2.1.3.sif
# in container:
ogs --version
# OR directly run from host
singularity exec ogs-ompi-2.1.3.sif ogs local/path/to/square_1e0.prj
```

## All options

All options for current builtin recipes:

```
$ ogscm compiler.py mpi.py ogs.py --help
Evaluating compiler.py
Evaluating mpi.py
Evaluating ogs.py
usage: ogscm [-h] [--version] [--out OUT] [--file FILE] [--print] [--format {docker,singularity}] [--base_image BASE_IMAGE] [--runtime_base_image RUNTIME_BASE_IMAGE]
             [--cpu-target {a64fx,aarch64,arm,broadwell,bulldozer,cannonlake,cascadelake,core2,excavator,haswell,i686,icelake,ivybridge,k10,mic_knl,nehalem,nocona,pentium2,pentium3,pentium4,piledriver,power7,power8,power8le,power9,power9le,ppc,ppc64,ppc64le,ppcle,prescott,sandybridge,skylake,skylake_avx512,sparc,sparc64,steamroller,thunderx2,westmere,x86,x86_64,zen,zen2}]
             [--build] [--build_args BUILD_ARGS] [--upload] [--registry REGISTRY] [--tag TAG] [--convert] [--sif_file SIF_FILE] [--convert-enroot] [--enroot-bundle] [--enroot_file ENROOT_FILE] [--force]
             [--runtime-only] [--clean] [--deploy [DEPLOY]] [--pip [package ...]] [--packages [packages ...]] [--compiler COMPILER] [--compiler_version COMPILER_VERSION] [--fortran] [--iwyy] [--ompi OMPI]
             [--mpi_benchmarks] [--mpi_no_entrypoint] [--pm {system,off}] [--ogs OGS] [--cmake_args CMAKE_ARGS] [--cmake_preset CMAKE_PRESET] [--cmake_preset_file CMAKE_PRESET_FILE] [--ccache]
             [--cpmcache] [--parallel PARALLEL] [--gui] [--docs] [--cvode] [--cppcheck] [--gcovr] [--mfront] [--insitu] [--dev] [--mkl] [--petsc_configure_args PETSC_CONFIGURE_ARGS]
             [--version_file VERSION_FILE]
             recipe [recipe ...]

positional arguments:
  recipe

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --out OUT             Output directory (default: _out)
  --file FILE           Overwrite output recipe file name (default: )
  --print, -P           Print the definition to stdout (default: False)

General image config:
  --format {docker,singularity}
  --base_image BASE_IMAGE
                        The base image. (default: ubuntu:20.04)
  --runtime_base_image RUNTIME_BASE_IMAGE
                        The runtime base image. (default: )
  --cpu-target {a64fx,aarch64,arm,broadwell,bulldozer,cannonlake,cascadelake,core2,excavator,haswell,i686,icelake,ivybridge,k10,mic_knl,nehalem,nocona,pentium2,pentium3,pentium4,piledriver,power7,power8,power8le,power9,power9le,ppc,ppc64,ppc64le,ppcle,prescott,sandybridge,skylake,skylake_avx512,sparc,sparc64,steamroller,thunderx2,westmere,x86,x86_64,zen,zen2}
                        The CPU microarchitecture to optimize for (archspec). (default: ivybridge)

Image build options:
  --build, -B           Build the images from the definition files (default: False)
  --build_args BUILD_ARGS
                        Arguments to the build command. Have to be quoted and **must** start with a space. E.g. --build_args ' --no-cache' (default: )
  --upload, -U          Upload Docker image to registry (default: False)
  --registry REGISTRY   The docker registry the image is tagged and uploaded to. (default: registry.opengeosys.org/ogs/ogs)
  --tag TAG             The full docker image tag. Overwrites --registry. (default: )
  --convert, -C         Convert Docker image to Singularity image (default: False)
  --sif_file SIF_FILE   Overwrite output singularity image file name (default: )
  --convert-enroot, -E  Convert Docker image to enroot image (default: False)
  --enroot-bundle       Convert enroot image to enroot bundle (default: False)
  --enroot_file ENROOT_FILE
                        Overwrite output enroot image file name (default: )
  --force               Forces overwriting of image files! (default: False)
  --runtime-only, -R    Generate multi-stage Dockerfiles for small runtime images (default: False)

Maintenance:
  --clean               Cleans up generated files in default directories. (default: False)

Image deployment:
  --deploy [DEPLOY], -D [DEPLOY]
                        Deploys to all configured hosts (in config/deploy_hosts.yml) with no additional arguments or to the specified host. Implies --build and --convert arguments. (default: )

Packages to install:
  --pip [package ...]   Install additional Python packages (default: [])
  --packages [packages ...]
                        Install additional OS packages (default: [])

compiler.py:
  --compiler COMPILER   The compiler to use. Possible options: off, gcc, clang (default: gcc)
  --compiler_version COMPILER_VERSION
                        Compiler version. (default: )
  --fortran             Install fortran compiler. (default: False)
  --iwyy                Install include-what-you-use (requires clang compiler) (default: False)

mpi.py:
  --ompi OMPI           OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2 (default: 4.0.6)
  --mpi_benchmarks      Installs OSU MPI benchmarks and mpi_bw, mpi_ring, mpi_hello (default: False)
  --mpi_no_entrypoint   Disables mpi entrypoint. (Use with ogs_jupyter.py recipe) (default: False)

ogs.py:
  --pm {system,off}     Package manager to install third-party dependencies (default: system)
  --ogs OGS             OGS repo on gitlab.opengeosys.org in the form 'user/repo@branch' OR 'user/repo@@commit' to checkout a specific commit OR a path to a local subdirectory to the git cloned OGS
                        sources OR 'off' to disable OGS building OR 'clean' to disable OGS and all its dev dependencies (default: ogs/ogs@master)
  --cmake_args CMAKE_ARGS
                        CMake argument set has to be quoted and **must** start with a space. e.g. --cmake_args ' -DFIRST=TRUE -DFOO=BAR' (default: )
  --cmake_preset CMAKE_PRESET
                        A CMake configuration preset to use. (default: release)
  --cmake_preset_file CMAKE_PRESET_FILE
                        A CMake (user) presets file as a local file path. (default: None)
  --ccache              Enables ccache build caching. (Docker-only) (default: False)
  --cpmcache            Enables CPM source caching. (Docker-only) (default: False)
  --parallel PARALLEL, -j PARALLEL
                        The number of cores to use for compilation. (default: 8)
  --gui                 Builds the GUI (Data Explorer) (default: False)
  --docs                Setup documentation requirements (Doxygen) (default: False)
  --cvode               Install and configure with cvode (default: False)
  --cppcheck            Install cppcheck (default: False)
  --gcovr               Install gcovr (default: False)
  --mfront              Install tfel and build OGS with -DOGS_USE_MFRONT=ON (default: False)
  --insitu              Builds with insitu capabilities (default: False)
  --dev                 Installs development tools (vim, gdb) (default: False)
  --mkl                 Use MKL. By setting this option, you agree to the [Intel End User License Agreement](https://software.intel.com/en-us/articles/end-user-license-agreement). (default: False)
  --petsc_configure_args PETSC_CONFIGURE_ARGS
                        PETSc configuration arguments; has to be quoted. (default: --with-fc=0 --download-f2cblaslapack=1)
  --version_file VERSION_FILE
                        OGS versions.json file (default: None)
```

## Advanced usage

### Build OGS from local git repo

You can use the ogs-container-maker to build a container image from your current source code on your host machine:

```
virtualenv .venv
source .venv/bin/activate
pip install ogscm
ogscm compiler.py ogs.py -B -C -R --ogs [path to ogs sources]
```

### Deploy image files

- Requires `rsync`
- Rename the file `config/deploy_hosts_example.yml` to `config/deploy_hosts.yml`
- `host` has to be a SSH host to which you have passwordless access
- Deploy to the host with `... -D myhost`


## PyPi Publication

- Bump version in `pyproject.py` and `version.py`
- Create tag
- Push to GitLab (`git push --tags`)
