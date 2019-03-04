#!/usr/bin/env python

import argparse
import hpccm
import os
import re

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()

dict = {
    'Dockerfile.gcc.full': {
        'jenkins': True,
        'pm': 'conan',
        'cppcheck': True,
        'docs': True,
        'gcovr': True
    },
    'Dockerfile.gcc.gui': {
        'jenkins': True,
        'pm': 'conan',
        'gui': True,
        'cppcheck': True,
    },
    'Dockerfile.clang.minimal': {
        'base_image': 'ubuntu:18.04',
        'compiler_version': '7',
        'jenkins': True,
        'pm': 'conan',
        'clang': True
    },
    'Dockerfile.clang.full': {
        'base_image': 'ubuntu:18.04',
        'compiler_version': '7',
        'jenkins': True,
        'pm': 'conan',
        'clang': True,
        'iwyy': True
    }
}

for key, value in dict.items():
    print(key)
    print(value)
    recipe = hpccm.recipe('recipes/ogs-builder.py', single_stage=True,
                          raise_exceptions=True, userarg=value)

    # Remove stage statement as this crashes Jenkins
    recipe = re.sub(r' AS stage0', '', recipe)
    with open(os.path.join(args.out, key), 'w') as f:
        print(recipe, file=f)

