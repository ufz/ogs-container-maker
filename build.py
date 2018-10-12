# Invoke with: eval "$(python build.py --format singularity --pm conan spack --ogs True --ompi off 2.1.1)"

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0
#  Eve: 1.8.8, 1.10.2, 2.1.1
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import itertools

cli = argparse.ArgumentParser()
cli.add_argument("--output", type=str, default=".")
cli.add_argument("--recipe", type=str, default="ogs-builder.py")
cli.add_argument("--format", nargs="*", type=str, choices=['docker', 'singularity'], default=['docker', 'singularity'])
cli.add_argument("--pm", nargs="*", type=str, choices=["conan", "spack", "easybuild"], default=["conan", "spack", "easybuild"])
cli.add_argument("--ompi", nargs="*", type=str, choices=["off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"], default=["off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"])
cli.add_argument("--ogs", nargs="*", type=bool, choices=[True, False], default=[True, False])
cli.add_argument("--upload", dest='upload', action='store_true')
cli.set_defaults(upload=False)
args = cli.parse_args()

c = list(itertools.product(args.format, args.ogs, args.pm, args.ompi))
for build in c:
  format = build[0]
  ogs = build[1]
  pm = build[2]
  ompi = build[3]

  def_file = f"ogs_{pm}_openmpi-{ompi}.{format}.def"
  if format == 'singularity':
    img_file = def_file.replace(".def", ".simg")
  else:
    img_file = def_file.replace(".def", ".simg")
  hpccm_args = f"--format {format} --userarg ogs={ogs} pm={pm} ompi={ompi}"

  cmds = []
  cmds.append(f"hpccm --recipe {args.recipe} {hpccm_args} > {args.output}/{def_file}")
  if format == 'singularity':
    cmds.extend([
      f"sudo `which singularity` build {args.output}/{img_file} {args.output}/{def_file}",
      f"sudo chown $USER:$USER {args.output}/{img_file}",
    ])
  else:
    tag = f"registry.opengeosys.org/ogs/docker/openmpi-{ompi}/{pm}" # :{tag}
    cmds.append(f"docker build -t {tag} -f {def_file} {args.output}")
    if args.upload:
      cmds.append(f"docker push {tag}")

  print('\n'.join(cmds))
