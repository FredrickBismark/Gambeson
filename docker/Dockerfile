# Headless FreeCAD + solver environment for the Gambeson simulation pipeline
#
# Build: docker build -t gambeson-sim docker/
# Run:   docker run -v $(pwd):/workspace gambeson-sim python -m src.pipeline.orchestrator

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    wget \
    gmsh \
    calculix-ccx \
    elmer \
    elmerfem-csc \
    openscad \
    openradioss \
    libocct-modeling-algorithms-dev \
    libocct-data-exchange-dev \
    && rm -rf /var/lib/apt/lists/*

# Python environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml /tmp/pyproject.toml
RUN pip install --no-cache-dir pyyaml numpy meshio gmsh pyelmer pyvista cadquery solidpython2

WORKDIR /workspace

# Default: run the pipeline orchestrator
CMD ["python", "-m", "src.pipeline.orchestrator", "--help"]
