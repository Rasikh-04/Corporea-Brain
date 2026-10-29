#!/usr/bin/env bash
# The instructor demonstration, one step at a time.
#
#   demo/run-demo.sh            interactive: y or Enter for next, b for back
#   demo/run-demo.sh --check    preflight only, exit non-zero if anything is missing
#   demo/run-demo.sh --auto     run every step without prompting (rehearsal)
#   demo/run-demo.sh --list     print the steps and exit
#
# Each step prints what it is about to show, runs it, and prints what came back. Steps that
# need the application drive one long-lived Slicer window through demo/slicer/driver.py, so
# going forward or back never waits for a restart. Step numbers match demo/briefing.html.
#
# Every step is labelled PLATFORM (stock 3D Slicer, not our work), OURS (code in this
# repository) or MOCK (synthetic data showing a result we have not built yet).

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SLICER="${CORPOREA_SLICER:-$ROOT/Slicer-build/Slicer-build/Slicer}"
NATIVE="${CORPOREA_NATIVE:-$ROOT/../BrainTwin_Native}"
PY="$ROOT/.venv/bin/python"
STATE="$ROOT/build/demo-state"
BENCH_BATCH_TIER0="2026-07-31-2239-machineA-tier0"
BENCH_BATCH_TIER1="2026-08-02-0131-machineA-rust-t1"
SLICER_START_TIMEOUT_S=120
ACT_TIMEOUT_S=120

MODE="interactive"
case "${1:-}" in
  --check) MODE="check" ;;
  --auto) MODE="auto" ;;
  --list) MODE="list" ;;
  "") ;;
  *) echo "usage: demo/run-demo.sh [--check | --auto | --list]" >&2; exit 2 ;;
esac

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  BOLD=$'\e[1m'; DIM=$'\e[2m'; RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'
  BLUE=$'\e[34m'; MAGENTA=$'\e[35m'; RESET=$'\e[0m'
else
  BOLD=""; DIM=""; RED=""; GREEN=""; YELLOW=""; BLUE=""; MAGENTA=""; RESET=""
fi

# id | label | title
STEPS=(
  "preflight|CHECK|Preflight: is everything on this laptop?"
  "platform|PLATFORM|The base: 3D Slicer, built from source here"
  "load|PLATFORM|Load a scan from local disk"
  "render3d|PLATFORM|3D volume rendering on this laptop's GPU"
  "segment|PLATFORM|Segmentation tools, driven from a Python script"
  "compare|PLATFORM|Two scans side by side"
  "phantom|OURS|Our orientation phantom: left must stay left"
  "harness|OURS|Our test suite and the empty results tables"
  "mock_attribution|MOCK|The result we are building toward"
  "stacks|EVIDENCE|The stack comparison we ran"
  "decisions|ASK|What we need decided"
)

say() { printf '  %s\n' "$@"; }
note() { printf '  %s%s%s\n' "$DIM" "$*" "$RESET"; }
good() { printf '  %s%s%s %s\n' "$GREEN" "ok  " "$RESET" "$*"; }
warn() { printf '  %s%s%s %s\n' "$YELLOW" "warn" "$RESET" "$*"; }
bad() { printf '  %s%s%s %s\n' "$RED" "FAIL" "$RESET" "$*"; }
# Runs from the repository root, so pytest reads pytest.ini and never wanders into Slicer/.
run() {
  printf '  %s$ %s%s\n' "$DIM" "${*/#"$ROOT"\//}" "$RESET"
  (cd "$ROOT" && "$@") 2>&1 | sed 's/^/    /'
  return "${PIPESTATUS[0]}"
}

label_colour() {
  case "$1" in
    PLATFORM) printf '%s' "$BLUE" ;;
    OURS) printf '%s' "$GREEN" ;;
    MOCK) printf '%s' "$MAGENTA" ;;
    *) printf '%s' "$YELLOW" ;;
  esac
}

# --- Slicer process -------------------------------------------------------------------

SLICER_PID=""
SEQUENCE=0

slicer_running() { [[ -n "$SLICER_PID" ]] && kill -0 "$SLICER_PID" 2>/dev/null; }

start_slicer() {
  slicer_running && return 0
  mkdir -p "$STATE"
  rm -f "$STATE/ready" "$STATE/control" "$STATE/status"
  note "Starting Slicer. The first start takes about twenty seconds."
  CORPOREA_DEMO_ROOT="$ROOT" CORPOREA_DEMO_STATE="$STATE" \
    CORPOREA_DEMO_SHOTS="${CORPOREA_DEMO_SHOTS:-}" \
    "$SLICER" --no-splash --python-script "$ROOT/demo/slicer/driver.py" \
    >"$STATE/slicer.log" 2>&1 &
  SLICER_PID=$!
  local waited=0
  until [[ -f "$STATE/ready" ]]; do
    if ! slicer_running; then
      bad "Slicer exited during startup. Last lines of $STATE/slicer.log:"
      tail -n 8 "$STATE/slicer.log" | sed 's/^/    /'
      SLICER_PID=""
      return 1
    fi
    if ((waited >= SLICER_START_TIMEOUT_S * 5)); then
      bad "Slicer did not report ready within ${SLICER_START_TIMEOUT_S} s. See $STATE/slicer.log"
      return 1
    fi
    sleep 0.2
    waited=$((waited + 1))
  done
}

# Ask the running Slicer to show one act, then print the facts it reports back.
slicer_act() {
  start_slicer || return 1
  SEQUENCE=$((SEQUENCE + 1))
  local token="$$-$SEQUENCE"
  printf '%s %s\n' "$token" "$1" >"$STATE/control.tmp"
  mv "$STATE/control.tmp" "$STATE/control"
  local waited=0
  until [[ -f "$STATE/status" ]] && [[ "$(head -n 1 "$STATE/status")" == "$token "* ]]; do
    if ! slicer_running; then
      bad "Slicer closed before the step finished. Press r to start it again."
      SLICER_PID=""
      return 1
    fi
    if ((waited >= ACT_TIMEOUT_S * 5)); then
      bad "No answer from Slicer within ${ACT_TIMEOUT_S} s. See $STATE/slicer.log"
      return 1
    fi
    sleep 0.2
    waited=$((waited + 1))
  done
  local outcome
  outcome="$(head -n 1 "$STATE/status" | cut -d' ' -f2)"
  tail -n +2 "$STATE/status" | while IFS= read -r line; do say "$line"; done
  if [[ "$outcome" != "ok" ]]; then
    bad "The step reported an error. Full trace in $STATE/slicer.log"
    return 1
  fi
}

stop_slicer() {
  slicer_running || return 0
  slicer_act quit >/dev/null 2>&1
  local waited=0
  while slicer_running && ((waited < 50)); do sleep 0.2; waited=$((waited + 1)); done
  slicer_running && kill "$SLICER_PID" 2>/dev/null
  SLICER_PID=""
}

# --- Steps ----------------------------------------------------------------------------

step_preflight() {
  local failures=0
  if [[ -x "$SLICER" ]]; then good "Slicer launcher: ${SLICER#"$ROOT"/}"; else
    bad "Slicer launcher not found at $SLICER"; failures=$((failures + 1)); fi
  if [[ -x "$PY" ]]; then good "Pipeline environment: .venv ($("$PY" --version 2>&1))"; else
    bad "No .venv. Run scripts/setup-env.sh"; failures=$((failures + 1)); fi
  if "$ROOT/demo/fetch-data.sh" --check >/dev/null 2>&1; then
    good "Public sample scans: 3 files in build/demo-data, checksums match"
  else
    bad "Sample scans missing. Run demo/fetch-data.sh while online"; failures=$((failures + 1))
  fi
  if [[ ! -f "$ROOT/build/phantom.nii.gz" || ! -f "$ROOT/build/phantom-broken-lr.nii.gz" ]]; then
    "$PY" "$ROOT/scripts/make_phantom.py" --out "$ROOT/build/phantom.nii.gz" >/dev/null 2>&1
    "$PY" "$ROOT/scripts/make_phantom.py" --out "$ROOT/build/phantom-broken-lr.nii.gz" \
      --break-axis 0 >/dev/null 2>&1
  fi
  if [[ -f "$ROOT/build/phantom.nii.gz" && -f "$ROOT/build/phantom-broken-lr.nii.gz" ]]; then
    good "Orientation phantoms: generated in build/"
  else
    bad "Could not generate the phantoms with scripts/make_phantom.py"; failures=$((failures + 1))
  fi
  if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then good "A display is available"; else
    bad "No display. Run this from a desktop terminal, not over plain ssh"
    failures=$((failures + 1)); fi
  if [[ -f "$NATIVE/harness/report.py" ]]; then good "Benchmark repository: found"; else
    warn "BrainTwin_Native not found. Step 10 will point at the briefing instead"; fi
  local free_gb
  free_gb="$(df --output=avail -BG "$ROOT" | tail -n 1 | tr -dc '0-9')"
  say "Free disk: ${free_gb} GB.  Network needed for the demonstration: none."
  return "$failures"
}

step_harness() {
  say "The whole commit gate, as CI runs it:"
  run "$PY" -m pytest -q --no-header || return 1
  say "The orientation assertion on its own, the check step 7 just showed by eye:"
  run "$PY" -m pytest -q --no-header -m orientation || return 1
  say "The organ manifest validator. Deferred checks are printed, never skipped silently:"
  run "$PY" "$ROOT/scripts/validate_organs.py" || return 1
  say "Results table 4.1, rendered by the harness today. The rows exist before the numbers do:"
  PYTHONPATH="$ROOT/eval" "$PY" - <<'PYTHON' | sed 's/^/    /'
from corporea_eval import tables

stamp = tables.VersionStamp("no model yet", "stage 3 only", "no dataset yet", "none")
print(tables.render_table(tables.ALL_TABLES[0], {}, stamp=stamp))
PYTHON
}

step_stacks() {
  if [[ ! -f "$NATIVE/harness/report.py" ]]; then
    warn "BrainTwin_Native is not on this machine. The recorded numbers are in the briefing."
    return 0
  fi
  say "Tier 0, the Hello World control. Cold start, median of 5, one capture batch:"
  python3 "$NATIVE/harness/report.py" --batch "$BENCH_BATCH_TIER0" --csv "$NATIVE/results/runs.csv" \
    | awk '/cross-stack — batch/ {show = 1} /^Tier 1|^CPU clock|^Integrity/ {show = 0} show' \
    | sed 's/^/  /'
  say "Tier 1, volume plus mesh plus overlay. Only Rust completed it:"
  python3 "$NATIVE/harness/report.py" --batch "$BENCH_BATCH_TIER1" --csv "$NATIVE/results/runs.csv" \
    | awk '/^Tier 1/ {show = 1} /^CPU clock|^Integrity/ {show = 0} show' | sed 's/^/  /'
  say "Rust was fastest and smallest, and it is the only stack with a finished Tier 1."
  say "We still chose Qt, C++ and VTK through 3D Slicer, and not on frame rate:"
  say "  1. Slicer already is a Qt, C++ and VTK application, so stack and platform converge."
  say "  2. It supplies DICOM, segmentation, registration and rendering we would rebuild."
  say "  3. No medical volume-rendering template exists for Rust. We recorded that finding."
  say "  4. Python scripted modules let the whole team contribute from day one."
  note "Qt+VTK has one Tier 1 run on record and Avalonia none. That is a gap in the evidence,"
  note "and docs/DECISIONS/ADR-003 says so in writing."
}

step_decisions() {
  say "${BOLD}From you, today${RESET}"
  say "  1. May we build on 3D Slicer (open source, BSD-style licence) instead of from scratch?"
  say "  2. Is the contribution boundary acceptable? Platform is declared; we are assessed on"
  say "     the six components we originate and on the numbers they produce."
  say "  3. Is an offline desktop application the right form? Qt, C++, VTK and Python."
  say "  4. Is R2 the evaluated thesis, with R3 to R5 as optional stretch work?"
  say "${BOLD}Where your input would unblock us${RESET}"
  say "  5. ADR-006, blocking: coordinate space and parcellation atlas."
  say "  6. ADR-004: primary user. We recommend neurologist first, trainee second."
  say "  7. ADR-005: cognitive instrument. MMSE cannot ship; MoCA or Mini-Cog."
  say "  8. ADR-007: record store. We recommend SQLite with encryption."
  say "  9. Dataset agreements and the ethics route, which are the long lead-time items."
  note "Each of these is one card in section 8 of demo/briefing.html."
}

run_step() {
  case "$1" in
    preflight) step_preflight ;;
    harness) step_harness ;;
    stacks) step_stacks ;;
    decisions) step_decisions ;;
    *) slicer_act "$1" ;;
  esac
}

show_header() {
  local index="$1" id label title
  IFS='|' read -r id label title <<<"${STEPS[$index]}"
  printf '\n%s%s%s\n' "$DIM" "────────────────────────────────────────────────────────────" "$RESET"
  printf '%sStep %d of %d%s  %s[%s]%s  %s%s%s\n' "$DIM" "$((index + 1))" "${#STEPS[@]}" "$RESET" \
    "$(label_colour "$label")" "$label" "$RESET" "$BOLD" "$title" "$RESET"
  note "Briefing: demo/briefing.html, card \"Step $((index + 1))\""
  echo
}

list_steps() {
  local index id label title
  for index in "${!STEPS[@]}"; do
    IFS='|' read -r id label title <<<"${STEPS[$index]}"
    printf '  %2d  %-9s %s\n' "$((index + 1))" "$label" "$title"
  done
}

# --- Main -----------------------------------------------------------------------------

case "$MODE" in
  list) list_steps; exit 0 ;;
  check) show_header 0; step_preflight; exit $? ;;
esac

trap 'echo; note "Interrupted. Slicer is left open; close it by hand."; exit 130' INT

if [[ "$MODE" == "auto" ]]; then
  failures=0
  for index in "${!STEPS[@]}"; do
    show_header "$index"
    run_step "${STEPS[$index]%%|*}" || failures=$((failures + 1))
  done
  stop_slicer
  echo
  if ((failures == 0)); then good "All ${#STEPS[@]} steps ran."; else bad "$failures step(s) failed."; fi
  exit "$failures"
fi

index=0
rerun=1
while :; do
  if ((rerun)); then
    show_header "$index"
    run_step "${STEPS[$index]%%|*}" || warn "This step did not complete. r repeats it."
  fi
  rerun=1
  echo
  read -r -p "${BOLD}[y]${RESET} next  ${BOLD}[b]${RESET} back  ${BOLD}[r]${RESET} repeat  \
${BOLD}[1-${#STEPS[@]}]${RESET} jump  ${BOLD}[l]${RESET} list  ${BOLD}[q]${RESET} quit > " answer || answer="q"
  case "${answer,,}" in
    "" | y | yes | c | continue | n | next)
      if ((index + 1 >= ${#STEPS[@]})); then
        note "That was the last step. b goes back, q quits."
        rerun=0
      else
        index=$((index + 1))
      fi
      ;;
    b | back | p | prev | previous)
      if ((index == 0)); then note "Already at the first step."; rerun=0; else index=$((index - 1)); fi
      ;;
    r | repeat) ;;
    l | list) list_steps; rerun=0 ;;
    q | quit | exit)
      if slicer_running; then
        read -r -p "Close Slicer too? [Y/n] > " close || close="y"
        [[ "${close,,}" == n* ]] || stop_slicer
      fi
      exit 0
      ;;
    *)
      if [[ "$answer" =~ ^[0-9]+$ ]] && ((answer >= 1 && answer <= ${#STEPS[@]})); then
        index=$((answer - 1))
      else
        note "Not a command. y next, b back, r repeat, a number to jump, l list, q quit."
        rerun=0
      fi
      ;;
  esac
done
