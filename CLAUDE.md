# CLAUDE.md — BrainTwin Desktop

Read fully at the start of every session. This file is the standing contract. It is
deliberately short; depth lives in `docs/`, indexed at [`docs/00-INDEX.md`](docs/00-INDEX.md).

**Size ceiling: 120 lines.** If it grows past that, move the detail into a doc and link it.
This file is a permanent context tax on every single session — see
[`docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md`](docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md).

## What we are building

An offline neuro case workstation, built as a **custom 3D Slicer application** via
SlicerCustomAppTemplate (Qt / C++ / VTK / CTK / ITK / Python). See
[`docs/03-ARCHITECTURE.md`](docs/03-ARCHITECTURE.md) and
[ADR-003](docs/DECISIONS/ADR-003-application-shell.md).

The thesis artifact is **R2: patient mapping, disorders, and the longitudinal record.**
Everything else exists to make R2 usable and the demo compelling. R2 is hard-gated at week 22.

## The nine rules

1. **Every rung emits at least one number that lands in a results table.** A rung with no
   number is a demo feature: build it last, cheaply, and never let it eat a month.
2. **Never invent a medical, anatomical, or clinical fact.** Every clinical statement is
   either computed from data or carries a citation. No source means the literal string
   `NEEDS_SOURCE` or a `TODO(neuro-review)` marker — never a plausible-sounding guess.
3. **Region involvement is computed, never recalled.** Lesion mask intersected with the
   parcellation, with the overlap metric recorded. Literature-level patterns are labelled as
   typical patterns and cited, never presented as this patient's finding.
4. **Rank, never suppress.** The clinician's guidance is that missing a finding is far worse
   than over-flagging. Display everything, ordered by confidence. No silent filtering.
5. **Orientation is asserted, not assumed.** Every pipeline stage that touches geometry runs
   the left/right assertion against the synthetic asymmetric phantom. This is the failure
   mode that silently invalidates an entire project. See
   [`docs/06-IMAGING_PIPELINE.md`](docs/06-IMAGING_PIPELINE.md).
6. **Provenance on every derived artifact.** Source series, tool, version, parameters,
   timestamp. No provenance, no results chapter.
7. **Build the measuring instrument before the thing it measures.** The evaluation harness
   lands before the segmenter. Non-negotiable ordering.
8. **Never commit patient-derived data.** Downloader scripts only. Dataset use agreements
   forbid redistribution and a public repo is a breach. `.gitignore` discipline is a review
   item on every PR that adds a path.
9. **Prototype in Python, port on evidence.** Slicer scripted modules are fast to write;
   C++ loadable modules are fast to run. Port only what profiling proves needs it.

## Repo map

```
app/         custom Slicer application + our modules   (see docs/03)
organs/      organ manifests and assets                (see docs/04)
pipeline/    preprocessing, segmentation, batch jobs   (see docs/06)
eval/        harness, metrics, results tables          (see docs/10)
bench/       NFR benchmark, inherited from BrainTwin_Native (see docs/11)
ui/          UI bundles: tokens, stylesheet, layouts   (see docs/09)
hardware/    STLs, PLUS configs, marker sheets         (R5 only)
scripts/     dataset downloaders — never the data
docs/        everything above, specified
```

## Conventions

- **Commits:** conventional, scoped. `feat(ingest):`, `feat(attrib):`, `fix(pipeline):`,
  `docs:`, `bench:`, `adr:`.
- **Branches:** `mod/*` per module, `pipe/*` pipeline, `adr/*` decisions, `bench/*`.
- `main` is protected. One review per PR. Anything touching the data model or the organ
  module contract needs a second reviewer.
- **ADRs are mandatory** for any decision you would have to defend at viva. Template at
  [`docs/DECISIONS/ADR-000-template.md`](docs/DECISIONS/ADR-000-template.md).
- Prose style in generated documents: sentence-case headings, no em dashes, no decorative
  horizontal rules, plain text.

## Session working agreement

- **Declare a depth level at session start:** `TRIAGE`, `BUILD`, or `DECIDE`. See
  [`docs/ai-workflow/A1-MODEL_ROUTING_AND_COST.md`](docs/ai-workflow/A1-MODEL_ROUTING_AND_COST.md).
- **Never paste upstream Slicer, VTK or ITK source, `CMakeCache.txt`, full build logs, or
  DICOM pixel data into a prompt.** If the team cannot edit the file, it does not go in
  context. Filter first: `rg`, `ctags`, `clang-tidy -p build`, `pytest --tb=line`.
- **Compact at phase boundaries, not when the window fills.** Write the handoff artifact
  first. Checkpoints are listed in the A2 annex.
- Update [`HANDOFF.md`](HANDOFF.md) before ending any session that changed a decision.

## When unsure

Leave a `TODO(neuro-review)` or `NEEDS_SOURCE` marker. A blank a neurologist fills in is
correct. A confident hallucination that reaches a neurologist is the one failure this
project cannot afford.
