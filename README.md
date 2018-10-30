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
singularity exec ogs-openmpi-off-conan.simg scif run ogs $PWD/square_1e0.prj

s run ~/imgs/ogs-openmpi-off-conan.simg square_1e0.prj
```

# Parallel

```bash
CONTAINER=/home/bilke/imgs/ogs_openmpi-2.1.1_conan_ufz.ogs.master.simg
ml singularity/2.6.0 OpenMPI/2.1.1-GCC-6.4.0-2.28
mkdir _out
mpirun -np 3 $CONTAINER cube_1e3.prj -o _out
singularity exec $CONTAINER vtkdiff --rel 2e-15 --abs 1e-16 -b Linear_1_to_minus1 -a pressure _out/cube_1e3_pcs_0_ts_1_t_1_000000_0.vtu cube_1e3_pcs_0_ts_1_t_1_000000_0.vtu
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
