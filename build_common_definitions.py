#!/usr/bin/env python
import subprocess

subprocess.run(f"python build.py --pm system --cvode "
               "--ompi off 2.1.2 3.1.2 4.0.0",
               shell=True)

subprocess.run(f"python build.py --file Dockerfile.gcc.full --jenkins "
               "--cppcheck --docs --gcovr",
               shell=True)
subprocess.run(f"python build.py --file Dockerfile.gcc.gui --jenkins "
               "--cppcheck --gui --gcovr",
               shell=True)
subprocess.run(f"python build.py --file Dockerfile.clang.full "
               "--base_image ubuntu:18.04 --compiler 7 --clang --jenkins "
               "--iwyy",
               shell=True)
