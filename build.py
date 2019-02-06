# Invoke with: eval "$(python build.py --format singularity --pm conan spack \
#   --ogs True --ompi off 2.1.1)"

# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0, 3.1.2
#  Eve: 1.8.8, 1.10.2, 2.1.1
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import itertools
import json
import os
import requests
from subprocess import run

cli = argparse.ArgumentParser()
cli.add_argument("--recipe", type=str, default="ogs-builder.py")
cli.add_argument("--format", nargs="*", type=str,
                 choices=['docker', 'singularity'],
                 default=['docker', 'singularity'])
cli.add_argument("--pm", nargs="*", type=str,
                 choices=["system", "conan"],
                 default=["system", "conan"])
cli.add_argument("--ompi", nargs="*", type=str,
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
    __format = build[0]
    ogs = build[1]
    pm = build[2]
    ompi = build[3]

    out_dir = f"_out/{__format}/openmpi-{ompi}/{pm}"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    definition_file = 'Dockerfile'
    if __format == 'singularity':
        definition_file = 'Singularity.def'
    definition_file = os.path.join(out_dir, definition_file)


    # TODO: handle exit code of run (for Jenkins)
    print('Run:\n' + f"hpccm --print-exceptions --recipe {args.recipe} --format {__format} " +
          f"--userarg ogs={ogs} pm={pm} ompi={ompi} " +
          f"cmake_args='{args.cmake_args}'")
    run(f"hpccm --print-exceptions --recipe {args.recipe} --format {__format} " +
        f"--userarg ogs={ogs} pm={pm} ompi={ompi} " +
        f"cmake_args='{args.cmake_args}' > {definition_file}",
        shell=True)

    img_file = f"ogs-openmpi-{ompi}-{pm}.simg"
    if __format == 'singularity':
        run(f"sudo `which singularity` build {out_dir}/{img_file} {definition_file}",
            shell=True)
        run(f"sudo chown $USER:$USER {out_dir}/{img_file}", shell=True)
    else:
        # Get git commit hash and construct image tag name
        repo, branch = ogs.split("@")
        url = f"https://api.github.com/repos/{repo}/commits?sha={branch}"
        response = requests.get(url)
        response_data = json.loads(response.text)
        commit_hash = response_data[0]['sha']
        ogs_tag = ogs.replace('/', '.').replace('@', '.')
        tag = f"registry.opengeosys.org/ogs/ogs/openmpi-{ompi}/{pm}:{ogs_tag}"

        build_cmd = (f"docker build --build-arg OGS_COMMIT_HASH={commit_hash} "
                     f"-t {tag} -f {definition_file} .")
        print(f"Running: {build_cmd}")
        run(build_cmd, shell=True)
        if args.upload:
            run(f"docker push {tag}", shell=True)
        if args.convert:
            run(f"docker run -v /var/run/docker.sock:/var/run/docker.sock "
                f"-v $PWD/{out_dir}:/output --privileged -t --rm "
                f"singularityware/docker2singularity --name {img_file} {tag}",
                shell=True)
