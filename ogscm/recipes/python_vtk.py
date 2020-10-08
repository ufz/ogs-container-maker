from hpccm.building_blocks import pip
from hpccm.primitives import comment

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)
parse_g.add_argument("--vtk_version", type=str, default="8.1.2")

# Parse local args
local_args = parser.parse_known_args()[0]

# set image file name
img_file = f"vtk-{local_args.vtk_version}"

# Optionally set out_dir
out_dir = f"{local_args.out}/{local_args.format}/vtk/{local_args.vtk_version}"

# Implement recipe
Stage0 += comment(f"Begin {filename}")

Stage0 += pip(pip="pip3", packages=[f"vtk=={local_args.vtk_version}"])

Stage0 += comment(f"--- End {filename} ---")
