# OGS Container Maker

## General usage

### Installation

```bash
virtualenv ~/.venv/ogs-container-maker
source ~/.venv/ogs-container-maker/bin/activate
pip install ogscm
```

### Generate container definition

```bash
$ ogscm
Creating 1 image definition(s)...
Created definition _out/docker/ubuntu_17.10/ogs-4c7de6a4/serial/conan/cmake-d41d8cd9/Dockerfile

# With user options
$ ogscm --format singularity --ompi 2.1.3 --cmake_args ' -DOGS_BUILD_PROCESSES=GroundwaterFlow'
Creating 1 image definition(s)...
Created definition _out/singularity/ubuntu_17.10/ogs-4c7de6a4/openmpi-2.1.3/conan/cmake-fde09bf7/Singularity.de
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

## Using the combinatorial builder

Creates Docker definition files with different OpenMPI implementations and OpenGeoSys parallel configuration (from the current master), builds the docker images and converts them to Singularity images:

```bash
python build.py --ogs ufz/ogs@master --ompi 2.1.2 3.1.2 --build --convert
```

Check help for more options:

```
$ ogscm --help
usage: ogscm [-h] [--version] [--out OUT] [--file FILE] [--print]
              [--format [{docker,singularity} [{docker,singularity} ...]]]
              [--pm [{system,conan,spack,off} [{system,conan,spack,off} ...]]]
              [--ompi [OMPI [OMPI ...]]] [--ogs [OGS [OGS ...]]]
              [--cmake_args [CMAKE_ARGS [CMAKE_ARGS ...]]] [--build]
              [--upload] [--registry REGISTRY] [--convert] [--runtime-only]
              [--base_image BASE_IMAGE] [--compiler COMPILER]
              [--compiler_version COMPILER_VERSION] [--gui] [--docs]
              [--jenkins] [--cvode] [--cppcheck] [--iwyy] [--gcovr]
              [--mpi_benchmarks] [--dev] [--clean]

Generate container image definitions.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  --out OUT             Output directory (default: _out)
  --file FILE           Overwrite output recipe file name (default: )
  --print, -P           Print the definition to stdout (default: False)

Combinatorial options:
  All combinations of the given options will be generated

  --format [{docker,singularity} [{docker,singularity} ...]]
  --pm [{system,conan,spack,off} [{system,conan,spack,off} ...]]
                        Package manager to install third-party dependencies
                        (default: ['conan'])
  --ompi [OMPI [OMPI ...]]
                        OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2
                        (default: ['off'])
  --ogs [OGS [OGS ...]]
                        OGS GitHub repo in the form 'user/repo@branch' or
                        'off' to disable OGS building (default:
                        ['ufz/ogs@master'])
  --cmake_args [CMAKE_ARGS [CMAKE_ARGS ...]]
                        CMake argument sets have to be quoted and **must**
                        start with a space. e.g. --cmake_args ' -DFIRST=TRUE
                        -DFOO=BAR' ' -DSECOND=TRUE' (default: [''])

Image build options:
  --build, -B           Build the images from the definition files (default:
                        False)
  --upload, -U          Upload Docker image to registry (default: False)
  --registry REGISTRY   The docker registry the image is tagged and uploaded
                        to. (default: registry.opengeosys.org/ogs/ogs)
  --convert, -C         Convert Docker image to Singularity image (default:
                        False)
  --runtime-only, -R    Generate multi-stage Dockerfiles for small runtime
                        images (default: False)

Additional options:
  --base_image BASE_IMAGE
                        The base image. 'centos:7' is supported too. (default:
                        ubuntu:18.04)
  --compiler COMPILER   The compiler to use. Possible options: off, gcc, clang
                        (default: gcc)
  --compiler_version COMPILER_VERSION
                        Compiler version. (default: )
  --gui                 Builds the GUI (Data Explorer) (default: False)
  --docs                Setup documentation requirements (Doxygen) (default:
                        False)
  --jenkins             Setup Jenkins slave (default: False)
  --cvode               Install and configure with cvode (default: False)
  --cppcheck            Install cppcheck (default: False)
  --iwyy                Install include-what-you-use (default: False)
  --gcovr               Install gcovr (default: False)
  --mpi_benchmarks      Installs OSU MPI benchmarks as scif app and mpi_bw,
                        mpi_ring,mpi_hello (default: False)
  --dev                 Installs development tools (vim, gdb) (default: False)

Maintenance:
  --clean               Cleans up generated files in default directories.
                        (default: False)
```
