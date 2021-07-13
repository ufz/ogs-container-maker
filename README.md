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

OGS Container Maker has builtin recipes. You need to specify the recipes to use as command arguments. Each of recipes adds options to the tool. Typically you want to start with a compiler. Add the `compiler.py` recipe and the `--help`-flag to get more options:

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
  --pm {system,conan,off}
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

To generate a Dockerfile with the default parameters:

```bash
$ ogscm compiler.py ogs.py
Evaluating compiler.py
Evaluating ogs.py
Created definition _out/docker/gcc/default/ogs-d18c786e/conan/Dockerfile
```

With some options (and the `mpi.py`-recipe):

```bash
$ ogscm compiler.py mpi.py ogs.py --base_image 'centos:8' --ompi 4.0.5 --cmake_args ' -DOGS_BUILD_PROCESSES=LiquidFlow'
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
$ ogscm compiler.py mpi.py ogs.py --base_image 'centos:8' --help
Evaluating compiler.py
Evaluating mpi.py
Evaluating ogs.py
usage: ogscm [-h] [--version] [--out OUT] [--file FILE] [--print] [--format {docker,singularity}] [--base_image BASE_IMAGE] [--build] [--build_args BUILD_ARGS] [--upload] [--registry REGISTRY] [--tag TAG]
             [--convert] [--sif_file SIF_FILE] [--convert-enroot] [--enroot_file ENROOT_FILE] [--runtime-only] [--clean] [--deploy [DEPLOY]] [--pip [package ...]] [--packages [packages ...]] [--compiler COMPILER]
             [--compiler_version COMPILER_VERSION] [--iwyy] [--ompi OMPI] [--mpi_benchmarks] [--pm {system,conan,off}] [--ogs OGS] [--cmake_args CMAKE_ARGS] [--ccache] [--parallel PARALLEL] [--gui] [--docs]
             [--cvode] [--cppcheck] [--gcovr] [--mfront] [--insitu] [--dev] [--mkl] [--version_file VERSION_FILE]
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
                        The base image. (centos:8 is supported too) (default: ubuntu:20.04)

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
  --enroot_file ENROOT_FILE
                        Overwrite output enroot image file name (default: )
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
  --iwyy                Install include-what-you-use (requires clang compiler) (default: False)

mpi.py:
  --ompi OMPI           OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2 (default: 4.0.5)
  --mpi_benchmarks      Installs OSU MPI benchmarks and mpi_bw, mpi_ring, mpi_hello (default: False)

ogs.py:
  --pm {system,conan,off}
                        Package manager to install third-party dependencies (default: system)
  --ogs OGS             OGS repo on gitlab.opengeosys.org in the form 'user/repo@branch' OR 'user/repo@@commit' to checkout a specific commit OR a path to a local subdirectory to the git cloned OGS sources OR
                        'off' to disable OGS building OR 'clean' to disable OGS and all its dev dependencies (default: ogs/ogs@master)
  --cmake_args CMAKE_ARGS
                        CMake argument set has to be quoted and **must** start with a space. e.g. --cmake_args ' -DFIRST=TRUE -DFOO=BAR' (default: )
  --ccache              Enables ccache build caching. (default: False)
  --parallel PARALLEL, -j PARALLEL
                        The number of cores to use for compilation. (default: 32)
  --gui                 Builds the GUI (Data Explorer) (default: False)
  --docs                Setup documentation requirements (Doxygen) (default: False)
  --cvode               Install and configure with cvode (default: False)
  --cppcheck            Install cppcheck (default: False)
  --gcovr               Install gcovr (default: False)
  --mfront              Install tfel and build OGS with -DOGS_USE_MFRONT=ON (default: False)
  --insitu              Builds with insitu capabilities (default: False)
  --dev                 Installs development tools (vim, gdb) (default: False)
  --mkl                 Use MKL. By setting this option, you agree to the [Intel End User License Agreement](https://software.intel.com/en-us/articles/end-user-license-agreement). (default: False)
  --version_file VERSION_FILE
                        OGS versions.json file (default: None)
```

## Advanced usage

### Build OGS from local git repo

You can use the ogs-container-maker to build multiple container images from your current source code at once. The following commands will build (`-B`-parameter) 4 docker container (using one serial and 3 MPI-enabled configurations), convert them to Singularity image files (`-C`) and strip everything out but the runtime-requirements (`-R`). You can find the images in `_out/images`.

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

## Developer setup

```bash
poetry install
poetry shell

# Register Jupyter kernel:
python -m ipykernel install --user --name=container-maker
```
## Jupyter interface

### Requirements:

- Docker
- Singularity

### Setup

Create a kernel with `ogscm` installed and in the `PATH`:

```bash
virtualenv ogscm-venv
cd ogscm-venv
source bin/activate
pip install ogscm
python -m ipykernel install --user --name=ogscm --env PATH $PWD/bin:$PATH`
```

### Usage

In a notebook run this cell:

```py
from ogscm.jupyter import setup_ui

def run_cmd(cmd):
    print(f"Executing: {cmd}")
    !poetry run {cmd}

user_recipes = ["user_recipes/my_recipe.py"] # optional user recipes
out = setup_ui(run_cmd, user_recipes)
```

Options `--build` and `--convert` are enabeld per default, then click on button `CREATE CONTAINER`. Optionally run a second cell to get a download link to the image file:

```py
from ogscm.jupyter import display_download_link, display_source
display_source(display_download_link(out.outputs[0]['text']), "docker")
```

Output is stored in `[notebook-location]/_out`. UI state is preserved when notebook was saved. Enable recipes from the tab widget by clicking on the `Disabled`-button (`compiley.py`-recipe is enabled by default).
