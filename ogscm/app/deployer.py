import os
import subprocess
import sys
import yaml


class deployer(object):
    def __init__(self, args_deploy, cwd, image_file, **kwargs):
        deploy_config_filename = f"{cwd}/config/deploy_hosts.yml"
        if not os.path.isfile(deploy_config_filename):
            print(
                f"ERROR: {deploy_config_filename} not found but required for deploying!"
            )
            exit(1)

        with open(deploy_config_filename, "r") as ymlfile:
            deploy_config = yaml.load(ymlfile, Loader=yaml.FullLoader)
        if not args_deploy == "ALL" and args_deploy not in deploy_config:
            print(f'ERROR: Deploy host "{args_deploy}" not found in config!')
            exit(1)
        deploy_hosts = {}
        if args_deploy == "ALL":
            deploy_hosts = deploy_config
        else:
            deploy_hosts[args_deploy] = deploy_config[args_deploy]
        for deploy_host in deploy_hosts:
            deploy_info = deploy_hosts[deploy_host]
            print(f"Deploying to {deploy_info} ...")
            proxy_cmd = ""
            user_cmd = ""
            if "user" in deploy_info:
                user_cmd = f"{deploy_info['user']}@"
            if "proxy" in deploy_info:
                proxy_cmd = f"-e 'ssh -A -J {user_cmd}{deploy_info['proxy']}'"
                print(proxy_cmd)
            print(
                subprocess.check_output(
                    f"rsync -c -v {proxy_cmd} {image_file} {user_cmd}{deploy_info['host']}:{deploy_info['dest_dir']}",
                    shell=True,
                ).decode(sys.stdout.encoding)
            )
