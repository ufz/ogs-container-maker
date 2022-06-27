# Recipe template
# Have a look and change statements with ### SET comment

### SET imports
from hpccm.primitives import comment, shell, raw
from hpccm.building_blocks import packages

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:
# parse_g.add_argument("--my_arg", type=str, default="default_value")

# Parse local args
local_args = parser.parse_known_args()[0]

### SET append to image file name, e.g.:
img_file += f"-web"

### SET Append to out_dir, e.g.:
out_dir += f"/web"

# Implement recipe
Stage0 += comment(f"Begin {filename}")

Stage0 += shell(commands=["curl -fsSL https://deb.nodesource.com/setup_18.x | bash -"])
Stage0 += packages(ospackages=["nodejs", "pandoc"])
Stage0 += shell(
    commands=[
        "npm install --global yarn",
        "wget https://github.com/gohugoio/hugo/releases/download/v0.101.0/hugo_0.101.0_Linux-64bit.deb",
        "dpkg -i hugo_0.101.0_Linux-64bit.deb",
        "rm hugo_0.101.0_Linux-64bit.deb",
    ]
)

Stage0 += comment(f"--- End {filename} ---")
