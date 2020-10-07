import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import openmpi, pmix, slurm_pmi2, ucx

from packaging import version
from hpccm.primitives import label, shell
from ogscm.building_blocks.osu_benchmarks import osu_benchmarks
from copy import copy


class mpi_recipe(object):
    def __init__(self, Stage0, Stage1, args, **kwargs):
        ucx_version = "1.8.1"
        Stage0 += ucx(version=ucx_version, cuda=False)
        Stage0 += slurm_pmi2(version="17.02.11")
        pmix_version = True
        if version.parse(args.ompi) >= version.parse("4"):
            Stage0 += pmix(version="3.1.5")
            pmix_version = "/usr/local/pmix"

        mpicc = openmpi(
            version=args.ompi,
            cuda=False,
            infiniband=False,
            pmi="/usr/local/slurm-pmi2",
            pmix=pmix_version,
            ucx="/usr/local/ucx",
        )

        self.toolchain = mpicc.toolchain
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
                "org.opengeosys.mpi.version": args.ompi,
            }
        )

        if args.mpi_benchmarks:
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
            Stage1 += copy(
                _from="build", src="/usr/local/bin/mpi-*", dest="/usr/local/bin/"
            )

            # Stage0 += mlnx_ofed()
