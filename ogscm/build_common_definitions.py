#!/usr/bin/env python
import subprocess

subprocess.run(f"python cli.py --pm system --cvode "
               "--ompi off 2.1.6 3.1.4 4.0.1",
               shell=True)

subprocess.run(f"python cli.py --file Dockerfile.gcc.full --jenkins "
               "--cppcheck --docs --gcovr",
               shell=True)
subprocess.run(f"python cli.py --file Dockerfile.gcc.gui --jenkins "
               "--cppcheck --gui --gcovr",
               shell=True)
subprocess.run(f"python cli.py --file Dockerfile.clang.full "
               "--base_image ubuntu:18.04 --compiler clang --jenkins "
               "--iwyy",
               shell=True)
