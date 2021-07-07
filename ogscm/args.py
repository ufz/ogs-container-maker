import argparse

from ogscm.version import __version__


def setup_args_parser():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    parser.add_argument("--out", type=str, default="_out", help="Output directory")
    parser.add_argument(
        "--file", type=str, default="", help="Overwrite output recipe file name"
    )
    parser.add_argument(
        "--print",
        "-P",
        dest="print",
        action="store_true",
        help="Print the definition to stdout",
    )
    general_g = parser.add_argument_group("General image config")
    general_g.add_argument(
        "--format", type=str, choices=["docker", "singularity"], default="docker"
    )
    general_g.add_argument(
        "--base_image",
        type=str,
        default="ubuntu:20.04",
        help="The base image. (centos:8 is supported too)",
    )
    build_g = parser.add_argument_group("Image build options")
    build_g.add_argument(
        "--build",
        "-B",
        dest="build",
        action="store_true",
        help="Build the images from the definition files",
    )
    build_g.add_argument(
        "--build_args",
        type=str,
        default="",
        help="Arguments to the build command. Have to be "
        "quoted and **must** start with a space. E.g. "
        "--build_args ' --no-cache'",
    )
    build_g.add_argument(
        "--upload",
        "-U",
        dest="upload",
        action="store_true",
        help="Upload Docker image to registry",
    )
    build_g.add_argument(
        "--registry",
        type=str,
        default="registry.opengeosys.org/ogs/ogs",
        help="The docker registry the image is tagged and " "uploaded to.",
    )
    build_g.add_argument(
        "--tag",
        type=str,
        default="",
        help="The full docker image tag. Overwrites --registry.",
    )
    build_g.add_argument(
        "--convert",
        "-C",
        dest="convert",
        action="store_true",
        help="Convert Docker image to Singularity image",
    )
    build_g.add_argument(
        "--sif_file",
        type=str,
        default="",
        help="Overwrite output singularity image file name",
    )
    build_g.add_argument(
        "--convert-enroot",
        "-E",
        dest="convert_enroot",
        action="store_true",
        help="Convert Docker image to enroot image",
    )
    build_g.add_argument(
        "--enroot-bundle",
        dest="enroot_bundle",
        action="store_true",
        help="Convert enroot image to enroot bundle",
    )
    build_g.add_argument(
        "--enroot_file",
        type=str,
        default="",
        help="Overwrite output enroot image file name",
    )
    build_g.add_argument(
        "--force",
        dest="force",
        action="store_true",
        help="Forces overwriting of image files!",
    )
    build_g.add_argument(
        "--runtime-only",
        "-R",
        dest="runtime_only",
        action="store_true",
        help="Generate multi-stage Dockerfiles for small runtime " "images",
    )
    maint_g = parser.add_argument_group("Maintenance")
    maint_g.add_argument(
        "--clean",
        dest="cleanup",
        action="store_true",
        help="Cleans up generated files in default directories.",
    )
    deploy_g = parser.add_argument_group("Image deployment")
    deploy_g.add_argument(
        "--deploy",
        "-D",
        nargs="?",
        const="ALL",
        type=str,
        default="",
        help="Deploys to all configured hosts (in config/deploy_hosts.yml) with no additional arguments or to the specified host. Implies --build and --convert arguments.",
    )

    install_g = parser.add_argument_group("Packages to install")
    install_g.add_argument(
        "--pip",
        nargs="*",
        type=str,
        default=[],
        metavar="package",
        help="Install additional Python packages",
    )
    install_g.add_argument(
        "--packages",
        nargs="*",
        type=str,
        default=[],
        metavar="packages",
        help="Install additional OS packages",
    )

    return parser
