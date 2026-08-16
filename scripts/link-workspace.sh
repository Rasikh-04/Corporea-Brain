#!/usr/bin/env bash
# Point this repository's build output at the `workspace` partition.
#
#   sudo scripts/link-workspace.sh
#
# What it does: mounts /mnt/workspace if it is not mounted, creates a project directory there
# owned by the invoking user, and replaces ./build with a symlink to it. Idempotent.
#
# READ THIS BEFORE EXPECTING IT TO UNBLOCK THE SUPERBUILD.
#
# It will not. The `workspace` partition (/dev/nvme0n1p6) is 19.4 GB. The Slicer superbuild
# needs 60 GB, per the machine requirements table in docs/15-BUILD_AND_ENVIRONMENT.md, and a
# symlink does not pool free space across filesystems: a directory linked here has 18 GB
# available and the 46 GB on / stays on /. Anything that needs 60 GB in one tree still needs
# 60 GB in one tree.
#
# What this script is actually good for is the ordinary build output — the generated phantom,
# ccache, scratch volumes, per-case working directories — all of which grow without bound and
# all of which currently grow on the same filesystem the superbuild will have to fit into.
# Moving them here buys headroom on / rather than replacing it.
#
# The routes to an actual 60 GB are in docs/15-BUILD_AND_ENVIRONMENT.md, disk budget section.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOUNT_POINT="/mnt/workspace"
PROJECT_DIR="${MOUNT_POINT}/corporea-brain"
BUILD_LINK="${REPO_ROOT}/build"

if [[ "${EUID}" -ne 0 ]]; then
  echo "This script creates a directory on ${MOUNT_POINT}, which is root-owned." >&2
  echo "Run it as: sudo ${BASH_SOURCE[0]}" >&2
  exit 1
fi

# The invoking user, not root: everything created here must be writable without sudo
# afterwards, or every later build command needs it too.
OWNER="${SUDO_USER:-root}"
OWNER_GROUP="$(id -gn "${OWNER}")"

if ! findmnt --mountpoint "${MOUNT_POINT}" >/dev/null 2>&1; then
  echo "mounting ${MOUNT_POINT}"
  mount "${MOUNT_POINT}"
fi

mkdir -p "${PROJECT_DIR}/build"
chown -R "${OWNER}:${OWNER_GROUP}" "${PROJECT_DIR}"

if [[ -L "${BUILD_LINK}" ]]; then
  current="$(readlink -f "${BUILD_LINK}")"
  if [[ "${current}" == "${PROJECT_DIR}/build" ]]; then
    echo "${BUILD_LINK} already points at ${PROJECT_DIR}/build"
  else
    echo "${BUILD_LINK} points at ${current}, not ${PROJECT_DIR}/build." >&2
    echo "Refusing to repoint an existing link. Remove it by hand if that is what you want." >&2
    exit 1
  fi
elif [[ -d "${BUILD_LINK}" ]]; then
  # A real directory with contents is somebody's build. Moving it is cheap and reversible;
  # deleting it is neither, so this never deletes.
  echo "moving existing ${BUILD_LINK} into ${PROJECT_DIR}/"
  rmdir "${BUILD_LINK}" 2>/dev/null || mv "${BUILD_LINK}" "${PROJECT_DIR}/build.moved.$(date +%s)"
  sudo -u "${OWNER}" ln -s "${PROJECT_DIR}/build" "${BUILD_LINK}"
elif [[ -e "${BUILD_LINK}" ]]; then
  echo "${BUILD_LINK} exists and is not a directory or a symlink. Refusing to touch it." >&2
  exit 1
else
  sudo -u "${OWNER}" ln -s "${PROJECT_DIR}/build" "${BUILD_LINK}"
fi

avail_gb="$(df -BG --output=avail "${PROJECT_DIR}" | tail -1 | tr -dc '0-9')"
echo
echo "build/ -> ${PROJECT_DIR}/build, ${avail_gb} GB free on ${MOUNT_POINT}"
echo
echo "This does NOT make the superbuild's 60 GB available. scripts/check-env.sh now measures"
echo "the filesystem that holds build/, so run it to see the real number:"
echo "  scripts/check-env.sh --superbuild"
