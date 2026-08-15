# Context Budget & Session Hygiene Policy — Corporea-Brain FYP (Qt/C++/VTK on 3D Slicer)

Scope: the desktop app repo (custom 3D Slicer app), `BrainTwin_Native` benchmark harness, and the retiring `BrainTwin` / `EarTwin` web POCs.

## Sources read

ECC plugin (`.../rpm/plugin_016jTqahv5nuHriZfVWTLkrG/`):

- `skills/context-budget/SKILL.md` (5,695 B)
- `skills/strategic-compact/SKILL.md` (6,382 B)
- `skills/agent-sort/SKILL.md` (5,910 B)
- `skills/config-gc/SKILL.md` (7,930 B)
- `commands/harness-audit.md` (3,051 B) — backed by `scripts/harness-audit.js`, present

Repo evidence (shallow pass):

- `/home/rasikh/Projects/BrainTwin_Native/` — `system-definition.md`, `README.md`, `docs/research plan/FYP_Brain_Digital_Twin_Build_Plan.md`, `stacks/qt-vtk/tier1/CMakeLists.txt`, `stacks/qt-vtk/tier1/src/*` (9 `.cpp`, 8 `.h`), `harness/*.py|*.sh`, `scripts/build_tier1_assets.py`, `results/runs.csv`
- `/home/rasikh/Projects/BrainTwin/` — `CLAUDE.md` (66 lines), `backend/requirements.txt`, `backend/*.py`, `frontend/package.json`, `contract/`
- `/home/rasikh/Projects/EarTwin/` — `pytest.ini`, `backend/requirements.txt`, `frontend/package.json`, `contract/`

## Measured installed surface (why this matters)

| Surface | Count | Always-on cost |
|---|---|---|
| ECC skills | 262 (2.30 MB of SKILL.md) | name+description frontmatter = 61,750 B ≈ **15.4k tokens**, in the system prompt every turn |
| ECC agents | 64 (394 KB) | descriptions = 13,773 B ≈ **3.4k tokens**, in every Task invocation |
| ECC commands | 84 | descriptions = 10,565 B ≈ **2.6k tokens** |
| ECC rule modules | 20 languages | only `cpp`, `python`, `common` are on-stack |
| Plugin MCP (`.mcp.json`) | chrome-devtools, ~30 tools | ≈ **15k tokens** of tool schema |

**Baseline ≈ 36k tokens (~18% of a 200k window) before a single file is read.** Session-level MCP servers (Vercel, Gmail, Drive, Calendar, job search, Chrome) add ~150 more tool schemas ≈ 75k tokens if they are ever un-deferred. Keep them deferred.

---

## 1. DAILY — 15 items, each tied to a real task in these repos

| # | ECC surface | Cadence | Repo evidence / justification |
|---|---|---|---|
| 1 | `ecc:cpp-build` | per build failure | `stacks/qt-vtk/tier1/CMakeLists.txt` uses `find_package(VTK REQUIRED COMPONENTS ...)` (14 modules) + `vtk_module_autoinit`; the Slicer superbuild ahead is the project's declared first technical risk (Build Plan §2 "day or two on a new machine"). |
| 2 | `ecc:cpp-review` | per C++ PR | `src/scene.cpp`, `viewport.cpp`, `script.cpp`, `contract.h` mix Qt parent-ownership with VTK `vtkSmartPointer` lifetimes — the exact memory-safety class this reviewer covers. |
| 3 | `ecc:python-review` | per Python PR | `harness/results.py` (413 L), `report.py` (337 L), `import_results.py` (169 L) are the single writer/reader of `results/runs.csv`; `BrainTwin/backend` uses nibabel/nilearn/dipy where a silent dtype or affine error is unfalsifiable by eye. |
| 4 | `ecc:python-testing` | R2 onward | R2's graded output is Dice / HD95 / ASSD (Build Plan §1). `EarTwin/pytest.ini` + `backend/tests/` is the existing precedent; `BrainTwin_Native` currently has **zero** test files. |
| 5 | `ecc:code-explorer` (agent) | weekly | Read-only tracing of Slicer's MRML scene model and CLI/scripted/loadable module types — Build Plan §2 names "you inherit a large codebase" as the honest cost. Read-only agent = no write risk on upstream code. |
| 6 | `ecc:update-codemaps` | after each rung | Produces token-lean architecture maps so nobody re-reads the Slicer tree to answer "where does X live". Directly counters the inherited-codebase context tax. |
| 7 | `ecc:plan` | before each rung/feature | Weeks 13–22 (R2) are declared "sacred" in Build Plan §5; the WAIT-for-CONFIRM gate stops a session from burning the window on unapproved code. |
| 8 | `ecc:save-session` | end of every session | 38-week, 2-person, multi-session project. This is the only thing that survives a compaction with the *reasoning*, not just the diff. |
| 9 | `ecc:resume-session` | start of every session | Pairs with #8; replaces "re-read the repo to remember where we were", which is the largest avoidable context spend. |
| 10 | `ecc:healthcare-phi-compliance` | R0 + R2 | R0 ingests real DICOM studies from a USB stick (Build Plan §6, demo minute 2–4); `BrainTwin/CLAUDE.md` golden rule 4 already mandates `review_status: "pending"` and de-identified cases. |
| 11 | `ecc:benchmark` | per measurement run | `harness/run_tier0.sh`, `run_tier1.sh`, `run_matrix.sh`, `results/runs.csv`, `docs/03-metrics-and-test-matrix.md` are a benchmark harness already; R1 adds "render fps at target volume" as a graded metric. |
| 12 | `ecc:strategic-compact` | continuous (hook) | Install the `suggest-compact.js` PreToolUse hook. Its context-size signal (160k on a 200k window) is what prevents auto-compaction landing mid-R2. |
| 13 | `ecc:context-budget` | after any install | Run after adding any skill/agent/MCP. Section 3 below is the procedure. |
| 14 | `/harness-audit` | monthly + before each gate | Deterministic 12-category scorecard incl. **Context Efficiency** and **Cost Efficiency**; reproducible per commit, so it can be cited in the thesis methods chapter. |
| 15 | `ecc:agent-sort` | once now, re-run per rung | Produces the evidence-backed DAILY/LIBRARY install plan for the *new* Slicer repo when it is created. Re-run when the stack changes (spike → Slicer). |

Rules `cpp/` (5 files, 5,330 B), `python/` (6 files, 4,799 B), `common/` (10 files, 16,250 B) are the only rule modules to install. That is ~26 KB ≈ 6.5k tokens — acceptable. Do **not** install `react/` (31,702 B alone), `typescript/`, or the other 16.

---

## 2. LIBRARY — keep installed, do not load

Reachable by explicit name or via a `skill-library` router skill; never in the always-on catalog.

| Category | Named examples | Why kept |
|---|---|---|
| C++/CMake reference | `cpp-coding-standards`, `cpp-testing`, `docker-patterns` | Correct for the stack but reference-grade; pull when writing GoogleTest/CTest or a reproducible Slicer build image. |
| Medical domain | `healthcare-cdss-patterns`, `healthcare-emr-patterns`, `healthcare-eval-harness`, `hipaa-compliance` | Needed at the R2 disorder + longitudinal-record layer and for the ethics chapter — not weekly. |
| Retired-stack comparators | `rust-build`, `rust-review`, `rust-patterns`, `csharp-testing`, `dotnet-patterns` | `stacks/rust-wgpu/tier1` (21 `.rs` + 4 `.wgsl`) and `stacks/avalonia/tier1` (27 `.cs`) are measured rows in `runs.csv` and become a thesis chapter, but no new feature work lands there. |
| Thin web/VR viewer | `react-patterns`, `nextjs-turbopack`, `vite-patterns`, `frontend-patterns`, `react-testing` | Build Plan §7 keeps the web POC alive as a *viewer-only* VR front-end fed by Slicer exports. Off the critical path; ~1 EW total. |
| Thesis deliverables | `anthropic-skills:docx`, `pptx`, `pdf`, `xlsx` | Thesis, slide decks, results tables. `BrainTwin/CLAUDE.md` already mandates these over hand-rolling. |
| Research | `scientific-thinking-literature-review`, `scientific-db-pubmed-database`, `deep-research` | Phase 1 landscape review and the disorder-literature layer. |
| VCS / review | `git-workflow`, `pr`, `code-review`, `security-review`, `security-scan` | Two-developer branch conventions (`fe/*`, `data/*`, `contract/*`) already exist; invoke by name. |
| One-shot onboarding | `codebase-onboarding`, `repo-scan` | Run once against the Slicer tree, then never again. |
| Periodic hygiene | `config-gc` | Monthly `~/.claude` garbage collection (see §3). Not a project surface. |

### REMOVE outright

Delete these from the installed set. None have any grep evidence in the three repos, and every one costs ~230 B of always-on catalog description.

| Category to remove | Named skills | Reason |
|---|---|---|
| Logistics / freight / supply chain | `carrier-relationship-management`, `logistics-exception-management`, `returns-reverse-logistics`, `inventory-demand-planning`, `production-scheduling`, `customs-trade-compliance`, `quality-nonconformance`, `energy-procurement` | No commercial-ops surface anywhere in the project. |
| Prediction markets / trading / crypto | `prediction-market-oracle-research`, `prediction-market-risk-review`, `ito-basket-compare`, `ito-data-atlas-agent`, `ito-market-intelligence`, `ito-trade-planner`, `defi-amm-security`, `evm-token-decimals`, `nodejs-keccak256`, `llm-trading-agent-security`, `agent-payment-x402` | Zero relevance; ~11 entries of pure catalog tax. |
| Marketing / growth / social | `marketing-campaign`, `marketing-agent`, `content-engine`, `crosspost`, `social-publisher`, `social-graph-ranker`, `connections-optimizer`, `brand-voice`, `seo`, `seo-specialist`, `article-writing`, `lead-intelligence`, `investor-materials`, `investor-outreach`, `market-research`, `x-api` | An FYP has no funnel. Worst offender by count. |
| Off-stack web frameworks | `django-*` (5), `laravel-*` (4), `springboot-*` (4), `quarkus-*` (4), `fastapi-*` (2), `nestjs-patterns`, `nuxt4-patterns`, `angular-developer`, `ui-to-vue`, `tinystruct-patterns`, `jpa-patterns`, `prisma-patterns` | No `pyproject.toml` web app, no `pom.xml`, no `composer.json`. ~25 entries. |
| Mobile | `flutter-*`, `dart-flutter-patterns`, `kotlin-*` (6), `swift*` (4), `swiftui-patterns`, `ios-icon-gen`, `compose-multiplatform-patterns`, `android-clean-architecture`, `gradle-build`, `foundation-models-on-device` | No mobile target. The deliverable is a desktop binary. |
| Networking / homelab | `cisco-ios-patterns`, `network-*` (4), `homelab-*` (5), `netmiko-ssh-automation` | No infra in scope. |
| Cloud / SaaS DB / deploy | `clickhouse-io`, `redis-patterns`, `mysql-patterns`, `postgres-patterns`, `kubernetes-patterns`, `deployment-patterns`, `canary-watch`, `pm2`, `uncloud`, `database-migrations` | The demo's own selling line is "No PACS, no server, no internet" (Build Plan §6). Ships from a USB stick. |
| Business ops / comms | `customer-billing-ops`, `finance-billing-ops`, `email-ops`, `messages-ops`, `google-workspace-ops`, `jira`, `jira-integration`, `unified-notifications-ops`, `chief-of-staff` | No ticketing system, no customers. |
| Media generation | `manim-video`, `remotion-video-creation`, `video-editing`, `videodb`, `fal-ai-media`, `openclaw-persona-forge`, `algorithmic-art` | The demo video is screen-recorded, not synthesized. |
| Multi-model orchestration | `gan-*` (3), `santa-loop`, `santa-method`, `orch-*` (6), `multi-*` (5), `loop-start`, `loop-status`, `autonomous-*`, `continuous-agent-loop`, `claude-devfleet`, `team-builder`, `agentic-os`, `continuous-learning` (deprecated v1) | ~25 entries. A 2-person team under a hard week-13–22 gate cannot review the diff volume these produce, and each doubles or triples spend per task. Highest-value removal after marketing. |

**MCP servers:** disable the plugin's `chrome-devtools` (~30 tools ≈ 15k tokens) until the §7 web viewer is actually live. Do not enable Vercel / Gmail / Drive / Calendar / job-search servers in this project — leave them deferred behind tool search.

**Estimated reclaim:** ~150 of 262 skills removed ≈ 35 KB of catalog ≈ **8.8k tokens**, plus 15k from the MCP = **~24k tokens (~12% of a 200k window) recovered permanently.**

---

## 3. The audit procedure

Run from the repo root (the Slicer app repo once it exists; `BrainTwin_Native` until then).

```bash
# 1. Baseline measurement — what is loaded and what it costs
/context-budget                 # or: Skill(ecc:context-budget)
/context-budget --verbose       # only when hunting a specific offender

# 2. Deterministic scorecard, reproducible per commit
node <ECC_PLUGIN>/scripts/harness-audit.js repo --format json --root . > .claude/harness-audit.json
/harness-audit repo             # text form for humans

# 3. Decide DAILY vs LIBRARY with grep evidence, not opinion
/agent-sort                     # emits STACK / DAILY / LIBRARY / INSTALL PLAN / VERIFICATION

# 4. Apply, then re-measure
/context-budget                 # confirm the delta

# 5. Monthly, on ~/.claude (not the repo)
/config-gc                      # one [y/n/skip] per candidate, soft-delete to ~/.claude/_gc_trash/
```

`context-budget` output shape:

```
Context Budget Report
═══════════════════════════════════════
Total estimated overhead: ~36,400 tokens
Context model: 200K window
Effective available context: ~163,600 tokens (82%)

┌─────────────────┬────────┬───────────┐
│ Component       │ Count  │ Tokens    │
├─────────────────┼────────┼───────────┤
│ Agents          │ 64     │ ~3,400    │
│ Skills          │ 262    │ ~15,400   │
│ Commands        │ 84     │ ~2,600    │
│ Rules           │ 20 mod │ ~6,500    │
│ MCP tools       │ ~30    │ ~15,000   │
│ CLAUDE.md       │ 1-3    │ ~1,200    │
└─────────────────┴────────┴───────────┘

Top 3 Optimizations:
1. Remove marketing/logistics/prediction-market skill categories → ~5,000 tokens
2. Disable chrome-devtools MCP until §7 viewer exists  → ~15,000 tokens
3. Install only rules/{cpp,python,common}              → ~4,000 tokens
```

`harness-audit` returns `overall_score / max_score` over applicable categories only (the deploy-target categories 9–12 will **not** apply — there is no `vercel.json` / `netlify.toml` / `wrangler.toml` / `fly.toml` in the desktop repo), plus `applicable_categories[]`, per-category findings with exact paths, and `top_actions[]`. Use its numbers verbatim; do not rescore by hand.

Governance rule: **run steps 1 and 2 after every ECC install, plugin update, or MCP addition, and at every phase gate.** Record the two numbers (`total overhead`, `overall_score`) in `docs/` so drift is visible across the 38 weeks.

---

## 4. Compaction checkpoints by project phase

Install the `strategic-compact` PreToolUse hook first — it fires the suggestion; you decide.

```json
{"hooks":{"PreToolUse":[
  {"matcher":"Edit","hooks":[{"type":"command","command":"node ~/.claude/scripts/hooks/suggest-compact.js"}]},
  {"matcher":"Write","hooks":[{"type":"command","command":"node ~/.claude/scripts/hooks/suggest-compact.js"}]}]}}
```

Env: `COMPACT_CONTEXT_THRESHOLD=140000` (lower than the 160k default — VTK/Slicer header reads and DICOM dumps fill the window in few calls), `COMPACT_CONTEXT_INTERVAL=50000`.

| Phase boundary | Compact? | Write to disk **before** compacting | Carry across in the `/compact <message>` |
|---|---|---|---|
| **Spike (a/b/c) → ADR-003 decision** | **Yes, hard** | `docs/adr/ADR-003.md` with the scored table (time-to-first-screen, time-to-second-feature, packaging, VR path, learnability) | The winning stack and the one-sentence "what did you actually build" answer. Discard all three spike codebases from context. |
| **Slicer superbuild green → R0 start** | **Yes** | `docs/setup/<os>.md` with the exact working toolchain versions and the failing-then-fixed CMake flags | Build command + build dir path only. Superbuild logs are the single largest junk-context source in this project — never carry them. |
| **R0 ingest → R1 atlas** | **Yes** | `DATA_MODEL.md`, the sequence-classifier rules table, ingest QC results | Data model shapes and the ingest module path. Drop all DICOM header dumps and per-study traces. |
| **R1 atlas → R2 analysis** | **Yes, hard** | `docs/CODEMAPS/*` (via `/update-codemaps`), the organ-module contract, R1 fps numbers in `runs.csv` | Module contract + codemap paths. R2 is the graded rung; it must start on a near-empty window. |
| **Inside R2: eval harness → segmentation** | **Yes** | Harness code committed; a dummy-pair Dice number recorded | Metric definitions (Dice/HD95/ASSD) and the harness entry point. |
| **Inside R2: mid-implementation** | **No** | — | Losing VTK/MRML node names, file paths, and partial state costs more than the window saved. |
| **After any failed approach / dead-end debug** | **Yes** | A 5-line `known_gaps` note or ADR | Just the conclusion "X does not work because Y". |
| **R2 → R3, or a rung is cut at the gate** | **Yes, hard** | Gate decision recorded with the numbers that justified it | The decision, not the deliberation. |
| **Switching repo (Slicer app ↔ `BrainTwin_Native` harness)** | **Yes** | `/save-session` | Nothing. These are different codebases; cross-contamination is pure waste. |

Survives compaction: CLAUDE.md, TodoWrite list, memory files, git state, files on disk. Lost: intermediate reasoning, previously-read file contents, tool history, verbally-stated preferences. **Anything you would be annoyed to re-derive must be a file before you type `/compact`.**

End every working session with `/save-session`; start every one with `/resume-session`. That is the durable substitute for a long-lived window.

---

## 5. CLAUDE.md — what belongs, what does not

`BrainTwin/CLAUDE.md` at 66 lines is the right shape and should be the template. It has per-directory children (`backend/CLAUDE.md`, `frontend/CLAUDE.md`) that load only in-context — keep that pattern for the Slicer app (`Modules/<name>/CLAUDE.md`).

**Size ceiling:** root ≤ **120 lines / ~1,500 tokens**. Each sub-directory file ≤ **60 lines**. Whole CLAUDE.md chain ≤ **300 lines** — this is exactly the threshold `context-budget` flags as bloat. Enforce at review; if a section pushes past it, that section belongs in `docs/` and gets *referenced*, not inlined.

**MUST live in CLAUDE.md** (loaded every turn, so it must be things violated silently and often):

- The one-sentence contribution claim: *"The platform is Slicer. Our contribution is the ingest classifier, region-attribution engine, deficit-hypothesis layer, longitudinal record module, navigation planner, and evaluation harness."* (Build Plan §2 says to write this now.)
- Golden rules with teeth: never invent anatomical/clinical facts; region involvement comes from mask↔atlas overlap, never from model priors; `NEEDS_SOURCE` / `TODO(neuro-review)` over a confident guess; everything ships `review_status: pending`. (Verbatim-equivalent to `BrainTwin/CLAUDE.md` rules 1–4.)
- PHI handling in one line: de-identified only, never commit patient data, never paste DICOM headers into a transcript.
- Repo map: 6–10 lines, path → owner → purpose.
- Build/test/run commands: the 3–5 commands that are wrong if guessed (CMake configure line with the VTK component list, harness `run_tier1.sh` invocation, pytest entry).
- Branch/commit conventions and the contract-change PR rule.
- Fidelity-tier declaration (R0=F, R1=F/D, R2=**V**) — it is the guard against scope creep.
- A pointer, not the content: "for medical content read `docs/MEDICAL_ACCURACY.md` first".

**MUST NOT live in CLAUDE.md** (permanent per-turn tax for information needed occasionally):

- Slicer architecture explanation, MRML node taxonomy, module-type comparison → `docs/CODEMAPS/` via `/update-codemaps`.
- Dataset provenance, licences, download steps → `docs/DATA_SOURCES.md`.
- The rung specifications, timeline, kill criteria → already in `FYP_Brain_Digital_Twin_Build_Plan.md`; link only.
- Per-OS setup instructions → `docs/setup/{fedora,ubuntu,windows}.md`, already correct.
- Coding standards that duplicate `rules/cpp/` or `rules/python/` — pick one location; duplication is the #1 source of double-counted context.
- Skill usage instructions repeating a skill's own description (the catalog already carries it).
- Anything historical: changelogs, "we tried X and it failed", meeting notes, the neurologist interview transcript.
- Long prose rationale. If it needs a paragraph to justify, it is an ADR.

---

## 6. Limitations — read before trusting any number here

1. **Token figures are estimates, not measurements.** Derived as `bytes / 4` from file sizes on disk (61,750 B of skill frontmatter, 13,773 B of agent descriptions, 10,565 B of command descriptions). Real tokenization varies ±15%, and the harness may inject only a subset of the catalog. Treat the ~36k baseline as an order of magnitude.
2. **MCP schema cost is a rule of thumb.** The `~500 tokens/tool` figure comes from `context-budget`'s own heuristic, not from inspecting `chrome-devtools`' actual schemas. Verbose-mode output supersedes it.
3. **The Slicer repo does not exist yet.** Every DAILY justification for the desktop app is inferred from `FYP_Brain_Digital_Twin_Build_Plan.md` §2/§4 plus the current `stacks/qt-vtk` code. Re-run `/agent-sort` against the real repo the day it is created; some picks (e.g. `python-testing` vs `cpp-test`) will flip once the Python-scripted-vs-C++-loadable module split is decided.
4. **I did not execute the tools.** `context-budget`, `harness-audit`, `agent-sort`, and `config-gc` were read, not run. The report shapes shown are from their own documented output contracts; actual output will differ in detail, and `harness-audit.js` may fail if run outside a Node environment or against a repo layout it does not recognize.
5. **The removal list is category-level, and category membership was inferred from skill names and one-line descriptions in the catalog listing** — not from reading all 262 SKILL.md bodies. A few skills may be misfiled (e.g. `benchmark-optimization-loop` reads as orchestration but could be genuinely useful for the R1 fps work). `config-gc`'s one-at-a-time confirm loop exists precisely for this; do not bulk-delete.
6. **Shallow repo pass by design.** `node_modules`, `data/`, `target/`, `dist/`, and `.git` were excluded. `BrainTwin/data/` alone holds ~69k files; conclusions about the POCs rest on `package.json`, `requirements.txt`, `CLAUDE.md`, and directory structure only.
7. **Compaction checkpoints are a policy, not a guarantee.** The hook suggests; a human must act. If auto-compaction fires at 92% mid-R2 anyway, the recovery path is `/resume-session` plus the codemaps — which is why §4 insists the artifacts are written *before* the boundary, not at it.
8. **The 300-line CLAUDE.md ceiling is inherited from `context-budget`'s flag threshold**, not independently validated against this team's needs. If the two developers keep diverging on a convention, that convention has earned its lines; raise the ceiling deliberately rather than letting it drift.
