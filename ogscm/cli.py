#!/usr/bin/env python3

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0, 3.1.4, 4.0.1
#  Eve: 1.8.8, 1.10.2, 2.1.1, 4.0.0
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import os
import subprocess
import sys
import yaml

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

import ogscm
from ogscm.cli_args import Cli_Args
from ogscm.container_info import container_info
from ogscm.version import __version__
from ogscm.building_blocks import ogs
from ogscm.app import builder
from ogscm.recipes import compiler_recipe, mpi_recipe
from ogscm.recipes.ogs import ogs_recipe


def main():  # pragma: no cover
    cli = Cli_Args()
    args = cli.parse_args()

    ogscm.config.set_package_manager(args.pm)
    cmake_args = args.cmake_args.strip().split(" ")

    # args checking
    if not args.deploy == "":
        args.build = True
        args.convert = True
    if not args.sif_file == "":
        args.convert = True
    if (
        (args.ogs == "off" or args.ogs == "clean")
        and len(cmake_args) > 0
        and cmake_args[0] != ""
    ):
        cmake_args = []
        print("--cmake_args cannot be used with --ogs off! Ignoring!")
    if args.format == "singularity":
        if args.runtime_only:
            args.runtime_only = False
            print(
                "--runtime-only cannot be used with --format singularity! " "Ignoring!"
            )
        if args.upload:
            print("--upload cannot be used with --format singularity! " "Ignoring!")
        if args.convert:
            print("--convert cannot be used with --format singularity! " "Ignoring!")

    info = container_info(args)
    if args.cleanup:
        info.cleanup()
        exit(0)
    info.make_dirs()

    if args.ompi != "off":
        if args.base_image == "ubuntu:20.04":
            args.base_image = "centos:8"
            print(
                "Setting base_image to 'centos:8'. OpenMPI is supported on CentOS only."
            )

    # Create definition
    hpccm.config.set_container_format(args.format)

    # ------------------------------ recipe -------------------------------
    Stage0 = hpccm.Stage()
    Stage0 += raw(docker="# syntax=docker/dockerfile:experimental")

    if args.runtime_only:
        Stage0.name = "build"
    Stage0 += baseimage(image=args.base_image, _as="build")

    Stage0 += comment(
        f"Generated with ogs-container-maker {__version__}", reformat=False
    )

    # Prepare runtime stage
    Stage1 = hpccm.Stage()
    Stage1.baseimage(image=args.base_image)

    Stage0 += packages(ospackages=["wget", "tar", "curl", "make"])

    toolchain = compiler_recipe(Stage0, Stage1, args).toolchain

    # Install scif in all stages
    Stage0 += pip(packages=["scif"], pip="pip3")
    Stage1 += pip(packages=["scif"], pip="pip3")

    if args.ompi != "off":
        toolchain = mpi_recipe(Stage0, Stage1, args).toolchain

    ogs_recipe(Stage0, Stage1, args, info, toolchain)

    stages_string = str(Stage0)

    if args.runtime_only:
        Stage1 += Stage0.runtime(exclude=["boost"])
        if args.compiler == "gcc" and args.compiler_version != None:
            Stage1 += packages(apt=["libstdc++6"])
        stages_string += "\n\n" + str(Stage1)

    # ---------------------------- recipe end -----------------------------
    with open(info.definition_file_path, "w") as f:
        print(stages_string, file=f)
    if args.print:
        print(stages_string)
    else:
        print(f"Created definition {os.path.abspath(info.definition_file_path)}")

    # Create image
    if not args.build:
        exit(0)

    builder(args=args, info=info).build()

    # Deploy image
    if not args.deploy:
        exit(0)

    deploy_config_filename = f"{info.cwd}/config/deploy_hosts.yml"
    if not os.path.isfile(deploy_config_filename):
        print(f"ERROR: {deploy_config_filename} not found but required for deploying!")
        exit(1)

    with open(deploy_config_filename, "r") as ymlfile:
        deploy_config = yaml.load(ymlfile, Loader=yaml.FullLoader)
    if not args.deploy == "ALL" and not args.deploy in deploy_config:
        print(f'ERROR: Deploy host "{args.deploy}" not found in config!')
        exit(1)
    deploy_hosts = {}
    if args.deploy == "ALL":
        deploy_hosts = deploy_config
    else:
        deploy_hosts[args.deploy] = deploy_config[args.deploy]
    for deploy_host in deploy_hosts:
        deploy_info = deploy_hosts[deploy_host]
        print(f"Deploying to {deploy_info} ...")
        proxy_cmd = ""
        user_cmd = ""
        if "user" in deploy_info:
            user_cmd = f"{deploy_info['user']}@"
        if "proxy" in deploy_info:
            proxy_cmd = f"-e 'ssh -A -J {user_cmd}{deploy_info['proxy']}'"
            print(proxy_cmd)
        print(
            subprocess.check_output(
                f"rsync -c -v {proxy_cmd} {image_file} {user_cmd}{deploy_info['host']}:{deploy_info['dest_dir']}",
                shell=True,
            ).decode(sys.stdout.encoding)
        )


if __name__ == "__main__":  # pragma: no cover
    main()
