# ilastik

`ilastik` packages the official ilastik 1.4.2 regular Linux distribution for
TAFFISH, including its interactive desktop, headless batch mode, local CPU
TikTorch/BioImage.io support, image readers and exporters.

Package identity:

- name: `ilastik`
- command: `taf-ilastik`
- kind: `tool`
- version: `1.4.2-r2`
- container: `ghcr.io/taffish/ilastik:1.4.2-r2`
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

The fixed upstream `ilastik-core` packaging metadata has no GUI extra or console
entry-point split; the desktop comes with the official regular bundle. The
official [Fiji companion plugin](https://www.ilastik.org/documentation/fiji_export/plugin)
is a separate Java/Fiji integration, not another hidden ilastik Qt desktop. It is
not bundled or validated here: install it through Fiji's ilastik update site in
an independently managed Fiji environment, or exchange HDF5 files with this app.
This boundary does not remove the main desktop, image conversion or headless CLI.

## Container Commands

- `ilastik`: upstream CLI with the official environment cleanup and direct
  signal delivery to its Python process;
- `ilastik-gui`: supervised Xvfb + `twm` + x11vnc + noVNC desktop session;
- `ilastik-models`: selected-member local BioImage.IO ZIP importer and prepared
  root verifier, with an explicit pinned HTTPS ZIP download option;
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
target/taf-ilastik-v1.4.2-r2 ilastik-gui --port 5801 --host-port 8765
```

This exercises the same installed-wrapper semantics used after publication;
`docs/help.md` intentionally contains only the installed `taf-ilastik` form.
Short-running Data Conversion was also validated with `taf run -b docker`,
`-b podman` and `-b apptainer`. Keep its inputs and outputs inside the source
working directory, or provide explicit backend binds; a neighboring host
directory is not automatically mounted by Docker/Podman.

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
the window manager, x11vnc, noVNC and the main ilastik window to all be alive,
plus HTTP and a real RFB 3.8 handshake (including framebuffer size without a
password, or the authentication challenge for password-protected sessions);
those components remain supervised after readiness. Ctrl-C stops the complete
session (INT 130, TERM 143). D-Bus/application and noVNC descendants are in
owned isolated process groups; cleanup ignores repeated signals during its
bounded grace period. This is an attached foreground-session contract, not a
promise that killing only a generic launcher shell PID implements service-manager
shutdown. Long-running `taf run` is not the recommended interface; use the real
built/installed wrapper shown above.

In the current TAFFISH 0.11.0 Apptainer developer-mode audit, `taf run` did not
deliver startup output live; the text became visible only after the test's
120-second Ctrl-C deadline, and the outer CLI exited 1. This is a developer
CLI/core boundary, not an ilastik helper fix. The same candidate's built wrapper
delivers live starting/ready messages and passes startup/ready Ctrl-C and TERM.

The x11vnc child alone has its soft open-file limit capped at the lower of its
inherited value and 1024. Some hosts supply extremely large limits that stall
x11vnc before its RFB greeting; the helper leaves the hard limit, ilastik process
and host configuration unchanged. Existing X display sockets/locks are rejected.
After its own Xvfb has exited, the helper removes leftover endpoints only when
their recorded device/inode and lock PID still match; it never clears another
session's display to make startup succeed.

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

Apptainer needs unused HTTP/VNC ports and display numbers on the host, and site
firewall permission. It does not support native arm64 with this amd64-only
bundle. Docker/Podman on arm64 require host-provided amd64 emulation; this does
not count as native arm64 support. Current-release validation is recorded below.

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
The [upstream installation guide](https://www.ilastik.org/documentation/basics/installation)
recommends at least 8 GB RAM; large 3-D projects may need substantially more.

## BioImage.io Models and Prepared Roots

Neural-network workflows accept a local BioImage.IO model ZIP or resolve a DOI
or nickname online. A DOI/nickname entered in the GUI is an explicit network
action; its resolver/catalog can evolve and the resulting cache is only
session-local under `/tmp`. Normal startup, non-neural workflows and Hub smoke
do not contact BioImage.IO.

Models are a selectable family, not one app-versioned database. The reusable
unit is one self-contained ZIP, explicit local model ID and exact SHA-256;
RDF version/license and source are recorded separately. The remote catalog
evolves independently of ilastik and this app does not resolve floating aliases,
choose a scientific model, or download the whole catalog. User-trained
`.ilp` projects and input images are project-specific inputs, not shared model
downloads.

For an exact publisher-provided HTTPS ZIP, set `URL`, `SHA`, `BYTES` and
`MODEL_LICENSE` from its versioned record, review its terms, and use:

```sh
ROOT="$HOME/.local/share/taffish/models/ilastik"
mkdir -p "$ROOT"
TAFFISH_ILASTIK_MODEL_INSTALL_ROOT="$ROOT" \
TAFFISH_CONTAINER_BACKEND=podman \
taf-ilastik ilastik-models --model-id MODEL --url "$URL" \
  --sha256 "$SHA" --archive-bytes "$BYTES" --expected-license "$MODEL_LICENSE" \
  --dry-run
```

Replace `--dry-run` with `--confirm-authorized-download` to download/install.
Use `TAFFISH_CONTAINER_BACKEND=docker` or `apptainer` for the corresponding
backend; the wrapper supplies the writable install bind in all three cases.
Dry-run prints identity, size, license, scope and destination without making a
network request. Download requires explicit confirmation, HTTPS redirects only,
a checksum/size-keyed cache, one installer lock, bounded curl retries and Range
resume. The disk preflight reserves download plus installed-copy size and 64 MiB.
A server that refuses Range resume fails visibly and retains the exact partial;
inspect/remove only that named partial to restart. Cache corruption fails closed,
including with `--force`; a completed verified cache is reused without network.
RDF license must match the expected license before installation.

Only self-contained, ilastik-compatible TorchScript/PyTorch ZIPs are accepted.
A DOI/nickname is not a fixed ZIP URL. If a publisher provides no stable ZIP,
trusted archive hash, size or reusable license, no automated catalog claim is
made: obtain/verify the package through its official interface and use the
offline local-import path below. A locally computed hash fixes supplied bytes
but is not independent publisher-authenticity evidence. Archive-specific license
review remains necessary: the software license never grants model-sharing rights.

Local import is still available and performs no network download:

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
choice. The v1 prepared-root schema and upstream version determine compatibility:
r1-prepared 1.4.2 roots remain reusable in r2 without altering their provenance.
Deep verification recomputes archive hashes:

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
Ordinary users then need no network or write permission. Full production/site installation is not validated. Synthetic prepared roots
exercise the installation and ordinary-user read-only reuse mechanism; this is
not a production multi-user site receipt. Each model has its
own RDF license; the confirmation flag records caller responsibility to verify
that personal or site sharing is permitted.

## Platform, GPU and External Services

The official regular Linux 1.4.2 bundle is x86_64-only, so the native image is
`linux/amd64`. `src/main.taf` automatically requests `--platform linux/amd64`
for Docker/Podman; an arm64 host therefore uses amd64 emulation, not native
arm64. Apptainer requires an amd64-compatible execution environment.

The current native candidate is 2,551,703,475 bytes (about 2.38 GiB unpacked OCI
image accounting); its SIF is 786,702,336 bytes. The official runtime occupies
about 2.2 GiB, mainly shared libraries and Python packages. Download/apt caches,
bytecode and non-runtime tests are removed before the final image; there is no
bundled package cache, large headers or sysroot left to remove. Fonts, Qt plugins,
translations, workflow modules, licensing and runtime data remain available.

The installed software tree is treated as read-only. The launcher creates one
mode-`0700` runtime root below `/tmp` and places HOME, XDG cache/config/data and
runtime state, Matplotlib/Numba caches and the session BioImage.IO cache there.
The GUI helper atomically creates a unique mode-`0700` log root before starting
any child, even under a permissive caller umask; its runtime subdirectories are
also private. It does not change the caller's umask or follow an old predictable
PID-based log path. Persistent project and
export files must use the wrapper's writable work directory; prepared models
use the explicit read-only bind described above. Direct smoke uses only its unique writable scratch and never writes
`/model-install` without an actual bind. Persistent installation is tested
separately through the real wrapper. The model validator creates its own private
temporary HOME/cache because importing ilastik can create `.ilastikrc`.
Explicit `--model-root /tmp/...` is disposable scratch; it is not a persistent
installation. Mount markers are not accepted as proof of a production bind.

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

## Backend Usage and Capability Matrix

Validation rows below describe the corrected r2 candidate. An intermediate
candidate failed final cleanup after a very early interrupt; that failure was
retained, the ownership-capture window was repaired, and every gate was rerun.

| Capability | Docker | Podman | Apptainer |
| --- | --- | --- | --- |
| Native image | linux/amd64 | linux/amd64 | linux/amd64 |
| CLI / headless | normal wrapper | normal wrapper | normal wrapper + read-only SIF |
| GUI networking | loopback host mapping | loopback host mapping | explicit loopback bind, no -p |
| Model installation | actual rw /model-install bind | actual rw /model-install bind | actual rw /model-install bind |
| Prepared-model reuse | actual ro /models/ilastik bind | actual ro /models/ilastik bind | actual ro /models/ilastik bind |
| Current r2 direct offline smoke | 28 normal + 28 read-only PASS | 28 normal + 28 read-only PASS | 28 actual SIF PASS |
| Current r2 wrapper / GUI | 20 wrapper + 5 PTY PASS; browser menu/export PASS | 20 wrapper + 5 PTY PASS; browser menu/export PASS | 20 wrapper + 5 PTY PASS; browser menu/export PASS |

Each backend repeated startup Ctrl-C three times, then checked ready-state
Ctrl-C and TERM. Apptainer checked the corresponding X11 socket and lock after
every lifecycle case. Each browser check
used real pointer menu/modal interaction, two viewport aspect ratios and a GUI
HDF5 export verified pixel-for-pixel against a synthetic 32-by-32 image.
Tests used native x86_64 on the maintainer's controlled Linux host,
synthetic images and format-only ZIP fixtures; they do not establish scientific
accuracy or production-model performance.

Default model discovery selects one prepared root, never searches multiple roots
for a requested model. A higher-priority incomplete root fails closed; use an
explicit override to select another complete root. Symlink host paths are
resolved physically. Manual readonly fallback after disabling automatic discovery:

```sh
export TAFFISH_ILASTIK_MODEL_AUTO_MOUNT=0
TAFFISH_DOCKER_RUN_ARGS="-v $ROOT/1.4.2:/models/ilastik:ro" \
TAFFISH_CONTAINER_BACKEND=docker taf-ilastik ilastik-models --verify-only
TAFFISH_PODMAN_RUN_ARGS="-v $ROOT/1.4.2:/models/ilastik:ro" \
TAFFISH_CONTAINER_BACKEND=podman taf-ilastik ilastik-models --verify-only
TAFFISH_APPTAINER_RUN_ARGS="--bind $ROOT/1.4.2:/models/ilastik:ro" \
TAFFISH_CONTAINER_BACKEND=apptainer taf-ilastik ilastik-models --verify-only
```

## Same-Upstream r2 Repair

Upstream tag/commit and official CPU binary archive are unchanged. This successor
repairs direct Index scratch/mount separation, private model-validation HOME,
prepared-root reuse across packaging releases, failure diagnostics and supervised
GUI cleanup. It adds explicit selected-ZIP acquisition, not a model catalog
crawler. Real RFB readiness, a VNC-child-only open-file limit and owner-checked
display cleanup address GUI startup/exit robustness without changing server
settings. Xvfb uses an isolated session; early signals are deferred across the
PID-assignment window, and cleanup captures owned endpoints before forwarding
shutdown. Atomic private log creation also protects permissive-umask sessions
and rejects reuse of predictable legacy paths. The canonical Action is byte-identical to fresh `taf new`; it is not
handwritten or customized. Documentation follows the shared tool template roles:
short installed-wrapper help, full resource/backend/validation details here.

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

Protocol tests also reject silent or malformed RFB services. An early-interrupt
PTY fixture deliberately leaves an X11 socket behind on child shutdown and
requires the helper to reclaim that owned socket and lock. Forced-Xvfb
and occupied-display tests cover exact endpoint cleanup and foreign-session
preservation. These tests do not replace actual browser pointer/menu/export
verification of the current candidate.

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
