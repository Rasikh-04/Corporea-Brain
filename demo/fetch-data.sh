#!/usr/bin/env bash
# Fetch the public sample scans the demonstration uses, into git-ignored build/demo-data/.
#
# Rule 8: this is a downloader, never the data. These three files are the 3D Slicer project's
# own public sample data, the same ones its SampleData module serves, pinned by SHA-256 from
# Slicer/Modules/Scripted/SampleData/SampleData.py at our pinned revision. They are not patient
# data of ours and nothing here is committed.
#
# Run it once while online. The demonstration itself needs no network.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/build/demo-data"
BASE="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256"

# file name, SHA-256
SAMPLES=(
  "MR-head.nrrd cc211f0dfd9a05ca3841ce1141b292898b2dd2d3f08286affadf823a7e58df93"
  "RegLib_C01_1.nrrd 998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95"
  "RegLib_C01_2.nrrd 1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97"
)

verify() { echo "$2  $DEST/$1" | sha256sum --check --status; }

mkdir -p "$DEST"
failed=0
for sample in "${SAMPLES[@]}"; do
  read -r name digest <<<"$sample"
  if [[ -f "$DEST/$name" ]] && verify "$name" "$digest"; then
    echo "ok       $name (already present, checksum matches)"
    continue
  fi
  if [[ "${1:-}" == "--check" ]]; then
    echo "MISSING  $name"
    failed=1
    continue
  fi
  echo "fetching $name"
  curl --fail --silent --show-error --location --max-time 600 \
    --output "$DEST/$name.part" "$BASE/$digest"
  mv "$DEST/$name.part" "$DEST/$name"
  if verify "$name" "$digest"; then
    echo "ok       $name"
  else
    echo "FAILED   $name: checksum mismatch, file removed" >&2
    rm -f "$DEST/$name"
    failed=1
  fi
done
exit "$failed"
