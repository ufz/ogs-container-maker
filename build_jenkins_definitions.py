#!/usr/bin/env python

import argparse
import hpccm
import os

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()

dict = {
    'Dockerfile.gcc.full': {
        'jenkins': True,
        'pm': 'conan',
        'cppcheck': True,
        'cvode': True
    }
}

for key, value in dict.items():
    print(key)
    print(value)
    recipe = hpccm.recipe('ogs-builder.py', single_stage=True,
                          raise_exceptions=True, userarg=value)
    print(recipe)
    with open(os.path.join(args.out, key), 'w') as f:
        print(recipe, file=f)

