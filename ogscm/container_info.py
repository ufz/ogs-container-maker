# pylint: disable=invalid-name, too-few-public-methods
# pylint: disable=too-many-instance-attributes
"""Container info"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import hashlib
import os
import requests
import shutil
import subprocess

from ogscm import config


class container_info():
    def __init__(self, args_iter, args, old_cwd):
        """Initialize container info"""
        self.buildkit = False
        self.outdir = ''
        self.definition_file = ''
        self.images_out_dir = ''

        container_format = args_iter[0]
        ogs_version = args_iter[1]
        ompi = args_iter[3]
        cmake_args = args_iter[4].strip().split(' ')
        name_start = 'gcc'

        if ogs_version != 'off':
            if os.path.isdir(ogs_version):
                commit_hash = subprocess.run(
                    ['cd {} && git rev-parse HEAD'.format(ogs_version)],
                    capture_output=True,
                    text=True,
                    shell=True).stdout.rstrip()
            else:
                # Get git commit hash and construct image tag name
                repo, branch = ogs_version.split("@")
                url = f"https://api.github.com/repos/{repo}/commits?sha={branch}"
                response = requests.get(url)
                response_data = json.loads(response.text)
                commit_hash = response_data[0]['sha']
                # ogs_tag = ogs_version.replace('/', '.').replace('@', '.')

            name_start = f'ogs-{commit_hash[:8]}'
        else:
            if args.compiler == 'clang':
                name_start = 'clang'

        name_openmpi = 'serial'
        if ompi != 'off':
            name_openmpi = f"openmpi-{ompi}"

        if len(cmake_args) > 0:
            cmake_args_hash = hashlib.md5(
                ' '.join(cmake_args).encode('utf-8')).hexdigest()
            cmake_args_hash_short = cmake_args_hash[:8]

        name_image = args.base_image.replace(':', '_')
        img_folder = f"{name_image}/{name_start}/{name_openmpi}/{config.g_package_manager.name.lower()}"
        img_file = img_folder.replace("/", "-")
        if len(cmake_args) > 0:
            img_file += f'-cmake-{cmake_args_hash_short}'
        if args.gui:
            img_file += '-gui'
        if args.docs:
            img_file += '-docs'
        if ogs_version != 'off' and not args.runtime_only:
            img_file += '-dev'
        docker_repo = img_file
        img_file += '.sif'

        self.tag = f"{args.registry}/{docker_repo}:latest"

        if os.path.isdir(ogs_version):
            self.buildkit = True

        if args.file != '':
            self.out_dir = args.out
            self.definition_file = args.file
        else:
            if self.buildkit:
                self.out_dir = os.path.join(
                    ogs_version, f"{args.out}/{container_format}/{img_folder}")
            else:
                self.out_dir = os.path.join(
                    old_cwd, f"{args.out}/{container_format}/{img_folder}")
            if len(cmake_args) > 0:
                self.out_dir += f'/cmake-{cmake_args_hash_short}'
            self.images_out_dir = os.path.join(old_cwd, f"{args.out}/images")
            self.definition_file = 'Dockerfile'
            if container_format == 'singularity':
                self.definition_file = 'Singularity.def'

    def make_dirs(self):
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)  # For .scif files
        if not os.path.exists(self.images_out_dir):
                os.makedirs(self.images_out_dir)

    def cleanup(self):
        shutil.rmtree(self.out_dir, ignore_errors=True)
        print('Cleaned up!')