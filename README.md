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

```bash
hpccm --recipe ogs-builder.py > Dockerfile
hpccm --recipe ogs-builder.py --format singularity > Singularity

# With user options
hpccm --recipe ogs-builder.py --format singularity --userarg ompi=2.1.3 centos=true
```

## Dev

```bash
hpccm --recipe ogs-builder.py --userarg centos=False ompi=off | docker build -t test-builder -
```
