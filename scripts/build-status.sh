#!/usr/bin/env bash
#
# Corporea-Brain — Slicer superbuild status probe.
#
# Prints one compact report on the running (or finished) superbuild: which outer
# external project is active, how far the inner build has got, the current target
# rate, an ETA, and the resources the build is spending.
#
# Nothing here is hardcoded to a particular run. The outer ninja process, both
# progress counters and their totals are discovered from the build tree and the
# log, so this works against any superbuild in any build directory.
#
# The probe is read-only with respect to the build. The single thing it writes is
# a progress sample under $BUILD_DIR/.monitor/, which is inside a git-ignored
# *-build/ directory and dies with the build tree it describes.
#
# A rate needs two samples. The first run reports "collecting" rather than
# inventing a number from one data point.
#
# Exit code: 0 always, unless the build directory or log is missing (2). Reporting
# a problem is this script's job; it is not a gate, so a failing build still exits 0.
#
# Usage:
#   scripts/build-status.sh                    probe the default Slicer-build tree
#   scripts/build-status.sh --build-dir DIR    probe a different build tree
#
# See docs/15-BUILD_AND_ENVIRONMENT.md for the failure modes this surfaces.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/Slicer-build"

while [ $# -gt 0 ]; do
  case "$1" in
    --build-dir) BUILD_DIR="$2"; shift 2 ;;
    -h|--help)   sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

BUILD_DIR="$(cd "$BUILD_DIR" 2>/dev/null && pwd)" || {
  echo "FAIL: build directory not found. Pass --build-dir." >&2; exit 2; }
LOG="$BUILD_DIR/build.log"
STATE_DIR="$BUILD_DIR/.monitor"
SAMPLES="$STATE_DIR/samples.csv"

[ -f "$LOG" ] || { echo "FAIL: no build.log in $BUILD_DIR" >&2; exit 2; }
mkdir -p "$STATE_DIR"

# shellcheck source=lib/superbuild-probe.sh
. "$REPO_ROOT/scripts/lib/superbuild-probe.sh"

now=$(date +%s)
printf '=== superbuild status  %s ===\n' "$(date '+%Y-%m-%d %H:%M:%S')"
printf 'build dir : %s\n' "$BUILD_DIR"

# --- liveness -------------------------------------------------------------
pid="$(detect_outer_pid "$BUILD_DIR")"
if [ -n "$pid" ]; then
  printf 'process   : ALIVE (outer ninja %s, up %s)\n' \
    "$pid" "$(ps -o etime= -p "$pid" | tr -d ' ')"
else
  printf 'process   : not running (no ninja owns %s)\n' "$BUILD_DIR"
fi

# --- progress -------------------------------------------------------------
outer_line="$(outer_progress_line "$LOG")"
inner_done="$(inner_done "$LOG")"
inner_total="$(inner_total "$LOG")"

printf 'outer     : %s\n' "${outer_line:-<no external-project step seen>}"
if [ "$inner_total" -gt 0 ]; then
  printf 'inner     : [%s/%s] (%d%%)\n' \
    "$inner_done" "$inner_total" $(( inner_done * 100 / inner_total ))
else
  printf 'inner     : <no inner build progress seen>\n'
fi

# --- log freshness --------------------------------------------------------
log_mtime=$(stat -c %Y "$LOG")
printf 'log       : last write %s min ago (%s)\n' \
  $(( (now - log_mtime) / 60 )) "$(date -d "@$log_mtime" '+%H:%M:%S')"
printf 'last line : %s\n' "$(tail -1 "$LOG" | cut -c1-120)"

# --- failures -------------------------------------------------------------
# Only a watchdog arming run records a watermark. Without one there is no notion
# of "new", so historical failures are reported as history rather than as an
# alarm — a log reused across attempts always carries the old ones.
total_fail="$(grep -acE "^FAILED:" "$LOG" 2>/dev/null)"
if [ -f "$STATE_DIR/failed-watermark" ]; then
  watermark="$(read_watermark "$STATE_DIR")"
  newfail="$(failures_past "$LOG" "$watermark")"
  if [ -n "$newfail" ]; then
    printf 'FAILURES  : *** NEW FAILED LINES BEYOND WATERMARK %s ***\n' "$watermark"
    printf '%s\n' "$newfail" | head -5 | cut -c1-150 | sed 's/^/  /'
  else
    printf 'failures  : none new since watermark line %s (%s historical in log)\n' \
      "$watermark" "$total_fail"
  fi
else
  printf 'failures  : %s in log, none classified as new (no watchdog watermark recorded)\n' \
    "$total_fail"
fi

# --- resources ------------------------------------------------------------
printf 'disk      : %s\n' "$(df -h "$BUILD_DIR" | tail -1 | awk '{print $4" free of "$2" ("$5" used)"}')"
printf 'memory    : %s\n' "$(free -g | awk '/^Mem:/{print $7" GB available of "$2" GB"}')"
printf 'tree size : %s\n' "$(du -sh "$BUILD_DIR" 2>/dev/null | cut -f1)"

# --- rate and ETA ---------------------------------------------------------
[ -f "$SAMPLES" ] || echo "epoch,inner_done" > "$SAMPLES"
echo "$now,$inner_done" >> "$SAMPLES"

awk -F, -v now="$now" -v cur="$inner_done" -v total="$inner_total" '
  NR>1 && $1 != "" {
    if (now - $1 <= 5400) { if (base_t == 0 || $1 < base_t) { base_t=$1; base_d=$2 } }
    if (first_t == 0 || $1 < first_t) { first_t=$1; first_d=$2 }
  }
  END {
    if (total > 0 && cur >= total) { print "rate      : inner build complete"; exit }
    if (base_t == 0 || base_t == now) { print "rate      : collecting (need a second sample)"; exit }
    dt = (now - base_t) / 60; dd = cur - base_d
    if (dt <= 0 || dd <= 0) { print "rate      : no forward progress since last sample"; exit }
    rate = dd / dt
    printf "rate      : %.1f targets/min over last %.0f min (%d targets)\n", rate, dt, dd
    if (total > 0) {
      remain = (total - cur) / rate
      printf "ETA inner : ~%.1f h remaining -> approx %s\n", remain/60, strftime("%H:%M", now + remain*60)
    }
    if (first_t != base_t) {
      odt = (now - first_t) / 60; odd = cur - first_d
      if (odt > 0 && odd > 0) printf "  (overall %.1f targets/min since first sample %.0f min ago)\n", odd/odt, odt
    }
  }
' "$SAMPLES"

printf 'note      : the ETA covers the inner build only; outer steps follow it.\n'
