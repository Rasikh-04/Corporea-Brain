#!/usr/bin/env bash
#
# Corporea-Brain — environment verification.
#
# Implements the checkable subset of "Verifying the install" in
# docs/15-BUILD_AND_ENVIRONMENT.md, plus the machine-requirement and known-trap checks
# from that document's tables.
#
# Steps 1-7 of the doc's verification list need a built application, a phantom volume and
# an evaluation harness, none of which exist yet. They are printed as SKIP with the reason,
# never silently omitted — a check that quietly does not run is worse than one that fails.
#
# Exit code: 0 if no FAIL, 1 otherwise. WARN does not fail the run.
#
# Usage:
#   scripts/check-env.sh               gate on the development environment only
#   scripts/check-env.sh --superbuild  also gate on the Slicer superbuild disk budget
#
# Disk is checked against whichever budget you are actually about to spend. Nothing is
# reserved ahead of time. Until you are ready to configure the superbuild, its 60 GB is
# reported as deferred, not failed, so a machine that is short on disk can still hold a
# complete and verified development environment.
#
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

GATE_SUPERBUILD=0
[[ "${1:-}" == "--superbuild" ]] && GATE_SUPERBUILD=1

# RAM, CPU and the superbuild disk figure come from the "Machine requirements, honestly"
# table in docs/15-BUILD_AND_ENVIRONMENT.md.
MIN_RAM_GB=16
MIN_CORES=4
DISK_SUPERBUILD_GB=60

# What the development environment alone costs: the Python venv (torch CPU ~1 GB, antspyx,
# nnU-Net and their trees ~2 GB), system packages already installed, and working headroom.
# Measured, not reserved. Datasets and the superbuild are budgeted separately.
DISK_ENV_GB=8

PIPELINE_PYTHON="3.12"

fails=0
warns=0

pass() { printf '  \033[32mPASS\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; fails=$((fails+1)); }
warn() { printf '  \033[33mWARN\033[0m  %s\n' "$*"; warns=$((warns+1)); }
skip() { printf '  \033[90mSKIP\033[0m  %s\n' "$*"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }

# --- Machine ------------------------------------------------------------------
head_ "Machine requirements"

disk_gb=$(df -BG --output=avail "$REPO_ROOT" | tail -1 | tr -dc '0-9')

# Account for what this project already occupies, so the number below is the project's
# real footprint rather than a guess. Missing paths contribute nothing.
occupied_mb=0
for p in "${REPO_ROOT}/.venv" "${HOME}/.ccache" "${REPO_ROOT}/build" "${REPO_ROOT}/.cache"; do
  [[ -e "$p" ]] || continue
  sz=$(du -sm "$p" 2>/dev/null | cut -f1)
  occupied_mb=$((occupied_mb + ${sz:-0}))
done
printf '  \033[90mINFO\033[0m  project occupies %s MB (.venv, ccache, build, cache)\n' "$occupied_mb"

# Gate 1: the development environment. This is what you are spending now.
if [[ "$disk_gb" -ge "$DISK_ENV_GB" ]]; then
  pass "disk free ${disk_gb} GB, enough for the development environment (${DISK_ENV_GB} GB)"
else
  fail "disk free ${disk_gb} GB, below the ${DISK_ENV_GB} GB the development environment \
needs. The venv install will fail partway."
fi

# Gate 2: the superbuild. Deferred by default, because it is a separate spend on a separate
# day and a shortfall here must not block environment work.
if [[ "$disk_gb" -ge "$DISK_SUPERBUILD_GB" ]]; then
  pass "disk free ${disk_gb} GB, enough for the Slicer superbuild (${DISK_SUPERBUILD_GB} GB)"
elif [[ "$GATE_SUPERBUILD" -eq 1 ]]; then
  fail "disk free ${disk_gb} GB, below the ${DISK_SUPERBUILD_GB} GB superbuild minimum \
(docs/15-BUILD_AND_ENVIRONMENT.md, machine requirements table). The superbuild compiles its \
own VTK, ITK, CTK, Qt and Python, and dies partway with an error that does not name disk."
else
  printf '  \033[90mDEFER\033[0m %s\n' "superbuild needs ${DISK_SUPERBUILD_GB} GB, \
${disk_gb} GB free. Not gated: pass --superbuild when you are ready to configure it."
fi

ram_gb=$(free -g | awk '/^Mem:/{print $2}')
if [[ "$ram_gb" -ge "$MIN_RAM_GB" ]]; then
  pass "RAM ${ram_gb} GB"
else
  warn "RAM ${ram_gb} GB, below the ${MIN_RAM_GB} GB minimum. Limit parallel jobs (-j4 or \
fewer) or the linker will be killed."
fi

cores=$(nproc)
if [[ "$cores" -ge "$MIN_CORES" ]]; then
  pass "CPU ${cores} logical cores"
else
  warn "CPU ${cores} cores. This is wall-clock build time, directly."
fi

# --- Build toolchain ----------------------------------------------------------
head_ "Build toolchain"

for tool in cmake ninja ccache git gcc g++ patch; do
  if command -v "$tool" >/dev/null 2>&1; then
    pass "$tool  $("$tool" --version 2>&1 | head -1)"
  else
    fail "$tool not found. Run scripts/setup-env.sh."
  fi
done

# CMake 4.x removes support for `cmake_minimum_required(VERSION <3.5)`, which the Slicer
# superbuild's external projects still declare. Configure aborts with an error that names
# the dependency, not the real cause.
if command -v cmake >/dev/null 2>&1; then
  cmake_major=$(cmake --version | head -1 | sed -E 's/.* ([0-9]+)\..*/\1/')
  if [[ "$cmake_major" -ge 4 ]]; then
    warn "CMake ${cmake_major}.x drops compatibility with cmake_minimum_required < 3.5, \
which Slicer superbuild dependencies still declare. Expect configure to abort. Mitigation: \
-DCMAKE_POLICY_VERSION_MINIMUM=3.5, or install CMake 3.31.x alongside."
  else
    pass "CMake major version ${cmake_major} is compatible with the superbuild"
  fi
fi

# --- Known traps --------------------------------------------------------------
head_ "Known traps"

# docs/15: "Do not install a system Qt and expect Slicer to use it. A system Qt on the path
# is a common source of a confusing mid-build failure."
qt_on_path=""
for q in qmake qmake6 qmake-qt5; do
  command -v "$q" >/dev/null 2>&1 && qt_on_path="${qt_on_path} ${q}=$(command -v $q)"
done
if [[ -n "$qt_on_path" ]]; then
  warn "system Qt on PATH:${qt_on_path}. The superbuild provides its own Qt. Remove these \
from PATH before configuring, or expect a Qt version mismatch mid-build."
else
  pass "no system Qt on PATH"
fi

if [[ -n "${CMAKE_PREFIX_PATH:-}" ]]; then
  warn "CMAKE_PREFIX_PATH is set (${CMAKE_PREFIX_PATH}). It can redirect the superbuild to \
system libraries. Unset it before configuring."
else
  pass "CMAKE_PREFIX_PATH not set"
fi

# --- Pipeline tools -----------------------------------------------------------
head_ "Pipeline tools"

if command -v dcm2niix >/dev/null 2>&1; then
  pass "dcm2niix  $(dcm2niix --version 2>&1 | head -1)"
else
  fail "dcm2niix not found. Pipeline stage 1 cannot convert DICOM to NIfTI."
fi

if command -v "python${PIPELINE_PYTHON}" >/dev/null 2>&1; then
  pass "python${PIPELINE_PYTHON}  $(python${PIPELINE_PYTHON} --version 2>&1)"
else
  fail "python${PIPELINE_PYTHON} not found. The system interpreter is \
$(python3 --version 2>&1), for which antspyx publishes no wheel."
fi

# --- Pipeline Python environment ----------------------------------------------
head_ "Pipeline Python environment"

VENV_PY="${REPO_ROOT}/.venv/bin/python"
if [[ -x "$VENV_PY" ]]; then
  pass "venv present  $("$VENV_PY" --version 2>&1)"

  for mod in nibabel pydicom SimpleITK ants nnunetv2 bids numpy scipy pandas torch yaml pytest; do
    if "$VENV_PY" -c "import ${mod}" >/dev/null 2>&1; then
      ver=$("$VENV_PY" -c "import ${mod};print(getattr(${mod},'__version__','?'))" 2>/dev/null)
      pass "import ${mod}  ${ver}"
    else
      fail "import ${mod} failed. Re-run scripts/setup-env.sh --no-system."
    fi
  done

  # The CUDA build is unusable on a 2 GB-VRAM GPU and costs several GB of disk on a machine
  # that is already short of the superbuild's 60 GB. It arrives by accident, not by choice:
  # see pipeline/constraints.txt.
  if "$VENV_PY" -c "import torch" >/dev/null 2>&1; then
    tver=$("$VENV_PY" -c "import torch;print(torch.__version__)" 2>/dev/null)
    if [[ "$tver" == *"+cpu"* ]]; then
      pass "torch is the CPU-only build (${tver})"
    else
      fail "torch ${tver} is not the CPU-only build. The reference machine's GPU cannot hold \
nnU-Net 3D inference, so this is pure disk cost. Re-run scripts/setup-env.sh --no-system, \
which now constrains it, then remove the orphaned nvidia-* packages."
    fi
  fi

  # The direct signal, and the one that costs the disk. torch's version string can be right
  # while an nvidia tree left over from an earlier install is still on disk, because pip does
  # not remove packages that stop being needed.
  nvidia_pkgs=$("$VENV_PY" -m pip list --format=freeze 2>/dev/null | grep -c '^nvidia-' || true)
  if [[ "${nvidia_pkgs:-0}" -eq 0 ]]; then
    pass "no nvidia-* packages in the venv"
  else
    venv_gb=$(du -sh "${REPO_ROOT}/.venv" 2>/dev/null | cut -f1)
    fail "${nvidia_pkgs} nvidia-* packages in the venv (.venv is ${venv_gb}). Nothing here can \
use them. Remove with: .venv/bin/pip uninstall -y \$(.venv/bin/pip list --format=freeze | \
grep '^nvidia-' | cut -d= -f1)"
  fi

  if [[ -f "${REPO_ROOT}/pipeline/requirements.lock.txt" ]]; then
    pass "pipeline/requirements.lock.txt present"
  else
    warn "pipeline/requirements.lock.txt missing. Without it the environment is not \
reproducible. Re-run scripts/setup-env.sh --no-system."
  fi
else
  fail "no venv at ${REPO_ROOT}/.venv. Run scripts/setup-env.sh."
fi

# --- Verification steps from docs/15 ------------------------------------------
head_ "Verification steps from docs/15"

skip "1. custom application launches, disclaimer before any data  — no application built"
skip "2. home module is the Body Layer                            — no application built"
skip "3. sample volume from bench assets renders                  — no application built"

# Steps 4, 5 and 6 no longer need the application, and by rule 7 they were built first:
# "build the measuring instrument before the thing it measures". Each runs the real test, not
# a proxy for it, so a failure here is the same failure CI reports.
run_pytest() {
  local step="$1" selection="$2"
  if [[ ! -x "$VENV_PY" ]]; then
    skip "${step} — no venv; run scripts/setup-env.sh"
    return
  fi
  if ! "$VENV_PY" -c "import pytest" >/dev/null 2>&1; then
    skip "${step} — pytest not installed; run scripts/setup-env.sh --no-system"
    return
  fi
  local output
  if output=$("$VENV_PY" -m pytest -q "$selection" 2>&1); then
    pass "${step}  ($(printf '%s' "$output" | tail -1))"
  else
    fail "${step}"$'\n'"$(printf '%s' "$output" | tail -20)"
  fi
}

run_pytest "4. orientation assertion against the asymmetric phantom" \
  "${REPO_ROOT}/pipeline/tests/test_phantom_orientation.py"
run_pytest "5. evaluation harness known-answer test (hand-computed Dice)" \
  "${REPO_ROOT}/eval/tests/test_metrics_known_answer.py"

if [[ -x "$VENV_PY" ]] && "$VENV_PY" -c "import yaml" >/dev/null 2>&1; then
  if organs_out=$("$VENV_PY" "${REPO_ROOT}/scripts/validate_organs.py" 2>&1); then
    pass "6. organ manifest validator  ($(printf '%s' "$organs_out" | tail -1 | sed 's/^ *//'))"
  else
    fail "6. organ manifest validator"$'\n'"$organs_out"
  fi
else
  skip "6. organ manifest validator — PyYAML not installed; run scripts/setup-env.sh --no-system"
fi

skip "7. repeat 3-6 with the network disconnected                 — depends on 3"

printf '\n  Steps 4 and 5 are the two that fail silently. Nothing built on a broken\n'
printf '  orientation or a broken metric is worth anything, which is why they were\n'
printf '  wired up before anything they measure existed.\n'

# --- Summary ------------------------------------------------------------------
head_ "Summary"
printf '  %d fail, %d warn\n\n' "$fails" "$warns"
[[ "$fails" -eq 0 ]]
