# OpenMPI versions:
#  Taurus: 1.8.8, 1.10.2, 2.1.0, 2.1.1, 3.0.0, 3.1.2
#  Eve: 1.8.8, 1.10.2, 2.1.1
#  --> 2.1.1
# https://easybuild.readthedocs.io/en/latest/Common-toolchains.html#common-toolchains-overview
# easybuild toolchain: 2017b (2.1.1), 2018a (2.1.2), 2018b (3.1.1)
import argparse
import hashlib
import itertools
import json
import os
import platform
import requests

from subprocess import run

import hpccm

cli = argparse.ArgumentParser(
    description='Generate container image definitions.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
cli.add_argument('--recipe', type=str, default='recipes/ogs-builder.py',
                 help='HPCCM recipe')
cli.add_argument('--out', type=str, default='_out', help='Output directory')
cli.add_argument('--print', '-P', dest='print', action='store_true',
                 help='Print the definition to stdout')
options_g = cli.add_argument_group('Combinatorial options',
                                   'All combinations of the given options will '
                                   'be generated')
options_g.add_argument('--format', nargs='*', type=str,
                       choices=['docker', 'singularity'],
                       default=['docker'])
options_g.add_argument('--pm', nargs='*', type=str,
                       choices=['system', 'conan'], default=['conan'],
                       help='Package manager to install third-party '
                            'dependencies')
options_g.add_argument('--ompi', nargs='*', type=str,
                       default=['off'],
                       help='OpenMPI version, e.g. 2.1.1, 2.1.5, 3.0.1, 3.1.2')
options_g.add_argument('--ogs', nargs='*', type=str,
                       default=['ufz/ogs@master'],
                       help='OGS GitHub repo in the form \'user/repo@branch\' '
                            'or \'off\' to disable OGS building')
options_g.add_argument('--cmake_args', nargs='*', type=str, default=[''],
                       help='CMake argument sets have to be quoted and **must**'
                            ' start with a space. e.g. --cmake_args \' -DFIRST='
                            'TRUE -DFOO=BAR\' \' -DSECOND=TRUE\'')
build_g = cli.add_argument_group('Image build options')
build_g.add_argument('--build', '-B', dest='build', action='store_true',
                 help='Build the images from the definition files')
build_g.add_argument('--upload', '-U', dest='upload', action='store_true',
                 help='Upload Docker image to registry')
build_g.add_argument('--convert', '-C', dest='convert', action='store_true',
                 help='Convert Docker image to Singularity image')
build_g.add_argument('--runtime-only', '-R', dest='runtime_only',
                 action='store_true',
                 help='Generate multi-stage Dockerfiles for small runtime '
                      'images')
cli.set_defaults(build=False)
cli.set_defaults(convert=False)
cli.set_defaults(print=False)
cli.set_defaults(runtime_only=False)
cli.set_defaults(upload=False)
args = cli.parse_args()

c = list(itertools.product(args.format, args.ogs, args.pm, args.ompi, args.cmake_args))
if not args.print:
    print('Creating {} image definition(s)...'.format(len(c)))
for build in c:
    opts = {
        'ogs': build[1],
        'pm': build[2],
        'ompi': build[3],
        'cmake_args': build[4].strip()
    }
    __format = build[0]

    # args checking
    if opts['ogs'] == 'off' and opts['cmake_args'] != '':
        opts['cmake_args'] = ''
        print('--cmake_args cannot be used with --ogs off! Ignoring!')
    if __format == 'singularity':
        if args.runtime_only:
            args.runtime_only = False
            print('--runtime-only cannot be used with --format singularity! '
                  'Ignoring!')
        if args.upload:
            print('--upload cannot be used with --format singularity! '
                  'Ignoring!')
        if args.convert:
            print('--convert cannot be used with --format singularity! '
                  'Ignoring!')

    if opts['cmake_args'] != '':
        cmake_args_hash = hashlib.md5(opts['cmake_args'].encode('utf-8')).hexdigest()
        cmake_args_hash_short = cmake_args_hash[:8]

    # paths
    out_dir = f"{args.out}/{__format}/openmpi-{opts['ompi']}/{opts['pm']}"
    if opts['cmake_args'] != '':
        out_dir += f'/cmake-{cmake_args_hash_short}'
    images_out_dir = "_out/images"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    if not os.path.exists(images_out_dir):
        os.makedirs(images_out_dir)
    definition_file = 'Dockerfile'
    if __format == 'singularity':
        definition_file = 'Singularity.def'

    definition_file = os.path.join(out_dir, definition_file)

    # Create definition
    hpccm.config.set_container_format(__format)
    recipe = hpccm.recipe(args.recipe, single_stage=not args.runtime_only,
                          raise_exceptions=True, userarg=opts)
    with open(definition_file, 'w') as f:
        print(recipe, file=f)
    if args.print:
        print(recipe)
    else:
        print(f'Created definition {definition_file}')

    # Create image
    if not args.build:
        continue

    img_file = f"ogs-openmpi-{opts['ompi']}-{opts['pm']}"
    if opts['cmake_args'] != '':
        img_file += f'-cmake-{cmake_args_hash_short}'
    if not args.runtime_only:
        img_file += '-dev'
    img_file += '.simg'
    if __format == 'singularity':
        run(f"sudo `which singularity` build {images_out_dir}/{img_file} "
            f"{definition_file}", shell=True)
        run(f"sudo chown $USER:$USER {images_out_dir}/{img_file}", shell=True)
        continue

    tag = f"registry.opengeosys.org/ogs/ogs/openmpi-{opts['ompi']}/{opts['pm']}"
    commit_hash = '0'
    # Get git commit hash and construct image tag name
    if opts['ogs'] != 'off':
        repo, branch = opts['ogs'].split("@")
        url = f"https://api.github.com/repos/{repo}/commits?sha={branch}"
        response = requests.get(url)
        response_data = json.loads(response.text)
        commit_hash = response_data[0]['sha']
        ogs_tag = opts['ogs'].replace('/', '.').replace('@', '.')
        tag += f":{ogs_tag}"
        if opts['cmake_args'] != '':
            tag += f'-cmake-{cmake_args_hash_short}'

    build_cmd = (f"docker build --build-arg OGS_COMMIT_HASH={commit_hash} "
                 f"-t {tag} -f {definition_file} {out_dir}")
    print(f"Running: {build_cmd}")
    run(build_cmd, shell=True)
    if args.upload:
        run(f"docker push {tag}", shell=True)
    if args.convert:
        if 'DOCKER_MACHINE_NAME' in os.environ:
            run("mkdir -p tmp", shell=True)
            run(f"docker-machine mount singularity1:/home/bilke/tmp tmp",
                shell=True)
            run(f"docker run -v /var/run/docker.sock:/var/run/docker.sock "
                f"-v /home/bilke/tmp:/output --privileged -t --rm "
                f"singularityware/docker2singularity --name {img_file} {tag}",
                shell=True)
            run(f"mv tmp/*.simg $PWD/{images_out_dir}/", shell=True)
            if platform.system() == 'Darwin':
                run(f"umount tmp", shell=True)
            else:
                run(
                    f"docker-machine mount -u singularity1:/home/bilke/tmp tmp",
                    shell=True)
            run("rm -rf tmp", shell=True)
        else:
            run(f"docker run -v /var/run/docker.sock:/var/run/docker.sock "
                f"-v $PWD/{images_out_dir}:/output --privileged -t --rm "
                f"singularityware/docker2singularity --name {img_file} {tag}",
                shell=True)
