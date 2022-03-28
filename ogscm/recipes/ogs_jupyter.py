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

# VTUInterface (vtk) dependencies
Stage1 += packages(
    apt=[
        "libgl1-mesa-glx",
        "libxt6",
        "libglu1-mesa",
        "libsm6",
        "libxrender1",
        "libfontconfig1",
        "xvfb",  # for offscreen display server
        "git",  # for nbdime
    ]
)

pip_packages = [
    "pyvista==0.33.3",
    "pythreejs==2.3.0",
    "nbdime==3.1.1",
    "h5py==3.6.0",
    "jupyterlab-gitlab==3.0.0",
]
for package in versions["python"]["notebook_requirements"]:
    pip_packages.append(package)

Stage1 += shell(commands=[f"pip install {' '.join(pip_packages)}"])

# Setup adapted from https://github.com/pyvista/pyvista/blob/main/docker/Dockerfile
Stage1 += environment(
    variables={
        "DISPLAY": ":99.0",
        "PYVISTA_OFF_SCREEN": True,
        "PYVISTA_JUPYTER_BACKEND": "pythreejs",
        "JUPYTER_ENABLE_LAB": True,
    }
)

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

Stage1 += raw(
    docker='CMD /bin/bash -c "Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &" && sleep 2 && start-notebook.sh'
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

Stage1 += comment(f"--- End {filename} ---")
