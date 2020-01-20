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
              [--ccache] [--parallel PARALLEL] [--base_image BASE_IMAGE]
              [--compiler COMPILER] [--compiler_version COMPILER_VERSION]
              [--gui] [--docs] [--jenkins] [--cvode] [--cppcheck] [--iwyy]
              [--gcovr] [--mpi_benchmarks] [--dev] [--insitu]
              [--pip [package [package ...]]] [--clean] [--deploy [DEPLOY]]

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
                        OGS GitHub repo in the form 'user/repo@branch' OR
                        'user/repo@@commit' to checkout a specific commit OR a
                        path to a local subdirectory to the git cloned OGS
                        sourcesOR 'off' to disable OGS building (default:
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
  --ccache              Enables ccache build caching. (default: False)
  --parallel PARALLEL, -j PARALLEL
                        The number of cores to use for compilation. (default:
                        10)

Additional options:
  --base_image BASE_IMAGE
                        The base image. (default: ubuntu:18.04)
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
  --insitu              Builds with insitu capabilities (default: False)
  --pip [package [package ...]]
                        Install additional Python packages (default: [''])

Maintenance:
  --clean               Cleans up generated files in default directories.
                        (default: False)

Image deployment:
  --deploy [DEPLOY], -D [DEPLOY]
                        Deploys to all configured hosts (in
                        config/deploy_hosts.yml) with no additional arguments
                        or to the specified host. Implies --build and
                        --convert arguments. (default: )
```

## Advanced usage

### Build OGS from local git repo

You can use the ogs-container-maker to build multiple container images from your current source code at once. The following commands will build (`-B`-parameter) 4 docker container (using one serial and 3 MPI-enabled configurations), convert them to Singularity image files (`-C`) and strip everything out but the runtime-requirements (`-R`). You can find the images in `_out/images`.

```
cd ogs
git submodule update --init ThirdParty/container-maker
virtualenv .venv
source .venv/bin/activate
pip install -r ThirdParty/container-maker/requirements.txt
export PYTHONPATH="${PYTHONPATH}:${PWD}/ThirdParty/container-maker"
python ThirdParty/container-maker/ogscm/cli.py -B -C -R --ogs . --pm system --cvode --ompi off 2.1.6 3.1.4 4.0.1
```

### Deploy image files

- Requires `rsync`
- Rename the file `config/deploy_hosts_example.yml` to `config/deploy_hosts.yml`
- `host` has to be a SSH host to which you have passwordless access
- Deploy to the host with `... -D myhost`
