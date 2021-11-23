#!/usr/bin/env python3
import archspec.cpu
import argparse
import os
import traceback
import sys

import hpccm
from hpccm.building_blocks import (
    packages,
    pip,
)
from hpccm.primitives import baseimage, comment, raw, shell

from ogscm.version import __version__
from ogscm.app import builder
from ogscm.app.deployer import deployer
import shutil


def main():  # pragma: no cover

    recipe_args_parser = argparse.ArgumentParser(add_help=False)
    parser = argparse.ArgumentParser(add_help=False)
    recipe_args_parser.add_argument("recipe", nargs="+")
    parser.add_argument("recipe", nargs="+")

    # General args
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
    general_g.add_argument(
        "--runtime_base_image",
        type=str,
        default="",
        help="The runtime base image.",
    )
    general_g.add_argument(
        "--cpu-target",
        type=str,
        default=None,
        choices=[a for a in sorted(archspec.cpu.TARGETS)],
        help="The CPU microarchitecture to optimize for.",
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

    args = parser.parse_known_args()[0]

    images_out_dir = os.path.abspath(f"{args.out}/images")
    if not os.path.exists(images_out_dir):
        os.makedirs(images_out_dir)

    hpccm.config.set_cpu_target(args.cpu_target)
    Stage0 = hpccm.Stage()
    Stage0 += raw(docker="# syntax=docker/dockerfile:experimental")

    if args.runtime_only:
        Stage0.name = "build"
    Stage0 += baseimage(image=args.base_image, _as="build")

    Stage0 += comment(
        f"Generated with ogs-container-maker {__version__}", reformat=False
    )
    Stage0 += packages(
        ospackages=["wget", "tar", "curl", "ca-certificates", "make", "unzip"]
    )

    # Prepare runtime stage
    Stage1 = hpccm.Stage()
    if args.runtime_base_image == "":
        Stage1.baseimage(image=args.base_image)
    else:
        Stage1.baseimage(image=args.runtime_base_image)
        if args.runtime_base_image == "jupyter/base-notebook":
            Stage1 += raw(docker="USER root")

    cwd = os.getcwd()
    img_file = ""
    out_dir = f"{args.out}/{args.format}"
    toolchain = None

    for recipe in recipe_args_parser.parse_known_args()[0].recipe:
        import importlib.resources as pkg_resources
        from ogscm import recipes

        # https://stackoverflow.com/a/1463370/80480
        ldict = {"filename": recipe}
        try:
            recipe_builtin = pkg_resources.read_text(recipes, recipe)
            exec(compile(recipe_builtin, recipe, "exec"), locals(), ldict)
        except Exception as err:
            error_class = err.__class__.__name__
            detail = err.args[0]
            cl, exc, tb = sys.exc_info()
            line_number = traceback.extract_tb(tb)[-1][1]
            print(f"{error_class} at line {line_number}: {detail}")
            if not os.path.exists(recipe):
                print(f"{recipe} does not exist!")
                exit(1)

            with open(recipe, "r") as reader:
                exec(compile(reader.read(), recipe, "exec"), locals(), ldict)
        if "out_dir" in ldict:
            out_dir = ldict["out_dir"]
        if "toolchain" in ldict:
            toolchain = ldict["toolchain"]
        if "img_file" not in ldict:
            print(f"img_file variable has to be set in {recipe}!")
            exit(1)
        img_file = ldict["img_file"]

    # Workaround to get the full help message
    help_parser = argparse.ArgumentParser(
        parents=[parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    help_parser.parse_args()

    # Finally parse
    args = parser.parse_args()

    ### container_info ###
    definition_file = "Dockerfile"
    if args.format == "singularity":
        definition_file = "Singularity.def"
    definition_file_path = os.path.join(out_dir, definition_file)
    if img_file[0] == "-":
        img_file = img_file[1:]
    if args.tag != "":
        tag = args.tag
    else:
        tag = f"{args.registry}/{img_file.lower()}:latest"
    # TODO:
    # context_path_size = len(self.ogsdir)
    # "{self.out_dir[context_path_size+1:]}/{self.definition_file}"
    ### end container_info ###

    if args.cleanup:
        shutil.rmtree(out_dir, ignore_errors=True)
        print("Cleaned up!")
        exit(0)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)  # For .scif files

    # General args
    if args.packages:
        Stage0 += packages(ospackages=args.packages)
        Stage1 += packages(ospackages=args.packages)

    if args.pip:
        Stage0 += pip(packages=args.pip, pip="pip3")
        Stage1 += pip(packages=args.pip, pip="pip3")

    # Create definition
    hpccm.config.set_container_format(args.format)

    stages_string = str(Stage0)

    if args.runtime_only:
        runtime_exclude = []
        if hasattr(args, "mfront") and not args.mfront:
            runtime_exclude.append("boost")
        Stage1 += Stage0.runtime(exclude=runtime_exclude)
        if (
            hasattr(args, "compiler")
            and args.compiler == "gcc"
            and args.compiler_version != None
        ):
            Stage1 += packages(apt=["libstdc++6"])
        if args.runtime_base_image == "jupyter/base-notebook":
            Stage1 += raw(docker="USER ${NB_USER}")
        stages_string += "\n\n" + str(Stage1)

    # ---------------------------- recipe end -----------------------------
    with open(definition_file_path, "w") as f:
        print(stages_string, file=f)
    if args.print:
        print(stages_string)
    else:
        print(f"Created definition {os.path.abspath(definition_file_path)}")

    # Create image
    if not args.build:
        exit(0)

    b = builder(
        args,
        images_out_dir,
        img_file,
        definition_file_path,
        tag,
        cwd,
    )
    b.build()

    # Deploy image
    if not args.deploy:
        exit(0)

    deployer(args.deploy, cwd, b.image_file)


if __name__ == "__main__":  # pragma: no cover
    main()
