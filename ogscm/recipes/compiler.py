import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import packages, llvm, gnu


class compiler_recipe(object):
    def __init__(self, Stage0, Stage1, args, **kwargs):

        if args.compiler == "off":
            return

        if args.compiler_version == "":
            if args.compiler == "clang":
                args.compiler_version = "8"
            else:
                if hpccm.config.g_linux_distro == linux_distro.CENTOS:
                    args.compiler_version = "10"  # required for std::filesystem
                else:
                    args.compiler_version = None  # Use default
        if args.compiler == "clang":
            compiler = llvm(
                extra_repository=True,
                extra_tools=True,
                version=args.compiler_version,
            )
        else:
            compiler = gnu(
                fortran=False, extra_repository=True, version=args.compiler_version
            )
        self.toolchain = compiler.toolchain
        Stage0 += compiler
        # Upgrade stdc++ lib after installing new compiler
        # https://stackoverflow.com/a/46613656/80480
        if args.compiler == "gcc" and args.compiler_version is not None:
            Stage0 += packages(apt=["libstdc++6"])
