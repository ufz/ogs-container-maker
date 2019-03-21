# OGS Container Maker

## General usage

### Installation

```bash
virtualenv ~/.venv/ogs-container-maker
source ~/.venv/ogs-container-maker/bin/activate
pip install --upgrade requests hpccm
```

### Generate container definition

```bash
hpccm --recipe recipes/ogs-builder.py > Dockerfile
hpccm --recipe recipes/ogs-builder.py --format singularity > Singularity

# With user options, Use : instead of = in cmake_args!
hpccm --recipe recipes/ogs-builder.py --format singularity \
    --userarg ompi=2.1.3 cmake_args="-DOGS_BUILD_PROCESSES:GroundwaterFlow"
```

### Build image

```
docker build -t ogs-ompi-2.1.3 -f Dockerfile .
sudo singularity build ogs-ompi-2.1.3.sif Singularity
```

Convert Docker image to Singularity image:

```
mkdir _out
docker run -v /var/run/docker.sock:/var/run/docker.sock \
    -v $PWD/_out:/output --privileged -t --rm \
    singularityware/docker2singularity ogs-ompi-2.1.3
```

### Run

```bash
docker run --it --rm ogs-ompi-2.1.3
# in container:
ogs --version
```

```
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

```bash
$ python build --help
usage: build.py [-h] [--recipe RECIPE] [--out OUT] [--print]
                [--format {docker,singularity} {docker,singularity}]
                [--pm [{system,conan} [{system,conan} ...]]]
                [--ompi [OMPI [OMPI ...]]] [--ogs [OGS [OGS ...]]]
                [--cmake_args [CMAKE_ARGS [CMAKE_ARGS ...]]] [--build]
                [--upload] [--convert] [--runtime-only]

Generate container image definitions.

optional arguments:
  -h, --help            show this help message and exit
  --recipe RECIPE       HPCCM recipe (default: recipes/ogs-builder.py)
  --out OUT             Output directory (default: _out)
  --print, -P           Print the definition to stdout (default: False)

Combinatorial options:
  All combinations of the given options will be generated

  --format {docker,singularity} {docker,singularity}
  --pm [{system,conan} [{system,conan} ...]]
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
                        -DFOO=BAR' ' -DSECOND=TRUE' (default: )

Image build options:
  --build, -B           Build the images from the definition files (default:
                        False)
  --upload, -U          Upload Docker image to registry (default: False)
  --convert, -C         Convert Docker image to Singularity image (default:
                        False)
  --runtime-only, -R    Generate multi-stage Dockerfiles for small runtime
                        images (default: False)
```
