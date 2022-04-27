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
    "nbdime==3.1.1",
    "h5py==3.6.0",
    "jupyterlab-gitlab==3.0.0",
    "pyvista==0.34.0",
]
if local_args.pyvista_gpu:
    pip_packages.extend(
        [
            # vtk with offscreen (EGL) hardware rendering
            "https://github.com/pyvista/pyvista/releases/download/0.27.0/vtk-egl-9.0.1-cp39-cp39-manylinux2014_x86_64.whl",
            # for interactive PyVista
            "ipyvtklink",
        ]
    )
else:
    pip_packages.extend(
        [
            "pythreejs",  # only working rendering backend in this config
        ]
    )

for package in versions["python"]["notebook_requirements"]:
    pip_packages.append(package)
pip_packages.sort()

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
else:
    Stage1 += packages(
        apt=[
            "libfontconfig1",
            "libosmesa6-dev",
            "libxrender1",
        ]
    )
    Stage1 += environment(variables={"PYVISTA_JUPYTER_BACKEND": "pythreejs"})

Stage1 += comment(f"--- End {filename} ---")
