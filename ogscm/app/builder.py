import subprocess
import sys
import re
import os


class builder(object):
    def __init__(
        self, args, images_out_dir, img_file, definition_file_path, tag, cwd, **kwargs
    ):
        self.__format = args.format
        self.__args = args
        self.__images_out_dir = images_out_dir
        self.__img_file = img_file
        self.__definition_file_path = definition_file_path
        self.__tag = tag
        self.__cwd = cwd

    def build(self):
        if self.__format == "singularity":
            self.build_singularity()
        else:
            self.build_docker()

    def build_singularity(self):
        sif_file = f"{self.__images_out_dir}/{self.__img_file}.sif"
        subprocess.run(
            f"sudo `which singularity` build --force {sif_file} "
            f"{self.__definition_file_path}",
            shell=True,
            check=True,
        )
        subprocess.run(f"sudo chown $USER {sif_file}", shell=True, check=True)
        print(f"Built Singularity image file: {sif_file}")
        # TODO: adapt this
        exit(0)

    def build_docker(self):
        build_cmd = (
            f"DOCKER_BUILDKIT=1 docker build {self.__args.build_args} "
            f"-t {self.__tag} -f {self.__definition_file_path} ."
        )
        print(f"Running: {build_cmd}")
        subprocess.run(build_cmd, shell=True, check=True)
        inspect_out = subprocess.check_output(
            f"docker inspect {self.__tag} | grep Id", shell=True
        ).decode(sys.stdout.encoding)
        image_id = re.search("sha256:(\w*)", inspect_out).group(1)
        image_id_short = image_id[0:12]

        if self.__args.upload:
            subprocess.run(f"docker push {self.__tag}", shell=True, check=True)
        image_base_name = f"{self.__images_out_dir}/{self.__img_file}-{image_id_short}"
        if self.__args.sif_file:
            self.image_file = f"{self.__images_out_dir}/{self.__args.sif_file}"
        else:
            self.image_file = f"{image_base_name}.sif"
        if self.__args.convert:
            if (
                not os.path.exists(self.image_file)
                or self.__args.force
                or self.__args.sif_file
            ):
                subprocess.run(
                    f"cd {self.__cwd} && singularity build --force {self.image_file} docker-daemon:{self.__tag}",
                    shell=True,
                    check=True,
                )
                print(f"Built Singularity image file: {self.image_file}")
            else:
                print(f"Already existing Singularity image file: {self.image_file}")

        if self.__args.enroot_file:
            self.image_file = f"{self.__images_out_dir}/{self.__args.enroot_file}"
        else:
            self.image_file = f"{image_base_name}.sqsh"
        if self.__args.convert_enroot and (
            not os.path.exists(self.image_file) or self.__args.force
        ):
            subprocess.run(
                # See https://www.mankier.com/1/mksquashfs for options.
                f"cd {self.__cwd} && rm -f {self.image_file} && ENROOT_SQUASH_OPTIONS='-comp xz -b 512K' enroot import -o {self.image_file} dockerd://{self.__tag}",
                shell=True,
                check=True,
            )
            print(f"Wrote image file {self.image_file}")

        bundle_file = f"{self.image_file[:-5]}.run"
        if self.__args.enroot_bundle and (
            not os.path.exists(bundle_file) or self.__args.force
        ):
            subprocess.run(
                f"cd {self.__cwd} && rm -f {bundle_file} && enroot bundle -o {bundle_file} {self.image_file}",
                shell=True,
                check=True,
            )
            print(f"Wrote bundle file {bundle_file}")
