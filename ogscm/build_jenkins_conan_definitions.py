#!/usr/bin/env python
import argparse
import hpccm
import os
import subprocess

from ogscm.building_blocks import jenkins_node

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()


for image in ['clang7', 'gcc7', 'gcc8', 'gcc9']:
    Stage0 = hpccm.Stage()
    Stage0 += hpccm.primitives.baseimage(image='conanio/{0}'.format(image))
    Stage0 += hpccm.primitives.user(user='root')
    Stage0 += hpccm.building_blocks.pip(packages=['bincrafters-package-tools'],
                                        pip='pip3')
    Stage0 += jenkins_node()

    definition_file = 'Dockerfile.{0}'.format(image)
    definition_file_path = os.path.join(args.out, definition_file)
    with open(definition_file_path, 'w') as f:
        print(Stage0, file=f)
    tag = f"ogs6/conan_{image}"
    build_cmd = (f"docker build -t {tag} -f {definition_file_path} {args.out}")
    print(f"Running: {build_cmd}")
    subprocess.run(build_cmd, shell=True)

    subprocess.run(f"docker push {tag}", shell=True)
