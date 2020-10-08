import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import packages, llvm, gnu
from hpccm.primitives import comment

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)
parse_g.add_argument(
    "--compiler",
    type=str,
    default="gcc",
    help="The compiler to use. Possible options: off, gcc, clang",
)
parse_g.add_argument(
    "--compiler_version", type=str, default="", help="Compiler version."
)

# Parse local args
local_args = parser.parse_known_args()[0]

if local_args.compiler_version == "":
    if local_args.compiler == "clang":
        local_args.compiler_version = "8"
    else:
        if hpccm.config.g_linux_distro == linux_distro.CENTOS:
            local_args.compiler_version = "10"  # required for std::filesystem
        else:
            local_args.compiler_version = None  # Use default

# set image file name
img_file = f"{local_args.compiler}-{local_args.compiler_version}"

# Optionally set out_dir
out_dir = f"{local_args.out}/{local_args.format}/{local_args.compiler}/{local_args.compiler_version}"

# Implement recipe
Stage0 += comment(f"--- Begin {filename} ---")
if local_args.compiler == "clang":
    compiler = llvm(
        extra_repository=True,
        extra_tools=True,
        version=local_args.compiler_version,
    )
else:
    compiler = gnu(
        fortran=False, extra_repository=True, version=local_args.compiler_version
    )
toolchain = compiler.toolchain
Stage0 += compiler
# Upgrade stdc++ lib after installing new compiler
# https://stackoverflow.com/a/46613656/80480
if local_args.compiler == "gcc" and local_args.compiler_version is not None:
    Stage0 += packages(apt=["libstdc++6"])

Stage0 += comment(f"--- End {filename} ---")
