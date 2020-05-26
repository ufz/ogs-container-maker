#!/usr/bin/env python
import argparse
import subprocess

cli = argparse.ArgumentParser()
cli.add_argument("--out", type=str, default="_out")
args = cli.parse_args()

subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.gcc.full "
               "--jenkins --docs --gcovr",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.gcc.gui "
               "--jenkins --pm conan --cvode --cppcheck --docs --gcovr --gui",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.clang.full "
               "--base_image ubuntu:18.04 --compiler clang --jenkins --iwyy "
               "--compiler_version 9",
               shell=True)
subprocess.run(f"python ogscm/cli.py --out {args.out} --file Dockerfile.clang.gui "
               "--base_image ubuntu:20.04 --compiler clang --jenkins --iwyy "
               "--compiler_version 9 --pm system --gui",
               shell=True)
