# Recipe template
# Have a look and change statements with ### SET comment

### SET imports
from hpccm.primitives import comment, shell, raw
from hpccm.building_blocks import packages

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:
parse_g.add_argument("--vscode_user", type=str, default="vscode")

# Parse local args
local_args = parser.parse_known_args()[0]

### SET append to image file name, e.g.:
img_file += f"-vscode"

### SET Append to out_dir, e.g.:
out_dir += f"/vscode"

# Implement recipe
Stage0 += comment(f"Begin {filename}")

username = local_args.vscode_user
id = 1000

Stage0 += packages(ospackages=["sudo", "gdb"])
Stage0 += shell(
    commands=[
        f"groupadd --gid {id} {username}",
        f"useradd --uid {id} --gid {id} -m {username}",
        f"echo {username} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/{username}",
        f"chmod 0440 /etc/sudoers.d/{username}",
    ]
)

Stage0 += raw(docker=f"USER {username}")

Stage0 += comment(f"--- End {filename} ---")
