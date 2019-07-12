#!/usr/bin/env python
import argparse
import subprocess

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()

subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.gcc.full "
               "--jenkins --cppcheck --docs --gcovr",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.gcc.gui "
               "--jenkins --cppcheck --gui --gcovr",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.clang.full "
               "--base_image ubuntu:18.04 --compiler clang --jenkins --iwyy",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.clang.gui "
               "--base_image ubuntu:18.04 --compiler clang --jenkins --iwyy "
               "--gui",
               shell=True)
