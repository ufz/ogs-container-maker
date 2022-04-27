import os

from hpccm.primitives import comment, copy, environment, raw, shell
from hpccm.building_blocks import packages

print(f"Evaluating {filename}")

# Add cli arguments to args_parser
parse_g = parser.add_argument_group(filename)

### SET arguments, e.g:

# Parse local args
local_args = parser.parse_known_args()[0]

if not local_args.runtime_base_image.startswith("jupyter/"):
    print(
        "The ogs_jupyter.py recipe requires a Jupyter base image for the "
        "runtime stage! E.g. --runtime_base_image jupyter/base-notebook"
    )
    exit(1)

img_file += f"-jupyter"
out_dir += f"/jupyter"

# Implement recipe
Stage1 += comment(f"Begin {filename}")

Stage1 += packages(apt=["git"])  # for pip packages via git

pip_packages = [
    "https://github.com/pyvista/pyvista/releases/download/0.27.0/vtk-egl-9.0.1-cp39-cp39-manylinux2014_x86_64.whl",  # vtk with offscreen (EGL) hardware rendering
    "ipyvtklink",  # for interactive PyVista
    "pyvista==0.34.0",
    "nbdime==3.1.1",
    "h5py==3.6.0",
    "jupyterlab-gitlab==3.0.0",
]
for package in versions["python"]["notebook_requirements"]:
    pip_packages.append(package)

# Install via shell (and not hpccm pip) to install into conda environment
Stage1 += shell(commands=[f"pip  --no-cache-dir install {' '.join(pip_packages)}"])

Stage1 += shell(
    commands=[
        # Install snakemake in conda 'base' environment
        "mamba install --yes --quiet -c bioconda -c conda-forge snakemake-minimal",
    ]
)

Stage1 += shell(
    commands=[
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
