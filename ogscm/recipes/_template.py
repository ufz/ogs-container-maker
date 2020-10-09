# Recipe template
# Have a look and change statements with ### SET comment

### SET imports
from hpccm.primitives import comment
from hpccm.building_blocks import xx

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:
parse_g.add_argument("--my_arg", type=str, default="default_value")

# Parse local args
local_args = parser.parse_known_args()[0]

### SET append to image file name, e.g.:
img_file += f"-someName-{local_args.my_arg}"

### SET Append to out_dir, e.g.:
out_dir += f"/someName/{local_args.my_arg}"

# Implement recipe
Stage0 += comment(f"Begin {filename}")

Stage0 += xx(arg="value")

Stage0 += comment(f"--- End {filename} ---")
