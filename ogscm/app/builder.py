import subprocess
import sys
import re
import os


class builder(object):
    def __init__(self, **kwargs):
        self.__format = kwargs.get("format", "docker")
        self.__definition_file = kwargs.get("definition_file")
        self.__info = kwargs.get("info")
        self.__args = kwargs.get("args")

    def build(self):
        if self.__format == "singularity":
            self.build_singularity()
        else:
            self.build_docker()

    def build_singularity(self):
        sif_file = f"{self.__info.images_out_dir}/{self.__info.img_file}.sif"
        subprocess.run(
            f"sudo `which singularity` build --force {sif_file}"
            f"{self.__definition_file}",
            shell=True,
        )
        subprocess.run(
            f"sudo chown $USER:$USER {sif_file}",
            shell=True,
        )
        # TODO: adapt this
        exit(0)

    def build_docker(self):
        build_cmd = (
            f"DOCKER_BUILDKIT=1 docker build {self.__args.build_args} "
            f"-t {self.__info.tag} -f {self.__definition_file} ."
        )
        print(f"Running: {build_cmd}")
        subprocess.run(build_cmd, shell=True)
        inspect_out = subprocess.check_output(
            f"docker inspect {self.__info.tag} | grep Id", shell=True
        ).decode(sys.stdout.encoding)
        image_id = re.search("sha256:(\w*)", inspect_out).group(1)
        image_id_short = image_id[0:12]

        if self.__args.upload:
            subprocess.run(f"docker push {self.__info.tag}", shell=True)
        if self.__args.sif_file:
            image_file = f"{self.__info.images_out_dir}/{self.__args.sif_file}"
        else:
            image_file = f"{self.__info.images_out_dir}/{self.__info.img_file}-{image_id_short}.sif"
        if self.__args.convert and not os.path.exists(image_file):
            subprocess.run(
                f"cd {self.__info.cwd} && singularity build --force {image_file} docker-daemon:{self.__info.tag}",
                shell=True,
            )
