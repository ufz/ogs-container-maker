# Invoke with: eval "$(python build.py --format singularity --pm conan spack --ogs True --ompi off 2.1.1)"

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0
#  Eve: 1.8.8, 1.10.2, 2.1.1
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import itertools
import os
import shutil
from subprocess import run

cli = argparse.ArgumentParser()
cli.add_argument("--output", type=str, default=".")
cli.add_argument("--recipe", type=str, default="ogs-builder.py")
cli.add_argument("--format", nargs="*", type=str, choices=['docker', 'singularity'], default=['docker', 'singularity'])
cli.add_argument("--pm", nargs="*", type=str, choices=["conan", "spack", "easybuild"], default=["conan", "spack", "easybuild"])
cli.add_argument("--ompi", nargs="*", type=str, choices=["off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"], default=["off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"])
cli.add_argument("--ogs", nargs="*", type=bool, choices=[True, False], default=[True, False])
cli.add_argument("--upload", dest='upload', action='store_true')
cli.add_argument("--cmake_args", type=str, default="")
cli.set_defaults(upload=False)
args = cli.parse_args()

if not os.path.exists(args.output):
    os.makedirs(args.output)

c = list(itertools.product(args.ogs, args.pm, args.ompi))
for build in c:
  # format = build[0]
  ogs = build[0]
  pm = build[1]
  ompi = build[2]

  dockerfile = f"ogs_{pm}_openmpi-{ompi}.docker.def"
  singularityfile = f"ogs_{pm}_openmpi-{ompi}.singularity.def"
  docker_singularityfile = f"ogs_{pm}_openmpi-{ompi}.docker_singularity.def"
  img_file = singularityfile.replace(".def", ".sif")
  for format in ['docker', 'singularity']:
    def_file = f"ogs_{pm}_openmpi-{ompi}.{format}.def"
    if format == 'singularity':
      img_file = def_file.replace(".def", ".sif")
    else:
      img_file = def_file.replace(".def", ".sif")
    hpccm_args = f"--format {format} --userarg ogs={ogs} pm={pm} ompi={ompi} cmake_args='{args.cmake_args}'"

    run(f"hpccm --recipe {args.recipe} {hpccm_args} > {args.output}/{def_file}", shell=True)

  from_file = open(f"{args.output}/{singularityfile}")
  from_file.readline()
  from_file.readline()
  to_file = open(f"{args.output}/{docker_singularityfile}", mode="w")
  to_file.write(f"BootStrap: localimage\nFrom: {args.output}/{img_file}\n\n")
  shutil.copyfileobj(from_file, to_file)

  tag = f"localhost:5000/openmpi-{ompi}/{pm}" # :{tag}
  run(f"docker build -t {tag} -f {args.output}/{dockerfile} {args.output}", shell=True)
  run(f"docker push {tag} ", shell=True)

  run(f"SINGULARITY_NOHTTPS=1 sudo -E `which singularity` build {args.output}/{img_file} docker://{tag}", shell=True)
  for section in ['applabels', 'apprun', 'apphelp', 'apptest']:
    run(f"sudo `which singularity` build --section {section} {args.output}/{img_file} {args.output}/{docker_singularityfile}", shell=True)
