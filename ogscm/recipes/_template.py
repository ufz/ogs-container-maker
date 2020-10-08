# Recipe template
# Have a look and change statements with ### SET comment

### SET imports
from hpccm.building_blocks import xx

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:
parse_g.add_argument("--my_arg", type=str, default="default_value")

# Parse local args
local_args = parser.parse_known_args()[0]

### SET image file name, e.g.:
img_file = f"someName-{local_args.my_arg}"

### Optionally SET out_dir, e.g.:
out_dir = f"{local_args.out}/{local_args.format}/someName/{local_args.my_arg}"

# Implement recipe
Stage0 += xx(arg="value")
