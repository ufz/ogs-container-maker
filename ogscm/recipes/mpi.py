from copy import copy
from packaging import version

from hpccm.building_blocks import openmpi, pmix, slurm_pmi2, ucx
from hpccm.primitives import comment, label, shell
from ogscm.building_blocks.osu_benchmarks import osu_benchmarks

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

# Parse local args
local_args = parser.parse_known_args()[0]

# set image file name
img_file += f"-openmpi-{local_args.ompi}"

# Optionally set out_dir
out_dir += f"/openmpi/{local_args.ompi}"

# Implement recipe
Stage0 += comment(f"--- Begin {filename} ---")

ucx_version = "1.8.1"
Stage0 += ucx(version=ucx_version, cuda=False)
Stage0 += slurm_pmi2(version="17.02.11")
pmix_version = True
if version.parse(local_args.ompi) >= version.parse("4"):
    Stage0 += pmix(version="3.1.5")
    pmix_version = "/usr/local/pmix"

mpicc = openmpi(
    version=local_args.ompi,
    cuda=False,
    infiniband=False,
    pmi="/usr/local/slurm-pmi2",
    pmix=pmix_version,
    ucx="/usr/local/ucx",
)

toolchain = mpicc.toolchain
Stage0 += mpicc
# OpenMPI expects this program to exist, even if it's not used.
# Default is "ssh : rsh", but that's not installed.
Stage0 += shell(
    commands=[
        "mkdir /mnt/0",
        "echo 'plm_rsh_agent = false' >> /mnt/0/openmpi-mca-params.conf",
    ]
)

Stage0 += label(
    metadata={
        "org.opengeosys.mpi": "openmpi",
        "org.opengeosys.mpi.version": local_args.ompi,
    }
)

if local_args.mpi_benchmarks:
    Stage0 += osu_benchmarks(toolchain=toolchain)
    Stage0 += shell(
        commands=[
            "mkdir -p /usr/local/mpi-examples",
            "cd /usr/local/mpi-examples",
            "curl -O https://raw.githubusercontent.com/hpc/charliecloud/674b3b4e4ad243be5565f200d8f5fb92b7544480/examples/mpihello/hello.c",
            "curl -O https://computing.llnl.gov/tutorials/mpi/samples/C/mpi_bandwidth.c",
            "curl -O https://raw.githubusercontent.com/mpitutorial/mpitutorial/gh-pages/tutorials/mpi-send-and-receive/code/ring.c",
            "mpicc -o /usr/local/bin/mpi-hello /usr/local/mpi-examples/hello.c",
            "mpicc -o /usr/local/bin/mpi-ring /usr/local/mpi-examples/ring.c",
            "mpicc -o /usr/local/bin/mpi-bandwidth /usr/local/mpi-examples/mpi_bandwidth.c",
        ]
    )
    Stage1 += copy(_from="build", src="/usr/local/bin/mpi-*", dest="/usr/local/bin/")

    # Stage0 += mlnx_ofed()

Stage0 += comment(f"--- End {filename} ---")
