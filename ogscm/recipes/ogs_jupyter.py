import os

from hpccm.primitives import comment, copy, environment, raw, shell
from hpccm.building_blocks import packages

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

parse_g.add_argument(
    "--pyvista-gpu",
    dest="pyvista_gpu",
    action="store_true",
    help="Enables PyVista with hardware rendering. (Requires NVidia GPU on the host with exactly the same driver version as the build machine)",
)

### SET arguments, e.g:

# Parse local args
local_args = parser.parse_known_args()[0]

if not "jupyter/" in local_args.runtime_base_image:
    print(
        "The ogs_jupyter.py recipe requires a Jupyter base image for the "
        "runtime stage! E.g. --runtime_base_image jupyter/base-notebook-ubuntu"
    )
    exit(1)

img_file += f"-jupyter"
out_dir += f"/jupyter"

# Implement recipe
Stage1 += comment(f"Begin {filename}")

Stage1 += packages(
    apt=["git", "libgl1-mesa-glx"]
)  # for pip packages via git, for gmsh conda package

conda_packages = []
for package in versions["python"]["jupyter_image"]["conda_packages"]:
    conda_packages.append(package)

pip_packages = pip_requirements

vtk_rendering_backend = "osmesa"
if local_args.pyvista_gpu:
    vtk_rendering_backend = "egl"
else:
    conda_packages.append("mesalib")
conda_packages.append(f"vtk=*={vtk_rendering_backend}*")

if "notebook_requirements" in versions["python"]:
    for package in versions["python"]["notebook_requirements"]:
        pip_packages.append(package)

pip_packages.sort()
conda_packages.sort()

Stage1 += shell(
    commands=[
        f"mamba install --yes --quiet -c bioconda -c conda-forge  {' '.join(conda_packages)}",
        "mamba clean --all -f -y",
        'fix-permissions "${CONDA_DIR}"',
        'fix-permissions "/home/${NB_USER}"',
    ]
)

# Install via shell (and not hpccm pip) to install into conda environment
Stage1 += shell(
    commands=[
        f"pip  --no-cache-dir install {' '.join(pip_packages)}",
        'fix-permissions "${CONDA_DIR}"',
        'fix-permissions "/home/${NB_USER}"',
    ]
)

lab_overrides = """\\n\
{\\n\
  "jupyterlab-gitlab:drive": {\\n\
    "baseUrl": "https://gitlab.opengeosys.org",\\n\
    "defaultRepo": "ogs/ogs"\\n\
  }\\n\
}\\n\
"""

# GitLab extension config, points to OGS GitLab and ogs/ogs as default repo
Stage1 += shell(
    commands=[
        "echo $'c.GitLabConfig.url = \"https://gitlab.opengeosys.org\"\\n' >> /etc/jupyter/jupyter_server_config.py",
        "mkdir -p /opt/conda/share/jupyter/lab/settings",
        f"echo $'{lab_overrides}' > /opt/conda/share/jupyter/lab/settings/overrides.json",
    ]
)

if local_args.pyvista_gpu:
    # NVidia driver
    Stage1 += packages(
        apt=[
            "kmod",
            "libglvnd-dev",
            "pkg-config",
            "libxrender1",
        ]
    )

    nv_driver_version = (
        os.popen("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
        .read()
        .strip()
    )

    Stage1 += shell(
        commands=[
            f"wget https://us.download.nvidia.com/XFree86/Linux-x86_64/{nv_driver_version}/NVIDIA-Linux-x86_64-{nv_driver_version}.run",
            f"sh NVIDIA-Linux-x86_64-{nv_driver_version}.run -s --no-kernel-module",
            f"rm NVIDIA-Linux-x86_64-{nv_driver_version}.run",
        ]
    )

Stage1 += comment(f"--- End {filename} ---")
