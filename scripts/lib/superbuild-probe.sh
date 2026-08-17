#!/usr/bin/env bash
#
# Corporea-Brain — shared probe helpers for the superbuild monitors.
#
# Sourced by scripts/build-status.sh and scripts/build-watchdog.sh. Every helper
# here is read-only against the build tree and discovers its facts rather than
# assuming them, so the monitors are not pinned to one machine or one run.
#
# Two progress counters exist in a superbuild log and they must not be confused:
#
#   outer   the superbuild's own ExternalProject steps, e.g.
#           [221/225] Performing build step for 'Slicer'
#   inner   whatever nested build is currently running, e.g.
#           [3830/3830] Linking CXX shared module .../qSlicerFooPythonQt.so
#
# Outer lines are identifiable because every ExternalProject step names its
# project in quotes. Everything else with a [n/m] prefix belongs to a nested
# build. Several nested builds run over the life of a superbuild, each with its
# own total, so the inner counter is always read from the most recent line.

# Longest-lived ninja whose working directory is the build tree. The superbuild
# spawns nested ninja processes that come and go; the outer one started first,
# so the lowest /proc start-time wins. Empty output means no build is running.
detect_outer_pid() {
  local build_dir="$1" p cwd st best="" besttime=""
  for p in $(pgrep -x ninja 2>/dev/null; pgrep -x ninja-build 2>/dev/null); do
    cwd="$(readlink "/proc/$p/cwd" 2>/dev/null)" || continue
    [ "$cwd" = "$build_dir" ] || continue
    st="$(awk '{print $22}' "/proc/$p/stat" 2>/dev/null)" || continue
    [ -n "$st" ] || continue
    if [ -z "$besttime" ] || [ "$st" -lt "$besttime" ]; then besttime="$st"; best="$p"; fi
  done
  printf '%s' "$best"
}

_OUTER_RE="^\[[0-9]+/[0-9]+\] (Completed '|Performing [a-z]+ step for '|No [a-z]+ step for '|Forcing [a-z]+ step for '|Creating directories for ')"

# Most recent ExternalProject step line, whole.
outer_progress_line() {
  tac "$1" 2>/dev/null | grep -aEm1 "$_OUTER_RE"
}

# Most recent nested-build progress line, whole.
inner_progress_line() {
  tac "$1" 2>/dev/null | grep -aE "^\[[0-9]+/[0-9]+\] " | grep -avEm1 "$_OUTER_RE"
}

inner_done() {
  local l; l="$(inner_progress_line "$1")"
  printf '%s' "$(printf '%s' "$l" | sed -n 's#^\[\([0-9]\+\)/[0-9]\+\].*#\1#p')" | grep -E '^[0-9]+$' || printf '0'
}

inner_total() {
  local l; l="$(inner_progress_line "$1")"
  printf '%s' "$(printf '%s' "$l" | sed -n 's#^\[[0-9]\+/\([0-9]\+\)\].*#\1#p')" | grep -E '^[0-9]+$' || printf '0'
}

# The watchdog records the highest pre-existing FAILED: line when it arms, so
# historical failures from earlier attempts never re-trigger an alert. Without a
# recorded watermark, every prior failure in a reused log would fire at once.
capture_watermark() {
  local log="$1" state_dir="$2" n
  n="$(grep -acE "^FAILED:" "$log" 2>/dev/null)"
  [ "$n" -gt 0 ] 2>/dev/null \
    && grep -anE "^FAILED:" "$log" | tail -1 | cut -d: -f1 > "$state_dir/failed-watermark" \
    || echo 0 > "$state_dir/failed-watermark"
  cat "$state_dir/failed-watermark"
}

read_watermark() {
  cat "$1/failed-watermark" 2>/dev/null || echo 0
}

# FAILED: lines strictly after the watermark, as "lineno:text".
failures_past() {
  grep -anE "^FAILED:" "$1" 2>/dev/null | awk -F: -v w="$2" '$1 > w'
}
