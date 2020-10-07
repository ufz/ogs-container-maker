# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Container info"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
import json
import os
import re
import requests
import shutil
import subprocess

from ogscm import config


class container_info:
    def __init__(self, args):
        """Initialize container info"""
        self.ogsdir = False
        self.outdir = ""
        self.definition_file = ""
        self.images_out_dir = ""
        self.img_file = ""
        self.commit_hash = ""
        self.repo = ""
        self.branch = ""
        self.git_version = ""

        name_start = "gcc"
        branch_is_release = False

        if args.ogs != "off" and args.ogs != "clean":
            if os.path.isdir(args.ogs):
                self.repo = "local"
                self.commit_hash = subprocess.run(
                    ["cd {} && git rev-parse HEAD".format(args.ogs)],
                    capture_output=True,
                    text=True,
                    shell=True,
                ).stdout.rstrip()
                if "GITLAB_CI" in os.environ:
                    if "CI_COMMIT_BRANCH" in os.environ:
                        self.branch = os.environ["CI_COMMIT_BRANCH"]
                    elif "CI_MERGE_REQUEST_SOURCE_BRANCH_NAME" in os.environ:
                        self.branch = os.environ["CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"]
                    self.git_version = os.getenv("args.ogs", "x.x.x")
                else:
                    self.branch = subprocess.run(
                        [
                            "cd {} && git branch | grep \* | cut -d ' ' -f2".format(
                                args.ogs
                            )
                        ],
                        capture_output=True,
                        text=True,
                        shell=True,
                    ).stdout
                    self.git_version = subprocess.run(
                        ["cd {} && git describe --tags".format(args.ogs)],
                        capture_output=True,
                        text=True,
                        shell=True,
                    ).stdout[0]
            else:
                # Get git commit hash and construct image tag name
                self.repo, self.branch, *commit = args.ogs.split("@")
                if commit:
                    self.commit_hash = commit[0]
                    if self.branch == "":
                        self.branch = "master"
                else:
                    if re.search(r"[\d.]+", self.branch):
                        branch_is_release = True
                    repo_split = self.repo.split("/")
                    response = requests.get(
                        f"https://gitlab.opengeosys.org/api/v4/projects/{self.repo.replace('/', '%2F')}/repository/commits?ref_name={self.branch}"
                    )
                    response_data = json.loads(response.text)
                    self.commit_hash = response_data[0]["id"]
                    # ogs_tag = args.ogs.replace('/', '.').replace('@', '.')

            if branch_is_release:
                name_start = f"ogs-{self.branch}"
            else:
                name_start = f"ogs-{self.commit_hash[:8]}"
        else:
            if args.compiler == "clang":
                name_start = "clang"

        name_openmpi = "serial"
        if args.ompi != "off":
            name_openmpi = f"openmpi-{args.ompi}"

        if len(args.cmake_args) > 0:
            cmake_args_hash = hashlib.md5(
                " ".join(args.cmake_args).encode("utf-8")
            ).hexdigest()
            cmake_args_hash_short = cmake_args_hash[:8]

        # name_image = args.base_image.replace(':', '_')
        # Removed {name_image}/
        img_folder = (
            f"{name_start}/{name_openmpi}/" f"{config.g_package_manager.name.lower()}"
        )
        self.img_file = img_folder.replace("/", "-")
        if len(args.cmake_args) > 0:
            self.img_file += f"-cmake-{cmake_args_hash_short}"
        if args.gui:
            self.img_file += "-gui"
        if args.ogs != "off" and not args.runtime_only:
            self.img_file += "-dev"

        if args.tag != "":
            self.tag = args.tag
        else:
            self.tag = f"{args.registry}/{self.img_file}:latest"

        if os.path.isdir(args.ogs):
            self.ogsdir = True

        if args.file != "":
            self.out_dir = args.out
            self.definition_file = args.file
        else:
            if self.ogsdir:
                self.out_dir = os.path.join(
                    args.ogs, f"{args.out}/{args.format}/{img_folder}"
                )
            else:
                self.out_dir = f"{args.out}/{args.format}/{img_folder}"
            if len(args.cmake_args) > 0:
                self.out_dir += f"/cmake-{cmake_args_hash_short}"
            self.images_out_dir = f"{args.out}/images"
            self.definition_file = "Dockerfile"
            if args.format == "singularity":
                self.definition_file = "Singularity.def"

    def make_dirs(self):
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)  # For .scif files
        if self.images_out_dir and not os.path.exists(self.images_out_dir):
            os.makedirs(self.images_out_dir)

    def cleanup(self):
        shutil.rmtree(self.out_dir, ignore_errors=True)
        print("Cleaned up!")
