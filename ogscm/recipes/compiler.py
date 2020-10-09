import hpccm
from hpccm import linux_distro
from hpccm.building_blocks import generic_cmake, packages, llvm, gnu
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
parse_g.add_argument(
    "--iwyy",
    dest="iwyy",
    action="store_true",
    help="Install include-what-you-use (requires clang compiler)",
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
compiler_version_string = local_args.compiler_version
if compiler_version_string == None:
    compiler_version_string = "default"

img_file += f"-{local_args.compiler}-{compiler_version_string}"

# Optionally set out_dir
out_dir += f"/{local_args.compiler}/{compiler_version_string}"

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

if local_args.iwyy and local_args.compiler != "clang":
    print("--iwyy can only be used with --compiler clang")
    exit(1)
if local_args.iwyy:
    Stage0 += packages(
        ospackages=[
            "libncurses5-dev",
            "zlib1g-dev",
            f"llvm-{local_args.compiler_version}-dev",
            f"libclang-{local_args.compiler_version}-dev",
        ]
    )
    Stage0 += generic_cmake(
        cmake_opts=[
            f"-D IWYU_LLVM_ROOT_PATH=/usr/lib/llvm-{local_args.compiler_version}"
        ],
        devel_environment={"PATH": "/usr/local/iwyy/bin:$PATH"},
        directory=f"include-what-you-use-clang_{local_args.compiler_version}.0",
        prefix="/usr/local/iwyy",
        runtime_environment={"PATH": "/usr/local/iwyy/bin:$PATH"},
        url="https://github.com/include-what-you-use/include-what-"
        f"you-use/archive/clang_{local_args.compiler_version}.0.tar.gz",
    )

Stage0 += comment(f"--- End {filename} ---")
