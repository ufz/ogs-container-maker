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
MPI_VERSION=2.1.1
CONTAINER=~/imgs/ogs_openmpi-$(MPI_VERSION)_conan_ufz.ogs.master.simg
SRC=~/code/ogs6/ogs
PRJ_DIR=$SRC/Tests/Data/EllipticPETSc
PRJ=cube_1e3.prj
OUT=h
ml singularity/2.6.0 OpenMPI/$(MPI_VERSION)-GCC-6.4.0-2.28
# Bandwidth test
mpirun -np 4 singularity exec --app mpi-bw $CONTAINER mpi-bandwidth
#
mkdir -p $OUT
mpirun -np 3 $CONTAINER $PRJ -o $OUT
singularity exec $CONTAINER vtkdiff --rel 2e-15 --abs 1e-16 -b Linear_1_to_minus1 -a pressure $OUT/cube_1e3_pcs_0_ts_1_t_1_000000_0.vtu $PRJ_DIR/cube_1e3_pcs_0_ts_1_t_1_000000_0.vtu
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
