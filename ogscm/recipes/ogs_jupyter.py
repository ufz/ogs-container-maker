from hpccm.primitives import comment, raw, shell
from hpccm.building_blocks import packages

if not parser.parse_args().runtime_base_image.startswith("jupyter/"):
    print(
        "The ogs_jupyter.py recipe requires a Jupyter base image for the "
        "runtime stage! E.g. --runtime_base_image jupyter/base-notebook"
    )
    exit(1)

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:
# parse_g.add_argument("--my_arg", type=str, default="default_value")

# Parse local args
local_args = parser.parse_known_args()[0]

img_file += f"-jupyter"
out_dir += f"/jupyter"

# Implement recipe
Stage1 += comment(f"Begin {filename}")

# VTUInterface (vtk) dependencies
Stage1 += packages(
    apt=[
        "libgl1-mesa-glx",
        "libxt6",
        "libglu1-mesa",
        "libsm6",
        "libxrender1",
        "libfontconfig1",
    ]
)

Stage1 += shell(
    commands=[
        "pip install ogs6py "
        "https://github.com/joergbuchwald/VTUinterface/archive/refs/heads/master.zip"
    ]
)

Stage1 += shell(
    commands=[
        'fix-permissions "${CONDA_DIR}"',
        'fix-permissions "/home/${NB_USER}"',
    ]
)

Stage1 += comment(f"--- End {filename} ---")
