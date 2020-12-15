from copy import copy

import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import (
    openmpi,
    generic_autotools,
    pmix,
    slurm_pmi2,
    ucx,
    gdrcopy,
    knem,
    multi_ofed,
    mlnx_ofed,
)
from hpccm.primitives import comment, copy, label, shell, environment, runscript

if hpccm.config.g_linux_distro != linux_distro.CENTOS:
    print(
        "OpenMPI is supported on CentOS only! Please supply --base_image 'centos:8' parameter!"
    )
    exit(1)

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)
parse_g.add_argument(
    "--ompi",
    type=str,
    default="4.0.5",
    help="OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2",
)
parse_g.add_argument(
    "--mpi_benchmarks",
    dest="mpi_benchmarks",
    action="store_true",
    help="Installs OSU MPI " "benchmarks as scif app and mpi_bw, mpi_ring," "mpi_hello",
)
# parse_g.add_argument(
#     "--ucx",
#     type=str,
#     default="1.8.1",
#     help="UCX version",
# )
# parse_g.add_argument(
#     "--slurm",
#     type=str,
#     default="20.02.5",
#     help="Slurm version",
# )
# parse_g.add_argument(
#     "--infiniband",
#     dest="infiniband",
#     action="store_true",
#     help="Enable Infiniband",
# )

# Parse local args
local_args = parser.parse_known_args()[0]

# set image file name
img_file += f"-openmpi-{local_args.ompi}"

# Optionally set out_dir
out_dir += f"/openmpi/{local_args.ompi}"

# Implement recipe
Stage0 += comment(f"--- Begin {filename} ---")

# Begin copy from https://github.com/NVIDIA/hpc-container-maker/blob/master/recipes/osu_benchmarks/common.py
Stage0 += shell(commands=["ln -s /usr/bin/gcc /usr/bin/cc"])  # Fix for gdrcopy
Stage0 += gdrcopy(ldconfig=True)
Stage0 += knem(ldconfig=True)

# Mellanox legacy OFED support
mlnx_versions = ["4.6-1.0.1.1", "4.7-3.2.9.0", "4.9-0.1.7.0", "4.9-2.2.4.0"]
Stage0 += multi_ofed(
    inbox=False, mlnx_versions=mlnx_versions, prefix="/usr/local/ofed", symlink=False
)

# RDMA-core based OFED support
Stage0 += mlnx_ofed(version="5.1-0.6.6.0", symlink=False)

# UCX default - RDMA-core based OFED
Stage0 += ucx(
    version="1.9.0",
    cuda=False,
    gdrcopy="/usr/local/gdrcopy",
    knem="/usr/local/knem",
    disable_static=True,
    enable_mt=True,
)

# UCX - Mellanox legacy support
Stage0 += ucx(
    version="1.9.0",
    build_environment={
        "LD_LIBRARY_PATH": "/usr/local/ofed/4.6-1.0.1.1/lib:${LD_LIBRARY_PATH}"
    },
    cuda=False,
    environment=False,
    gdrcopy="/usr/local/gdrcopy",
    knem="/usr/local/knem",
    prefix="/usr/local/ucx-mlnx-legacy",
    disable_static=True,
    enable_mt=True,
    with_verbs="/usr/local/ofed/4.6-1.0.1.1/usr",
    with_rdmacm="/usr/local/ofed/4.6-1.0.1.1/usr",
)

# Symlink legacy UCX into legacy OFED versions
Stage0 += shell(
    commands=[
        "ln -s /usr/local/ucx-mlnx-legacy/{1}/* /usr/local/ofed/{0}/usr/{1}".format(
            version, directory
        )
        for version in mlnx_versions
        for directory in ["bin", "lib"]
    ]
)

# PMI support
Stage0 += slurm_pmi2(prefix="/usr/local/pmi")
Stage0 += pmix()

# OpenMPI
mpicc = openmpi(
    cuda=False,
    infiniband=False,
    ldconfig=True,
    ucx=True,
    version=local_args.ompi,
    disable_oshmem=True,
    disable_static=True,
    enable_mca_no_build="btl-uct",
    with_slurm=False,
    with_pmi="/usr/local/pmi",
    with_pmix="/usr/local/pmix",
)
toolchain = mpicc.toolchain
Stage0 += mpicc

# OpenMPI expects this program to exist, even if it's not used.
# Default is "ssh : rsh", but that's not installed.
# TODO: /usr/etc/openmpi-mca-params.conf ?
# Stage0 += shell(
#     commands=[
#         "mkdir /mnt/0",
#         "echo 'plm_rsh_agent = false' >> /mnt/0/openmpi-mca-params.conf",
#         "echo 'mpi_warn_on_fork = 0' >> /mnt/0/openmpi-mca-params.conf",
#         "echo 'btl_openib_warn_default_gid_prefix = 0' >> /mnt/0/openmpi-mca-params.conf",
#     ]
# )

Stage0 += label(
    metadata={
        "org.opengeosys.mpi": "openmpi",
        "org.opengeosys.mpi.version": local_args.ompi,
        # "org.opengeosys.ucx": local_args.ucx,
        # "org.opengeosys.slurm": local_args.slurm,
        # "org.opengeosys.pmix": pmix_version,
    }
)

# Allow running MPI as root
Stage1 += environment(
    variables={"OMPI_ALLOW_RUN_AS_ROOT": "1", "OMPI_ALLOW_RUN_AS_ROOT_CONFIRM": "1"}
)

# Entrypoint
Stage1 += shell(
    commands=[
        "curl -o /usr/local/bin/entrypoint.sh https://gitlab.opengeosys.org/ogs/container-maker/-/raw/main/ogscm/recipes/mpi-entrypoint.sh"
    ]
)
Stage1 += runscript(commands=["/usr/local/bin/entrypoint.sh"])

# Performance and compatibility tuning
Stage1 += environment(
    variables={
        "CUDA_CACHE_DISABLE": "1",
        "MELLANOX_VISIBLE_DEVICES": "all",  # enroot
        "OMPI_MCA_pml": "ucx",
        "UCX_TLS": "all",
    }
)

if local_args.mpi_benchmarks:
    Stage0 += generic_autotools(
        build_environment={"CC": "mpicc", "CXX": "mpicxx"},
        # enable_cuda=True,
        prefix="/usr/local/osu",
        url="http://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-5.6.3.tar.gz",
        # with_cuda="/usr/local/cuda",
    )

    # Copy the OSU Micro-Benchmark binaries into the deployment stage
    Stage1 += copy(_from="0", src="/usr/local/osu", dest="/usr/local/osu")

    # Add the OSU Micro-Benchmarks to the default PATH
    base_path = "/usr/local/osu/libexec/osu-micro-benchmarks"
    Stage1 += environment(
        variables={
            "PATH": "{0}:{0}/mpi/collective:{0}/mpi/one-sided:{0}/mpi/pt2pt:{0}/mpi/startup:$PATH".format(
                base_path
            )
        }
    )
    # Stage0 += osu_benchmarks(toolchain=toolchain)
    # Stage0 += shell(
    #     commands=[
    #         "mkdir -p /usr/local/mpi-examples",
    #         "cd /usr/local/mpi-examples",
    #         "curl -O https://raw.githubusercontent.com/hpc/charliecloud/674b3b4e4ad243be5565f200d8f5fb92b7544480/examples/mpihello/hello.c",
    #         "curl -O https://computing.llnl.gov/tutorials/mpi/samples/C/mpi_bandwidth.c",
    #         "curl -O https://raw.githubusercontent.com/mpitutorial/mpitutorial/gh-pages/tutorials/mpi-send-and-receive/code/ring.c",
    #         "mpicc -o /usr/local/bin/mpi-hello /usr/local/mpi-examples/hello.c",
    #         "mpicc -o /usr/local/bin/mpi-ring /usr/local/mpi-examples/ring.c",
    #         "mpicc -o /usr/local/bin/mpi-bandwidth /usr/local/mpi-examples/mpi_bandwidth.c",
    #     ]
    # )
    # Stage1 += copy(_from="build", src="/usr/local/bin/mpi-*", dest="/usr/local/bin/")

Stage0 += comment(f"--- End {filename} ---")
