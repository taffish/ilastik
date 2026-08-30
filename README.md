# ilastik

`ilastik` packages the official ilastik 1.4.2 regular Linux distribution for
TAFFISH, including its interactive desktop, headless batch mode, local CPU
TikTorch/BioImage.io support, image readers and exporters.

Package identity:

- name: `ilastik`
- command: `taf-ilastik`
- kind: `tool`
- version: `1.4.2-r1`
- container: `ghcr.io/taffish/ilastik:1.4.2-r1`
- native platform: `linux/amd64`
- upstream tag/runtime version: `1.4.2`
- TAFFISH packaging license: Apache-2.0
- upstream: <https://github.com/ilastik/ilastik>

## What This App Packages

ilastik provides interactive machine-learning workflows for biological image
analysis. A common project starts in the GUI: load image data, choose features,
paint sparse labels, inspect predictions and save an `.ilp` project. The same
trained project can then be applied reproducibly to new images with the
headless CLI.

The image is based on the checksummed 681,505,433-byte official
`ilastik-1.4.2-Linux.tar.bz2` CPU bundle. The app adds a signal-safe launcher
and a supervised noVNC desktop helper; it does not rebuild or replace ilastik's
Python/Conda runtime.

## Scope

The official bundle exposes workflows for:

- pixel classification, autocontext, counting and object classification;
- boundary-based segmentation/multicut and carving;
- manual and automated tracking variants;
- neural-network classification and trainable domain adaptation;
- label/prediction viewing, data conversion and other bundled workflows;
- HDF5, TIFF/PNG and NumPy data, with bundled OME-Zarr/S3 readers and exporters.

All workflows except Carving have an upstream headless execution path. Exact
batch options depend on the workflow stored in the `.ilp` project; consult
upstream workflow documentation rather than reusing options from another
workflow.

## Container Commands

- `ilastik`: upstream CLI with the official environment cleanup and direct
  signal delivery to its Python process;
- `ilastik-gui`: supervised Xvfb + `twm` + x11vnc + noVNC desktop session;
- `ilastik-models`: selected-member local BioImage.IO ZIP importer and prepared
  root verifier; it performs no network download;
- `python`: the bundled Python 3.11 runtime, available through command mode for
  inspection and supported ilastik Python APIs;
- `ilastik-smoke`: packaging self-test used by the Hub/index contract.

The launcher is necessary because upstream `run_ilastik.sh` starts Python as a
child process. The TAFFISH launcher mirrors its environment settings but uses
`exec`, so INT/TERM reach the actual ilastik process.

## Install and Inspect

```sh
taf install ilastik
taf-ilastik --version
taf-ilastik -- --version
taf-ilastik -- --help
```

`taf-ilastik --help` is the TAFFISH terminal manual. `taf-ilastik -- --help`
passes `--help` to the default upstream command.

For an unpublished local candidate, build the real wrapper before testing a
long-running GUI session:

```sh
taf build
TAFFISH_DOCKER_RUN_ARGS="-p 127.0.0.1:8765:5801" \
TAFFISH_CONTAINER_BACKEND=docker \
target/taf-ilastik-v1.4.2-r1 ilastik-gui --port 5801 --host-port 8765
```

This exercises the same installed-wrapper semantics used after publication;
`docs/help.md` intentionally contains only the installed `taf-ilastik` form.

## GUI: Create and Train a Project

Docker example with different host/container ports:

```sh
TAFFISH_DOCKER_RUN_ARGS="-p 127.0.0.1:8765:5801" \
TAFFISH_CONTAINER_BACKEND=docker \
taf-ilastik ilastik-gui --port 5801 --host-port 8765
```

Wait for `ilastik GUI is ready.`, then open the printed URL. Choose a workflow,
load data, train/inspect it and save an `.ilp` project. Open an existing project
directly with:

```sh
TAFFISH_DOCKER_RUN_ARGS="-p 127.0.0.1:8765:5801" \
TAFFISH_CONTAINER_BACKEND=docker \
taf-ilastik ilastik-gui --port 5801 --host-port 8765 \
  --project project.ilp
```

TAFFISH command mode preserves a path containing spaces when the argument
contains literal inner quotes. For example:

```sh
taf-ilastik ilastik-gui --project '"project with spaces.ilp"' \
  --port 5801 --host-port 8765
```

The helper prints the host URL, an SSH tunnel example, log directory and stop
instruction before starting any long-running process. Readiness requires Xvfb,
the window manager, x11vnc, noVNC and the main ilastik window to all be alive;
those components remain supervised after readiness. Ctrl-C stops the complete
session.

The default virtual desktop is `1440x900`; the ilastik workbench is fitted with
a 48-pixel top safe area. `--geometry WxH` changes the virtual desktop and
`--no-fit-window` retains upstream native window sizing. noVNC
`resize=scale` scales the remote canvas to the browser and may create narrow
letterboxing when aspect ratios differ; it does not itself resize ilastik.

For a remote host, keep Docker/Podman bound to loopback and tunnel the printed
host port:

```sh
ssh -N -L 8765:127.0.0.1:8765 user@server
```

The helper is plain HTTP/noVNC unless `--password` is used for VNC access; it
does not provide TLS. A password can appear in shell history or the process
list, so a loopback bind plus SSH or a protected reverse proxy remains the
recommended boundary. Projects may expose image-derived data, file paths and
sample metadata.

Podman uses its own runtime environment variable:

```sh
TAFFISH_PODMAN_RUN_ARGS="-p 127.0.0.1:8765:5801" \
TAFFISH_CONTAINER_BACKEND=podman \
taf-ilastik ilastik-gui --port 5801 --host-port 8765
```

Apptainer shares the host network namespace and has no Docker-style `-p`:

```sh
TAFFISH_CONTAINER_BACKEND=apptainer \
taf-ilastik ilastik-gui --bind-address 127.0.0.1 \
  --port 8765 --host-port 8765
```

The Podman syntax is documented but was not runtime-validated because the local
Podman machine was unavailable. The Apptainer syntax is also not locally
validated because neither Apptainer nor an amd64 Linux host was available.
Apptainer needs an unused host port and site firewall permission; on an arm64
host, use the validated Docker amd64-emulation path instead.

## Headless Batch Processing

First create, train and save a compatible `.ilp` project in the GUI. A typical
pixel-classification batch call is:

```sh
taf-ilastik -- --headless --readonly=1 \
  --project=trained.ilp \
  --output_format=hdf5 \
  --output_filename_format='{dataset_dir}/{nickname}_prediction.h5' \
  --raw_data input.tif
```

Option names such as `--raw_data`, `--probabilities`, `--export_source`, output
axis order and filename placeholders are workflow-specific. Use absolute paths
when a project must remain portable across working directories.

Command mode can invoke the explicit packaged command:

```sh
taf-ilastik ilastik --version
taf-ilastik python -c '"import ilastik; print(ilastik.__version__)"'
```

## Inputs and Outputs

Inputs include `.ilp` projects plus workflow-appropriate image/label data.
Common local formats include HDF5/H5, TIFF, PNG, NumPy arrays and image stacks.
OME-Zarr, S3 and REST-backed sources are available through the bundled readers
but require network/credentials when the source is remote.

Outputs depend on the workflow and export settings: probability maps,
segmentations, labels, object/tracking tables, HDF5/TIFF/PNG sequences and
OME-Zarr stores are typical. ilastik will not invent a trained model from raw
images during headless execution; the project must contain the required
training state.

## Threads and Memory

The upstream variables `LAZYFLOW_THREADS` and `LAZYFLOW_TOTAL_RAM_MB` control
the lazyflow thread pool and RAM budget. `LAZYFLOW_TOTAL_RAM_MB` is in MiB and
values below 500 are rejected. Container CPU and memory limits still apply.

## BioImage.io Models and Prepared Roots

Neural-network workflows accept a local BioImage.IO model ZIP or resolve a DOI
or nickname online. A DOI/nickname entered in the GUI is an explicit network
action; its resolver/catalog can evolve and the resulting cache is only
session-local under `/tmp`. Normal startup, non-neural workflows and Hub smoke
do not contact BioImage.IO.

For reproducible reuse, independently obtain one exact model ZIP, verify its
published SHA-256 and model-specific license, then import that selected member.
The helper never downloads a model and never chooses one for the user:

```sh
MODEL=my-fixed-model
ROOT="$HOME/.local/share/taffish/models/ilastik"
mkdir -p "$ROOT/imports"
# Independently place the exact archive at "$ROOT/imports/$MODEL.zip".
SHA=REPLACE_WITH_INDEPENDENTLY_VERIFIED_64_HEX_SHA256
SOURCE=https://versioned.example/model.zip

TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT" \
taf-ilastik ilastik-models --model-id "$MODEL" \
  --archive "/model-install/imports/$MODEL.zip" --source "$SOURCE" \
  --sha256 "$SHA" --dry-run

TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT" \
taf-ilastik ilastik-models --model-id "$MODEL" \
  --archive "/model-install/imports/$MODEL.zip" --source "$SOURCE" \
  --sha256 "$SHA" --confirm-authorized-local-import
```

The import checks ZIP path safety, exact archive SHA-256, BioImage.IO schema and
local package I/O, supported weights and ilastik's broad input/output
compatibility. It uses a non-blocking lock, same-filesystem staging, atomic
promotion and rollback, then writes per-member and root-level manifests,
inventory and ready markers. `--force` replaces an already complete member;
an untrusted incomplete root is rejected rather than silently repaired.

Prepared roots live at `.../models/ilastik/1.4.2`. Normal discovery order is:

1. `TAFFISH_ILASTIK_MODEL_PATH`;
2. `~/.local/share/taffish/models/ilastik/1.4.2`;
3. `/usr/local/share/taffish/models/ilastik/1.4.2`;
4. `/opt/taffish/models/ilastik/1.4.2`.

The wrapper requires positive inventory/readiness metadata, resolves the host
path, mounts it read-only at `/models/ilastik`, and runs an internal metadata
check before starting ilastik. In the GUI, explicitly select
`/models/ilastik/MODEL/model.zip`; auto-mount never makes the scientific model
choice. Deep verification recomputes archive hashes:

```sh
taf-ilastik ilastik-models --verify-only --model-root /models/ilastik
taf-ilastik ilastik-models --inventory --model-root /models/ilastik
```

Set `TAFFISH_ILASTIK_MODEL_AUTO_MOUNT=0` to disable discovery. Host resource
paths with whitespace, comma, colon or glob characters are rejected because
the backend argument boundary cannot represent them safely. A manual read-only
bind to `/models/ilastik` remains the backend fallback.

For site reuse, an administrator can use
`ROOT=/usr/local/share/taffish/models/ilastik`, perform the same import, then
make directories `0755`, files `0644`, and remove ordinary-user write access.
Ordinary users then need no network or write permission. Site installation was
not performed in this release environment, so root-once ownership is a
documented contract rather than a production-site receipt. Each model has its
own RDF license; the confirmation flag records caller responsibility to verify
that personal or site sharing is permitted.

## Platform, GPU and External Services

The official regular Linux 1.4.2 bundle is x86_64-only, so the native image is
`linux/amd64`. `src/main.taf` automatically requests `--platform linux/amd64`
for Docker/Podman; an arm64 host therefore uses amd64 emulation, not native
arm64. Apptainer requires an amd64-compatible execution environment.

The installed software tree is treated as read-only. The launcher creates one
mode-`0700` runtime root below `/tmp` and places HOME, XDG cache/config/data and
runtime state, Matplotlib/Numba caches and the session BioImage.IO cache there.
The GUI helper uses the same session log/runtime tree. Persistent project and
export files must use the wrapper's writable work directory; prepared models
use the explicit read-only bind described above. This write map was exercised
with a Docker read-only root filesystem as an Apptainer-SIF proxy, but native
Apptainer execution remains unvalidated in this environment.

This app intentionally packages the official CPU bundle. The separate upstream
GPU archive is several gigabytes larger, requires CUDA 12.6-compatible host
drivers/devices and carries additional CUDA terms; it belongs in a separately
validated GPU app rather than silently bloating this default image. Remote
TikTorch servers are supported by upstream arguments but are external services,
not started or authenticated by TAFFISH.

Structured/learning tracking paths that require Gurobi or IBM CPLEX remain
subject to those commercial products' installation, license-server and
architecture requirements. The app does not bundle or bypass those licenses.
CPU workflows that do not select those solvers remain available.

The official archive's Python package metadata reports NumPy 2 requirements
for its bundled `imagecodecs 2026.3.6` and `elf 0.8.1`, while the same official
environment pins NumPy 1.26.4. TAFFISH does not rewrite that upstream-resolved
environment or recommend an in-place NumPy upgrade. The packaging smoke instead
executes an image-codec round trip and an ELF watershed, and also exercises the
Numba TBB backend whose `libtbb.so.12` runtime is supplied by this image.

Upstream documentation/file-opening menu actions use desktop URL handlers. The
remote desktop includes `xdg-open` integration but no full web browser or file
manager; open web documentation in the host browser and use mounted project
paths for files.

## Testing Boundary

The packaging smoke contract independently checks exact runtime identity,
headless/GUI modules, Astropy/pyshtools and representative workflow
registration, the imagecodecs/ELF/Numba-TBB runtime closure, a tiny real Data
Conversion export, the model-helper contract, a tiny valid BioImage.IO package
import, manifest/inventory, idempotency, shared-readable permissions and
corruption rejection, plus a real-project noVNC session, starting-before-ready
ordering, geometry, TERM cleanup, startup interruption and window-manager
failure before and after readiness. Every index test is independent and
designed for a fresh offline container.

Smoke does not prove scientific accuracy on production microscopy data, train a
classifier, download or execute a production model, prove any particular model
license allows site sharing, exercise remote S3/TikTorch, use a GPU, or validate
commercial solvers. Those are extended, resource-, dataset- and
infrastructure-specific acceptance steps.

## License and Citation

The TAFFISH packaging files are Apache-2.0. ilastik is GPL-2.0-or-later with
its applet/workflow/plugin linking exception; lazyflow is LGPL-2.1-or-later.
The official environment contains many third-party packages under their own
terms. External BioImage.IO ZIPs retain their own RDF-declared licenses; no
model is redistributed by this app. Upstream license text and the exact
environment manifest remain in the image.

Please cite:

> Berg S, et al. ilastik: interactive machine learning for (bio)image
> analysis. *Nature Methods* (2019). <https://doi.org/10.1038/s41592-019-0582-9>

Upstream documentation: <https://www.ilastik.org/documentation/>
