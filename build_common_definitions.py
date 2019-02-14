#!/usr/bin/env python

import argparse
import hpccm
import os

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()

dict = {
    'Dockerfile.ogs.serial': {
        'pm': 'system',
        'cvode': True
    },
    'Dockerfile.ogs.ompi-2.1.2': {
        'pm': 'system',
        'cvode': True,
        'ompi': '2.1.2'
    },
    'Dockerfile.ogs.ompi-3.1.2': {
        'pm': 'system',
        'cvode': True,
        'ompi': '3.1.2'
    }
}

for key, value in dict.items():
    print(key)
    print(value)
    recipe = hpccm.recipe('recipes/ogs-builder.py', single_stage=False,
                          raise_exceptions=True, userarg=value)

    with open(os.path.join(args.out, key), 'w') as f:
        print(recipe, file=f)

