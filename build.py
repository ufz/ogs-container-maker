# Invoke with: eval "$(python build.py --format singularity --pm conan spack \
#   --ogs True --ompi off 2.1.1)"

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0
#  Eve: 1.8.8, 1.10.2, 2.1.1
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import itertools
from subprocess import run

cli = argparse.ArgumentParser()
cli.add_argument("--recipe", type=str, default="ogs-builder.py")
cli.add_argument("--format", nargs="*", type=str,
                 choices=['docker', 'singularity'],
                 default=['docker', 'singularity'])
cli.add_argument("--pm", nargs="*", type=str,
                 choices=["conan", "spack", "easybuild"],
                 default=["conan", "spack", "easybuild"])
cli.add_argument("--ompi", nargs="*", type=str, choices=[
                 "off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"],
                 default=["off", "2.1.1", "2.1.5", "3.0.1", "3.1.2"])
cli.add_argument("--ogs", nargs="*", type=str, default=['ufz/ogs@master'])
cli.add_argument("--upload", dest='upload', action='store_true')
cli.add_argument("--convert", dest='convert', action='store_true')
cli.add_argument("--cmake_args", type=str, default="")
cli.set_defaults(upload=False)
cli.set_defaults(convert=False)
args = cli.parse_args()

c = list(itertools.product(args.format, args.ogs, args.pm, args.ompi))
for build in c:
    format = build[0]
    ogs = build[1]
    pm = build[2]
    ompi = build[3]

    out_dir = f"_out/{format}/openmpi-{ompi}/{pm}"

    # TODO: handle exit code of run (for Jenkins)
    print('Run:\n' + f"hpccm --recipe {args.recipe} --format {format} --out {out_dir} " +
        f"--userarg ogs={ogs} pm={pm} ompi={ompi} " +
        f"cmake_args='{args.cmake_args}'")
    run(f"hpccm --recipe {args.recipe} --format {format} --out {out_dir} " +
        f"--userarg ogs={ogs} pm={pm} ompi={ompi} " +
        f"cmake_args='{args.cmake_args}'",
        shell=True)

    if format == 'singularity':
        img_file = f"ogs-openmpi-{ompi}-{pm}.simg"
        run(f"sudo `which singularity` build {out_dir}/{img_file} {out_dir}/Singularity.def",
            shell=True)
        run(f"sudo chown $USER:$USER {out_dir}/{img_file}", shell=True)
    else:
        ogs_tag = ogs.replace('/', '.').replace('@', '.')
        tag = f"registry.opengeosys.org/ogs/ogs/openmpi-{ompi}/{pm}:{ogs_tag}"
        run(f"docker build -t {tag} -f {out_dir}/Dockerfile .", shell=True)
        if args.upload:
            run(f"docker push {tag}", shell=True)
        if args.convert:
            run(f"docker run -v /var/run/docker.sock:/var/run/docker.sock "
                f"-v $PWD/{out_dir}:/output --privileged -t --rm "
                f"singularityware/docker2singularity {tag}", shell=True)
