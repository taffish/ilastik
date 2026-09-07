# Synthetic format-only package; not a trained model or a scientific fixture.
from pathlib import Path
import hashlib
import sys
import zipfile

import numpy as np

root = Path(sys.argv[1])
architecture = b"class Tiny:\n    pass\n"
weights = b"taffish-smoke-weights\n"
values = np.linspace(-1e6, 1e6, 25, dtype=np.float32).reshape((1, 1, 5, 5))
np.save(root / "input.npy", values)
np.save(root / "output.npy", values)
rdf = f"""authors:
  - name: TAFFISH Smoke
description: Offline packaging fixture for the ilastik model import contract.
documentation: documentation.md
format_version: 0.4.10
inputs:
  - axes: bcyx
    data_range: [-.inf, .inf]
    data_type: float32
    name: input
    shape: [1, 1, 5, 5]
license: CC0-1.0
name: TAFFISH ilastik smoke model
outputs:
  - axes: bcyx
    data_range: [-.inf, .inf]
    data_type: float32
    halo: [0, 0, 0, 0]
    name: output
    shape: [1, 1, 5, 5]
test_inputs: [input.npy]
test_outputs: [output.npy]
timestamp: 2026-01-01T00:00:00Z
type: model
weights:
  pytorch_state_dict:
    architecture: architecture.py:Tiny
    architecture_sha256: {hashlib.sha256(architecture).hexdigest()}
    sha256: {hashlib.sha256(weights).hexdigest()}
    source: weights.pt
"""
with zipfile.ZipFile(root / "model.zip", "w", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("rdf.yaml", rdf)
    archive.writestr("documentation.md", "TAFFISH offline model fixture. " * 8)
    archive.writestr("architecture.py", architecture)
    archive.writestr("weights.pt", weights)
    archive.write(root / "input.npy", "input.npy")
    archive.write(root / "output.npy", "output.npy")
