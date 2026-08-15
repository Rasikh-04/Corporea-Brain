# 20 — AI workflow and cost

<a id="why"></a>

## Why this is a project document

A large share of this project's implementation output will come from AI-assisted work. That
makes model routing, context discipline and fan-out policy **engineering decisions with
measurable consequences**, not personal preferences. They belong in the documentation set for
the same reason the build environment does: an undocumented convention is one person's habit,
and this team is dispersed.

It is also a small, legitimate contribution to the implementation chapter — an honest account
of how an AI-assisted team actually worked, with numbers, is more interesting than most
methodology sections.

<a id="annexes"></a>

## The three annexes

Produced by parallel agents reading the installed ECC skill definitions and the actual
repositories. Each is grounded in what the tooling really does, with limitations stated.

| Annex | Covers | Key finding |
|---|---|---|
| [**A1** — Model routing and cost](ai-workflow/A1-MODEL_ROUTING_AND_COST.md) | Task-class to model-tier routing, local filtering before escalation, prompt caching for a large inherited codebase, budget tracking, depth levels | Local filtering is **tier control, not hygiene**: the router's input-size threshold means unfiltered build logs literally buy the more expensive model |
| [**A2** — Context budget and session hygiene](ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md) | Measured context surface, DAILY / LIBRARY / REMOVE lists, audit procedure, compaction checkpoints, CLAUDE.md ceilings | The installed surface costs roughly **36k tokens before a single file is read**; about 24k is reclaimable |
| [**A3** — Parallelism and benchmark automation](ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md) | Fan-out decision rule, worktree collision surfaces for a CMake superbuild, harness repurposing, local scheduled jobs | Fan-out wins only for **read-only sweeps**. Build fixes, renames and benchmark runs are strictly inline |

<a id="depth"></a>

## Depth levels

Declare one at session start. It persists for the session.

| Level | Use for | Model tier |
|---|---|---|
| **TRIAGE** | Build error triage, log reading, scaffolding, doc drafting, per-paper summaries | Cheapest |
| **BUILD** | Module implementation, pipeline logic, harness statistics, routine review | Default |
| **DECIDE** | Architecture, ADRs, evaluation design, deep review of safety-critical paths | Most capable, budgeted |

**The most capable tier is capped at roughly 6 to 10 calls for the entire project.** It is for
decisions that get written into an ADR, not for implementation. If a session is producing code,
it is not a DECIDE session.

<a id="filter"></a>

## The filter-before-escalate rule

> **If the team cannot edit the file, it does not go in the prompt.**

Never pasted: upstream Slicer, VTK, ITK or CTK source; `CMakeCache.txt`; full build logs;
DICOM pixel data; anything under `build/`.

Filter first, escalate second:

```bash
ninja 2>&1 | grep -E "error|Error" | head -40      # not the whole log
rg -n "<symbol>" app/ pipeline/ --type cpp         # not the whole tree
clang-tidy -p build app/Modules/<Module>/*.cxx     # structured, not raw
pytest --tb=line                                   # one line per failure
```

Escalate a tier only when all four hold: the filtered evidence is small, the tool output is
genuinely uninterpretable, the failing symbol is named, and two attempts at the current tier
have failed. Escalate **one tier at a time**.

<a id="fanout"></a>

## Fan-out policy

Four gates, **all four required** before spawning parallel agents:

1. The subtasks are genuinely independent.
2. The breadth is real — three or more lanes, or a search across more than twenty files.
3. A wrong answer is mechanically checkable.
4. The intermediate output is much larger than the conclusion.

Two hard overrides, regardless of the gates:

- **Never parallelise anything touching the GPU, the CPU governor, the compositor or the
  benchmark results file.** Concurrent measurement is measurement of the wrong thing.
- **Never parallelise a migration or a rename.**

| Recurring task | Verdict |
|---|---|
| Locating an API across the inherited Slicer tree | FAN-OUT |
| Multi-lens review of a large PR | FAN-OUT |
| Dependency and licence audit | FAN-OUT |
| Build error fixing | INLINE |
| Rename or refactor across modules | INLINE |
| Benchmark sweeps | INLINE, and serial |
| NFR investigation | INLINE |

**Worktree note for a CMake superbuild:** build the Slicer superbuild **once, read-only**, and
point every lane at it. That collapses most collision surfaces to a per-lane module build
directory. Keep `ccache` shared — it is content-addressed, so sharing is both safe and faster.
The non-obvious collision surfaces are the per-user Slicer settings file, ExternalProject stamp
directories, and AUTOMOC-generated export headers in a shared build tree.

<a id="compaction"></a>

## Compaction checkpoints

Compact at phase boundaries, not when the window fills. Automatic compaction at an arbitrary
point is less token-efficient and loses the wrong things.

Checkpoints: after the superbuild succeeds · after ADR-006 closes · after R0 ingest works end
to end · after the harness known-answer test passes · after R1 atlas renders · after each R2
stage lands · before and after each benchmark batch.

**Write the handoff artifact before compacting.** Update [`HANDOFF.md`](../HANDOFF.md) and any
relevant ADR first, then compact. The largest source of junk context in this project will be
Slicer superbuild logs; they should never have entered the window in the first place.

<a id="scheduled"></a>

## Scheduled local jobs

Local, not cloud. Three jobs, state in `ops/state/`, with a single-file kill switch. **No job
may commit or edit source.**

| Job | When | Produces |
|---|---|---|
| Nightly build | Overnight | Build status, compile times, a named failure if red |
| Nightly evaluation | Overnight | Golden-case metrics against committed expected values |
| Weekly audit | Weekly | Dependency, licence and `.gitignore` drift report |

**The measurement constraint carries into the schedule.** Because absolute timings are
comparable only within one capture batch, nightly performance jobs build baseline **and** HEAD
in one shared batch and report the ratio. Frame-rate figures cannot be captured on a locked
session — the runner correctly refuses — so the NFR job is split: headless metrics at night,
frame rate in an attended slot. Every absolute number that reaches the thesis comes from a
single attended sitting.

<a id="not-setup"></a>

## What is not set up yet

Stated plainly so nobody assumes a capability that does not exist.

- **Cost tracking requires a hook that the skills do not ship.** Until it is installed and
  vetted on every machine, the budget-tracking section of A1 is inert. It is also per-machine,
  not per-team, so a team total needs manual aggregation.
- **The filtering tooling is Linux-first.** The Windows machines lack `rg`, `ctags` and the
  clang tooling as configured.
- **The context-budget figures are estimates**, derived from file sizes rather than from a
  tokeniser, and the audit tools were read rather than executed.
- **The DAILY skill list is provisional.** It was derived from the predecessor repositories
  because the Slicer application repository does not exist yet. Re-run the audit after R0.
- **Removal recommendations were inferred from skill names and descriptions**, not from reading
  every skill body. Confirm before deleting.

---

**Related:** [`ai-workflow/A1-MODEL_ROUTING_AND_COST.md`](ai-workflow/A1-MODEL_ROUTING_AND_COST.md) ·
[`ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md`](ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md) ·
[`ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md`](ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md) ·
[`../CLAUDE.md`](../CLAUDE.md) ·
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md)
