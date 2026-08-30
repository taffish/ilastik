ilastik 1.4.2-r1

Purpose:
  Create/train biological-image projects in a browser-served desktop, then run
  workflow-compatible .ilp projects headlessly on new images.

Usage:
  taf-ilastik -- --version
  taf-ilastik -- --help
  taf-ilastik ilastik-gui --help
  taf-ilastik ilastik-models --help

Start the GUI with Docker:
  TAFFISH_DOCKER_RUN_ARGS="-p 127.0.0.1:8765:5801" \
  TAFFISH_CONTAINER_BACKEND=docker \
    taf-ilastik ilastik-gui --port 5801 --host-port 8765

Start the GUI with Podman:
  TAFFISH_PODMAN_RUN_ARGS="-p 127.0.0.1:8765:5801" \
  TAFFISH_CONTAINER_BACKEND=podman \
    taf-ilastik ilastik-gui --port 5801 --host-port 8765

Apptainer GUI syntax (not locally validated; no Apptainer/amd64 host available):
  TAFFISH_CONTAINER_BACKEND=apptainer \
    taf-ilastik ilastik-gui --bind-address 127.0.0.1 \
      --port 8765 --host-port 8765
  Apptainer shares the host network and has no -p mapping; use an unused port.
  On arm64, use the validated Docker amd64-emulation path instead.

GUI steps:
  1. Wait for "ilastik GUI is ready.", then open the printed host URL.
  2. Choose a workflow, load images, train/inspect, and save an .ilp project.
  3. Press Ctrl-C in the launching terminal to stop every GUI component.
  Open a project with: taf-ilastik ilastik-gui --project project.ilp ...
  For a path with spaces use --project '"project with spaces.ilp"'.
  Logs are printed before startup and live under /tmp for that session.

Remote GUI access:
  Keep the service on loopback and run locally:
    ssh -N -L 8765:127.0.0.1:8765 user@server
  Then open the printed URL. noVNC is not TLS; protect sensitive projects.

Run a trained pixel-classification project headlessly:
  taf-ilastik -- --headless --readonly=1 --project=trained.ilp \
    --output_format=hdf5 \
    --output_filename_format='{dataset_dir}/{nickname}_prediction.h5' \
    --raw_data input.tif
  Batch options and input roles are stored-workflow specific. Carving has no
  upstream headless path. Use writable output/work directories.

Prepare one fixed BioImage.IO model for personal reuse:
  ROOT="$HOME/.local/share/taffish/models/ilastik"
  mkdir -p "$ROOT/imports"
  Place an independently obtained exact MODEL.zip in ROOT/imports.
  Set SHA to its independently verified 64-character SHA-256 and SOURCE to its
  versioned HTTPS URL or doi: identifier; review the model-specific license.
  TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT" \
    taf-ilastik ilastik-models --model-id MODEL \
      --archive /model-install/imports/MODEL.zip --source "$SOURCE" \
      --sha256 "$SHA" --dry-run
  TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT" \
    taf-ilastik ilastik-models --model-id MODEL \
      --archive /model-install/imports/MODEL.zip --source "$SOURCE" \
      --sha256 "$SHA" --confirm-authorized-local-import

Reuse and verify prepared models:
  Auto-discovery mounts personal, /usr/local, then /opt roots read-only at
  /models/ilastik. In the GUI select /models/ilastik/MODEL/model.zip.
  taf-ilastik ilastik-models --verify-only --model-root /models/ilastik
  Override with TAFFISH_ILASTIK_MODEL_PATH; disable with
  TAFFISH_ILASTIK_MODEL_AUTO_MOUNT=0. Host resource paths cannot contain spaces.
  A site administrator may run the same import once under /usr/local/share,
  then make it root-owned and read-only; ordinary users need only read access.
  Import performs no download and records source, SHA-256, size and RDF license.

Inputs and outputs:
  Inputs: workflow-specific images/labels, .ilp projects and optional model ZIPs.
  Common local formats include HDF5, TIFF, PNG, NumPy arrays and image stacks.
  Outputs include probability maps, labels, segmentations, tracking/object
  tables and HDF5/TIFF/PNG/OME-Zarr exports. Remote S3/Zarr needs credentials.

Runtime boundaries:
  Native image support is linux/amd64 only; Docker/Podman request emulation on
  arm64. This is the CPU bundle. CUDA, remote TikTorch and commercial
  Gurobi/CPLEX services/licenses are not configured. LAZYFLOW_THREADS and
  LAZYFLOW_TOTAL_RAM_MB tune workers/RAM; RAM values below 500 MiB are rejected.

More documentation: https://github.com/taffish/ilastik
