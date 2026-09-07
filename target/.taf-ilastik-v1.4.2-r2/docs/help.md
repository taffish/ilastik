ilastik 1.4.2-r2

Purpose:
  Create image-analysis projects in the browser desktop, then apply compatible
  saved .ilp projects headlessly. Choose CLI or GUI below.

Usage:
  taf-ilastik -- --version
  taf-ilastik -- --help
  taf-ilastik ilastik-gui --help
  taf-ilastik ilastik-models --help

GUI with Docker:
  TAFFISH_DOCKER_RUN_ARGS="-p 127.0.0.1:8765:5801" \
  TAFFISH_CONTAINER_BACKEND=docker \
    taf-ilastik ilastik-gui --port 5801 --host-port 8765

GUI with Podman:
  TAFFISH_PODMAN_RUN_ARGS="-p 127.0.0.1:8765:5801" \
  TAFFISH_CONTAINER_BACKEND=podman \
    taf-ilastik ilastik-gui --port 5801 --host-port 8765

GUI with Apptainer (native amd64 Linux):
  TAFFISH_CONTAINER_BACKEND=apptainer \
    taf-ilastik ilastik-gui --bind-address 127.0.0.1 \
      --port 8765 --host-port 8765
  Apptainer shares host networking: no -p; select unused HTTP/VNC/display ports.

GUI tasks:
  Wait for "ilastik GUI is ready.", open the printed URL, select a workflow,
  load images and save the project. Ctrl-C stops the session; logs are under
  the /tmp directory printed before startup.
  Open an existing project with --project project.ilp.
  For spaces, pass literal inner quotes: --project '"project with spaces.ilp"'.
  --geometry 1440x900 sizes the desktop; browser scaling does not resize it.
  Keep access on loopback; from another computer use:
    ssh -N -L 8765:127.0.0.1:8765 user@server
  noVNC is not TLS. Do not expose sensitive projects publicly.

Headless batch (requires a trained pixel-classification .ilp):
  taf-ilastik -- --headless --readonly=1 --project=trained.ilp \
    --output_format=hdf5 \
    --output_filename_format='{dataset_dir}/{nickname}_prediction.h5' \
    --raw_data input.tif
  Input roles/options depend on the saved workflow. Carving has no headless
  path. Projects and exports need writable work/output directories.

Prepare one explicitly selected model:
  Set URL, SHA, BYTES and LICENSE from that fixed ZIP's publisher record.
  Review its terms for personal/site sharing. Missing trusted metadata:
  obtain and verify the ZIP independently, then use --archive (see helper help).
  ROOT="$HOME/.local/share/taffish/models/ilastik"
  mkdir -p "$ROOT"
  export TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT"
  export TAFFISH_CONTAINER_BACKEND=podman
  Use docker or apptainer instead to select either other backend.
  taf-ilastik ilastik-models --model-id MODEL --url "$URL" \
    --sha256 "$SHA" --archive-bytes "$BYTES" --expected-license "$LICENSE" --dry-run
  Repeat with --confirm-authorized-download instead of --dry-run to install.
  No automatic model choice or whole-library download. /tmp installs are temporary.

Reuse prepared models read-only (root includes the 1.4.2 child):
  unset TAFFISH_ILASTIK_MODEL_INSTALL_ROOT
  export TAFFISH_ILASTIK_MODEL_PATH="$ROOT/1.4.2"
  TAFFISH_CONTAINER_BACKEND=docker taf-ilastik ilastik-models --verify-only
  TAFFISH_CONTAINER_BACKEND=podman taf-ilastik ilastik-models --verify-only
  TAFFISH_CONTAINER_BACKEND=apptainer taf-ilastik ilastik-models --verify-only
  Select /models/ilastik/MODEL/model.zip in the GUI; no download is needed.
  Auto-discovery checks personal, /usr/local/share and /opt/taffish roots.
  TAFFISH_ILASTIK_MODEL_PATH overrides; TAFFISH_ILASTIK_MODEL_AUTO_MOUNT=0 disables.
  Host resource paths cannot contain whitespace, comma, colon or glob characters.
  For explicit manual binds, disable auto-mount and use:
    Docker: TAFFISH_DOCKER_RUN_ARGS="-v $ROOT/1.4.2:/models/ilastik:ro"
    Podman: TAFFISH_PODMAN_RUN_ARGS="-v $ROOT/1.4.2:/models/ilastik:ro"
    Apptainer: TAFFISH_APPTAINER_RUN_ARGS="--bind $ROOT/1.4.2:/models/ilastik:ro"
  Prefix the corresponding verify/GUI wrapper command with that variable.

Inputs, outputs and limits:
  Inputs: images/labels, .ilp projects, optional fixed model ZIPs. Outputs:
  probability maps, labels, tables and HDF5/TIFF/PNG/OME-Zarr exports.
  Native image: amd64 only. Docker/Podman on arm64 need host amd64 emulation.
  CPU bundle only; CUDA, external TikTorch and licensed Gurobi/CPLEX are not set up.
  LAZYFLOW_THREADS and LAZYFLOW_TOTAL_RAM_MB tune workers/RAM (minimum 500 MiB).
  Remote S3/Zarr or GUI model DOI/nickname loading explicitly needs network.

Wrapper options:
  taf-ilastik --help       This manual.
  taf-ilastik --version    Package identity.
  taf-ilastik --compile    Generated shell.
More documentation: https://github.com/taffish/ilastik
