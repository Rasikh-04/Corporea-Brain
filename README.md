# BrainTwin Desktop

An open, offline-capable neuro case workstation. It ingests a patient's brain imaging study
from local media, produces quantified and anatomically localised lesion characterisation for
ischemic stroke and glioma, attributes involvement to atlas regions and white-matter tracts
with explicit uncertainty, presents literature-referenced clinical correlates as hypotheses
rather than conclusions, and maintains all of it alongside a structured longitudinal
neurological record — on a single laptop, with no PACS and no internet.

It is a decision-support and record-continuity tool. **It does not diagnose, does not plan
surgery, and is not approved for clinical use.**

## The contribution sentence

Read this before anything else, and be able to say it at viva without looking:

> The platform is 3D Slicer, as declared. Our contribution is the ingest sequence
> classifier, the region-attribution engine, the deficit-hypothesis layer, the longitudinal
> neuro record module, the trajectory planner, and the evaluation harness — none of which
> exist in Slicer or any comparable free tool.

Everything we originate is tracked in [`docs/CONTRIBUTIONS.md`](docs/CONTRIBUTIONS.md).

## Where to start

- **[`docs/00-INDEX.md`](docs/00-INDEX.md)** — the master index. Every document, every
  section, with a one-line description. Start here; grep here.
- **[`CLAUDE.md`](CLAUDE.md)** — the working contract for every session, human or agent.
- **[`docs/19-RESEARCH_BRIDGE.md`](docs/19-RESEARCH_BRIDGE.md)** — how this software
  connects to the research plan and the build plan.

## Status

Early development. No Slicer application code exists yet, which is on plan: rule 7 says build
the measuring instrument before the thing it measures, so what exists first is the orientation
assertion, the evaluation harness and the organ manifest validator. All of it is pure Python,
headless, and runs in about two seconds.

```bash
scripts/setup-env.sh          # once per machine
scripts/check-env.sh          # verify, including the assertions below
.venv/bin/python -m pytest    # 176 tests
```

Current state, and what to read next, is in [`HANDOFF.md`](HANDOFF.md). Three predecessor
efforts feed into this repository and are catalogued in
[`docs/18-POC_INHERITANCE.md`](docs/18-POC_INHERITANCE.md):

| Repository | What it was | Status |
|---|---|---|
| `~/Projects/BrainTwin` | Next.js + R3F + Niivue brain POC with disorder mapping | Superseded as product; retained as reference and possible VR viewer |
| `~/Projects/EarTwin` | Next.js ear POC with a two-tier data model and derived disorder rules | Separate deliverable; contributes patterns, not code |
| `~/Projects/BrainTwin_Native` | Qt+VTK vs Rust+wgpu vs Avalonia benchmark harness | Stack question closed (Qt). Harness repurposed as the NFR benchmark |

## Licence

Project code Apache-2.0. Third-party components, datasets, atlases and clinical instruments
carry their own terms — see [`docs/13-LEGAL_AND_ETHICS.md`](docs/13-LEGAL_AND_ETHICS.md).
No patient-derived data is ever committed to this repository.
