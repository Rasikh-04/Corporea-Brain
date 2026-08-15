#!/usr/bin/env bash
#
# BrainTwin Desktop — development environment setup.
#
# Covers everything in docs/15-BUILD_AND_ENVIRONMENT.md that does not require the Slicer
# superbuild: system build dependencies, ccache, dcm2niix, and the pipeline Python
# environment. The superbuild itself is a separate, much longer job and is NOT run here.
#
# Idempotent. Safe to re-run.
#
# Usage:
#   scripts/setup-env.sh              full setup (prompts for sudo once)
#   scripts/setup-env.sh --no-system  skip the sudo/dnf step, Python environment only
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${REPO_ROOT}/.venv"
PYTHON_VERSION="3.12"
# Capped well below the 25G docs/15 suggests, because disk is the constraint on this
# machine and the cache only fills once superbuild work actually starts. Raise it when
# there is room. Override with CCACHE_MAX_SIZE in the environment.
CCACHE_MAX_SIZE="${CCACHE_MAX_SIZE:-10G}"
TORCH_VERSION="2.8.0"
TORCH_CPU_INDEX="https://download.pytorch.org/whl/cpu"

# This link is slow and drops connections. pip's default 15s socket timeout turns a
# stalled download into an error that names the package as if it did not exist. Retries
# plus a longer timeout make the install resumable instead of merely restartable.
PIP_OPTS=(--retries 10 --timeout 60)

DO_SYSTEM=1
[[ "${1:-}" == "--no-system" ]] && DO_SYSTEM=0

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
warn() { printf '\033[33mWARN: %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

# --- Step 1: system packages --------------------------------------------------
# The lists come from docs/15-BUILD_AND_ENVIRONMENT.md, Fedora section, plus dcm2niix
# (pipeline stage 1) and a Python 3.12 interpreter for the pipeline venv.
#
# Deliberately NOT installed: any system Qt. The Slicer superbuild provides its own Qt,
# and a system Qt on PATH is a documented cause of a confusing mid-build failure.
install_system_packages() {
  say "Installing system packages (requires sudo)"

  if ! command -v dnf >/dev/null 2>&1; then
    warn "dnf not found. This script's system step targets Fedora."
    warn "For Ubuntu, use the apt list in docs/15-BUILD_AND_ENVIRONMENT.md, then re-run"
    warn "this script with --no-system."
    return 1
  fi

  sudo dnf group install -y development-tools

  sudo dnf install -y \
    cmake git ninja-build ccache patch \
    libXt-devel mesa-libGL-devel mesa-libGLU-devel \
    libxcb-devel xcb-util-devel xcb-util-image-devel xcb-util-keysyms-devel \
    xcb-util-renderutil-devel xcb-util-wm-devel \
    libxkbcommon-devel libxkbcommon-x11-devel \
    dcm2niix \
    "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-devel"
}

# --- Step 2: ccache -----------------------------------------------------------
# The cache is shared across worktrees deliberately. It is content-addressed, so sharing
# is safe and materially faster when parallel agents build the same headers.
configure_ccache() {
  say "Configuring ccache"
  command -v ccache >/dev/null 2>&1 || { warn "ccache not installed, skipping"; return 0; }

  ccache --max-size="${CCACHE_MAX_SIZE}"
  ccache --show-config | grep -E 'max_size|cache_dir' || true

  cat <<EOF

  Add to your shell profile, and pass these to every CMake configure:

    export CCACHE_DIR=\$HOME/.ccache
    cmake ... -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
EOF
}

# --- Step 3: pipeline Python environment --------------------------------------
# Separate from Slicer's interpreter, deliberately.
setup_python_env() {
  say "Creating pipeline Python environment"

  local py="python${PYTHON_VERSION}"
  command -v "$py" >/dev/null 2>&1 \
    || die "$py not found. Run the system step, or install Python ${PYTHON_VERSION} manually.
       The system Python on Fedora 44 is 3.14, for which antspyx publishes no wheel."

  [[ -d "$VENV_DIR" ]] || "$py" -m venv "$VENV_DIR"
  # shellcheck disable=SC1091
  source "${VENV_DIR}/bin/activate"

  python -m pip install "${PIP_OPTS[@]}" --upgrade pip setuptools wheel

  # torch first, from the CPU-only index, so the resolver cannot pull the CUDA build.
  # See the rationale comment in pipeline/requirements.txt.
  say "Installing torch ${TORCH_VERSION} (CPU-only build)"
  python -m pip install "${PIP_OPTS[@]}" --index-url "${TORCH_CPU_INDEX}" "torch==${TORCH_VERSION}"

  say "Installing pipeline requirements"
  python -m pip install "${PIP_OPTS[@]}" -r "${REPO_ROOT}/pipeline/requirements.txt"

  say "Freezing lock file"
  python -m pip freeze --exclude-editable > "${REPO_ROOT}/pipeline/requirements.lock.txt"
  echo "  wrote pipeline/requirements.lock.txt"
}

main() {
  say "BrainTwin Desktop environment setup"
  echo "  repo:   ${REPO_ROOT}"
  echo "  python: ${PYTHON_VERSION}"

  if [[ "$DO_SYSTEM" -eq 1 ]]; then
    install_system_packages || die "system package step failed"
  else
    warn "Skipping system package step (--no-system)"
  fi

  configure_ccache
  setup_python_env

  say "Done"
  cat <<'EOF'
  Next:
    1. scripts/check-env.sh          verify what was just installed
    2. Free disk, then start the Slicer superbuild on the strongest available machine.
       See docs/15-BUILD_AND_ENVIRONMENT.md. It is the first technical risk to retire.
EOF
}

main "$@"
