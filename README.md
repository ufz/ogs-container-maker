TODO: 

- hpc-container-maker submodule? --> no conda
- serial config without mpi, test
- migrate Jenkins container definitions
- use conda inside container?

## Conda

```bash
conda activate ogs
conda env update -f=../../environment.yml
```

## Usage

### Generate

```bash
hpccm --recipe ogs-builder.py > Dockerfile
hpccm --recipe ogs-builder.py --format singularity > Singularity

# With user options
hpccm --recipe ogs-builder.py --format singularity --userarg ompi=2.1.3 centos=true
```

### Run

Overwrite Docker entry point:

```bash
docker run --it --entrypoint "/bin/bash" test-builder
```

```
docker run registry.opengeosys.org/ogs/ogs/openmpi-2.1.1/conan:ufz.ogs.master scif run ogs
singularity exec ogs-openmpi-off-conan.simg scif run ogs
```

## Dev

```bash
# Local
hpccm --recipe ogs-builder.py --userarg centos=False ompi=off | docker build -t test-builder -

# Local with context
hpccm --recipe ogs-builder.py --userarg centos=False ompi=off > Dockerfile && docker build -t test-builder . && rm Dockerfile

# Remote
hpccm --recipe ogs-builder.py --userarg centos=False ompi=off | ssh singularity1 "docker build -t test-builder -"
```
