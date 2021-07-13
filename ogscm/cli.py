#!/usr/bin/env python3
import argparse
import os
import traceback
import sys

import hpccm
from hpccm.building_blocks import (
    packages,
    pip,
)
from hpccm.primitives import (
    baseimage,
    comment,
    raw,
)

from ogscm.version import __version__
from ogscm.args import setup_args_parser
from ogscm.app import builder
from ogscm.app.deployer import deployer
import shutil


def main():  # pragma: no cover

    parser = setup_args_parser()
    recipe_args_parser = argparse.ArgumentParser(add_help=False)
    recipe_args_parser.add_argument("recipe", nargs="+")
    parser.add_argument("recipe", nargs="+")

    # General args
    args = parser.parse_known_args()[0]
    execute = True

    images_out_dir = os.path.abspath(f"{args.out}/images")
    if not os.path.exists(images_out_dir):
        os.makedirs(images_out_dir)

    Stage0 = hpccm.Stage()
    Stage0 += raw(docker="# syntax=docker/dockerfile:experimental")

    if args.runtime_only:
        Stage0.name = "build"
    Stage0 += baseimage(image=args.base_image, _as="build")

    Stage0 += comment(
        f"Generated with ogs-container-maker {__version__}", reformat=False
    )
    Stage0 += packages(ospackages=["wget", "tar", "curl", "make", "unzip"])

    # Prepare runtime stage
    Stage1 = hpccm.Stage()
    Stage1.baseimage(image=args.base_image)

    cwd = os.getcwd()
    img_file = ""
    out_dir = f"{args.out}/{args.format}"
    toolchain = None

    for recipe in recipe_args_parser.parse_known_args()[0].recipe:
        import importlib.resources as pkg_resources
        from ogscm import recipes

        # https://stackoverflow.com/a/1463370/80480
        ldict = {"filename": recipe}
        if os.path.exists(recipe):
            with open(recipe, "r") as reader:
                exec(compile(reader.read(), recipe, "exec"), locals(), ldict)
        else:
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
    if args.pip:
        Stage0 += pip(packages=args.pip, pip="pip3")
        Stage1 += pip(packages=args.pip, pip="pip3")

    if args.packages:
        Stage0 += packages(ospackages=args.packages)
        Stage1 += packages(ospackages=args.packages)

    # Create definition
    hpccm.config.set_container_format(args.format)

    stages_string = str(Stage0)

    if args.runtime_only:
        Stage1 += Stage0.runtime(exclude=["boost"])
        if args.compiler == "gcc" and args.compiler_version != None:
            Stage1 += packages(apt=["libstdc++6"])
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
