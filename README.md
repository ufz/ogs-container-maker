# OGS Container Maker

## Usage

### Installation

```bash
virtualenv ~/.venv/ogs-container-maker
source ~/.venv/ogs-container-maker/bin/activate
pip install --upgrade requests hpccm
```

### Generate container definition

```bash
hpccm --recipe ogs-builder.py > Dockerfile
hpccm --recipe ogs-builder.py --format singularity > Singularity

# With user options, Use : instead of = in cmake_args!
hpccm --recipe ogs-builder.py --format singularity \
    --userarg ompi=2.1.3 cmake_args="-DOGS_BUILD_PROCESSES:GroundwaterFlow"
```

### Build image

```
docker build -t ogs-ompi-2.1.3 -f Dockerfile .
sudo singularity build ogs-ompi-2.1.3.simg Singularity
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
singularity shell ogs-ompi-2.1.3.simg
# in container:
ogs --version
# OR directly run from host
singularity exec ogs-ompi-2.1.3.simg ogs local/path/to/square_1e0.prj
```
