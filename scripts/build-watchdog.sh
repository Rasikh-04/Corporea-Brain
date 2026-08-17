#!/usr/bin/env bash
#
# Corporea-Brain — Slicer superbuild watchdog.
#
# Polls a running superbuild quietly and exits the moment something is worth a
# human's attention. Exiting is the signal: run it in the background and the
# process ending is what tells you to look. It prints nothing until it has a
# reason, so it costs nothing to leave armed for hours.
#
# Wake conditions, and why each one is here:
#
#   PROCESS_GONE   the outer ninja vanished. Either the superbuild finished or
#                  something killed it. The script distinguishes the two by
#                  checking whether the outer counter reached its total, and
#                  looks for OOM reaping when it did not.
#   NEW_FAILURE    a FAILED: line appeared past the watermark recorded at arm
#                  time. Historical failures in a reused log never re-fire.
#   LOG_STALE      the log stopped moving while the process is still alive,
#                  which is what a hang looks like.
#   DISK_LOW       free space fell below the floor. docs/15 records disk as the
#                  leading risk for this build; catching it while the build is
#                  still alive is the difference between pausing and losing it.
#
# On failure it greps a window *around* the failing line rather than printing the
# log tail. docs/15 records why: the tail of this build is dense with C++20
# warnings and the real error routinely sits dozens of lines above it.
#
# Exit codes: 10 DISK_LOW, 11 NEW_FAILURE, 12 PROCESS_GONE, 13 LOG_STALE,
#             14 watchdog expired, 2 refused to arm.
#
# Usage:
#   scripts/build-watchdog.sh &                        arm against Slicer-build
#   scripts/build-watchdog.sh --disk-floor-gb 25 &     raise the disk floor
#   scripts/build-watchdog.sh --help                   full option list
#
# Options: --build-dir DIR, --poll SECS, --stale-mins N, --disk-floor-gb N,
#          --max-hours N
#
# See docs/15-BUILD_AND_ENVIRONMENT.md for the traps this watches for.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/Slicer-build"
POLL_SECS=60
STALE_MINS=30          # generous: configure and link steps are genuinely quiet
DISK_FLOOR_GB=15
MAX_HOURS=14           # hard stop, so an armed watchdog never lingers invisibly

while [ $# -gt 0 ]; do
  case "$1" in
    --build-dir)     BUILD_DIR="$2"; shift 2 ;;
    --poll)          POLL_SECS="$2"; shift 2 ;;
    --stale-mins)    STALE_MINS="$2"; shift 2 ;;
    --disk-floor-gb) DISK_FLOOR_GB="$2"; shift 2 ;;
    --max-hours)     MAX_HOURS="$2"; shift 2 ;;
    -h|--help)       sed -n '2,38p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

BUILD_DIR="$(cd "$BUILD_DIR" 2>/dev/null && pwd)" || {
  echo "REFUSED: build directory not found. Pass --build-dir." >&2; exit 2; }
LOG="$BUILD_DIR/build.log"
STATE_DIR="$BUILD_DIR/.monitor"

[ -f "$LOG" ] || { echo "REFUSED: no build.log in $BUILD_DIR" >&2; exit 2; }
mkdir -p "$STATE_DIR"

# shellcheck source=lib/superbuild-probe.sh
. "$REPO_ROOT/scripts/lib/superbuild-probe.sh"

# Refuse to arm against a build that is not running, rather than firing
# PROCESS_GONE one second later and calling a finished build an incident.
OUTER_PID="$(detect_outer_pid "$BUILD_DIR")"
if [ -z "$OUTER_PID" ]; then
  echo "REFUSED: no ninja process owns $BUILD_DIR, so there is nothing to watch." >&2
  echo "         Start the superbuild first, then arm this watchdog." >&2
  exit 2
fi

watermark="$(capture_watermark "$LOG" "$STATE_DIR")"
started=$(date +%s)

snapshot() {
  echo "--- snapshot ---"
  echo "time      : $(date '+%Y-%m-%d %H:%M:%S')"
  echo "outer     : $(outer_progress_line "$LOG")"
  echo "inner     : $(inner_progress_line "$LOG" | cut -c1-100)"
  echo "disk      : $(df -h "$BUILD_DIR" | tail -1 | awk '{print $4" free"}')"
  echo "log tail  :"
  tail -15 "$LOG" 2>/dev/null | cut -c1-160 | sed 's/^/  | /'
}

while :; do
  # ---- disk floor ----
  free_gb="$(df -BG --output=avail "$BUILD_DIR" | tail -1 | tr -dc '0-9')"
  if [ -n "$free_gb" ] && [ "$free_gb" -lt "$DISK_FLOOR_GB" ]; then
    echo "WAKE REASON: DISK_LOW"
    echo "Free space fell to ${free_gb} GB, below the ${DISK_FLOOR_GB} GB floor."
    echo "The build is still running. Act before it fails on a partial write."
    snapshot
    exit 10
  fi

  # ---- new failure ----
  newfail="$(failures_past "$LOG" "$watermark")"
  if [ -n "$newfail" ]; then
    echo "WAKE REASON: NEW_FAILURE"
    echo "New FAILED: line(s) past watermark ${watermark}:"
    printf '%s\n' "$newfail" | cut -c1-200 | sed 's/^/  /'
    echo
    echo "Context around the first new failure (the tail is misleading, see docs/15):"
    firstline="$(printf '%s\n' "$newfail" | head -1 | cut -d: -f1)"
    sed -n "$(( firstline > 40 ? firstline - 40 : 1 )),$(( firstline + 15 ))p" "$LOG" \
      | grep -aE "error:|Error|FAILED:|undefined reference|No such file|cannot find" \
      | tail -25 | cut -c1-200 | sed 's/^/  | /'
    snapshot
    exit 11
  fi

  # ---- process gone ----
  if ! kill -0 "$OUTER_PID" 2>/dev/null; then
    echo "WAKE REASON: PROCESS_GONE"
    outer_last="$(outer_progress_line "$LOG")"
    o_done="$(printf '%s' "$outer_last" | sed -n 's#^\[\([0-9]\+\)/[0-9]\+\].*#\1#p')"
    o_total="$(printf '%s' "$outer_last" | sed -n 's#^\[[0-9]\+/\([0-9]\+\)\].*#\1#p')"
    if [ -n "$o_done" ] && [ "$o_done" = "$o_total" ]; then
      echo "The outer superbuild reached [${o_done}/${o_total}]. This looks like SUCCESS."
      echo "Verify before believing it: docs/15 records that a step here can report"
      echo "success while producing nothing. Check the built artifacts, not the marker."
    else
      echo "Outer ninja ${OUTER_PID} exited WITHOUT completing."
      echo "Last outer step: ${outer_last:-<none>}"
      echo "No new FAILED: line was seen, so this was most likely killed,"
      echo "OOM-reaped, or interrupted rather than a compile failure."
      echo "Recent kernel OOM activity, if any:"
      { dmesg -T 2>/dev/null || journalctl -k --since '-2 hours' 2>/dev/null; } \
        | grep -aiE "out of memory|oom-kill|killed process" | tail -5 | sed 's/^/  | /'
    fi
    snapshot
    exit 12
  fi

  # ---- hung ----
  quiet_min=$(( ( $(date +%s) - $(stat -c %Y "$LOG") ) / 60 ))
  if [ "$quiet_min" -ge "$STALE_MINS" ]; then
    echo "WAKE REASON: LOG_STALE"
    echo "build.log has not been written for ${quiet_min} min (threshold ${STALE_MINS})."
    echo "Outer ninja ${OUTER_PID} is still alive, so this may be a hang, a very"
    echo "long single compile or link, or a stalled configure step."
    echo "Active build processes:"
    pgrep -a '^(cc1plus|cc1|collect2|ld|ld\.bfd|ld\.gold|ld\.lld|cmake|moc|ninja|ninja-build)$' \
      2>/dev/null | head -8 | cut -c1-160 | sed 's/^/  | /'
    snapshot
    exit 13
  fi

  # ---- hard stop ----
  if [ $(( ($(date +%s) - started) / 3600 )) -ge "$MAX_HOURS" ]; then
    echo "WAKE REASON: WATCHDOG_EXPIRED"
    echo "Watchdog hit its ${MAX_HOURS}h limit with the build still running."
    echo "Nothing is wrong. Re-arm it if you still want coverage."
    snapshot
    exit 14
  fi

  sleep "$POLL_SECS"
done
