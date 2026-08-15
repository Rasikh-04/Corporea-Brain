# Cost and Model-Routing Policy — Corporea-Brain FYP (Qt/C++/VTK on 3D Slicer)

Scope: 3-5 undergrad engineers, part-time, ~8 months, Fedora + Windows, Claude Code + Cowork.
Grounded only in the ECC skills/commands listed below. No tooling is invented.

## Source files actually read

Note: the paths in the brief (`.../3596fda3-.../rpm/plugin_016jTqahv5nuHriZfVWTLkrG/...`) do not exist.
The real plugin surface is mounted in the workspace at `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/`. Files read in full:

1. `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/skills/cost-aware-llm-pipeline/SKILL.md`
2. `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/skills/token-budget-advisor/SKILL.md`
3. `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/skills/cost-tracking/SKILL.md`
4. `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/commands/model-route.md`
5. `/sessions/hopeful-beautiful-edison/mnt/.remote-plugins/plugin_016jTqahv5nuHriZfVWTLkrG/commands/cost-report.md`

Project grounding: `/sessions/hopeful-beautiful-edison/mnt/Projects/BrainTwin_Native/` (`stacks/qt-vtk/{tier0,tier1}`, `harness/*.sh|*.py`, `docs/research plan/`).

---

## 1. Task-class → model-tier routing table

Tiers and their meaning come verbatim from `commands/model-route.md`:

- `haiku`: deterministic, low-risk mechanical changes
- `sonnet`: default for implementation and refactors
- `opus`: architecture, deep review, ambiguous requirements

Relative cost from `cost-aware-llm-pipeline` pricing table: Haiku 4.5 = 1x, Sonnet 4.6 = ~4x, Opus 4.5 = ~19x. Treat Opus as 19 Haiku calls before you type it.

| Task class (real workload) | Tier | Why |
|---|---|---|
| CMake / Slicer build error triage (`CMake Error at`, `undefined reference to vtk*`, `Slicer_DIR NOTFOUND`) | **haiku first, escalate to sonnet** | Most Slicer build breaks are mechanical: missing `find_package`, wrong `Slicer_DIR`, target link order. `haiku` = "deterministic, low-risk mechanical changes". Escalate to sonnet only after 2 failed haiku passes or when the error crosses >3 CMakeLists files. Never Opus. |
| Python scripted-module scaffolding (`ScriptedLoadableModule`, widget + logic + test triplet) | **haiku** | Slicer's scripted-module skeleton is templated and deterministic. Feed the template, not the docs. Sonnet only when the module needs non-trivial MRML node wiring. |
| C++ loadable-module porting (Python prototype → `qSlicer*Module` + `vtkSlicer*Logic`) | **sonnet** | This is "implementation and refactors" — the command's stated default. Involves real design (Qt parent/child ownership, VTK smart pointers, MRML observers) but the target shape is known. |
| DICOM tag heuristics (modality/series/orientation sniffing, de-identification rules) | **haiku for the tag lookups, sonnet for the rule logic** | Tag number → meaning is a lookup, not reasoning. Deciding *which* tags disambiguate a series, and failure modes on vendor-nonconformant files, is implementation logic. Split the prompt: don't pay sonnet rates for `(0008,0060)`. |
| Doc drafting (README, SETUP.md, user manual, FYP report chapters) | **haiku** | Low-risk, mechanical, high-volume, and you will rewrite it anyway. This is where a 5-person team burns budget invisibly. Hard rule: docs never go above haiku unless the doc *is* the deliverable being graded. |
| Literature summarisation (papers for the Reasoning and Research Plan) | **haiku, one paper per call** | Summarisation is not reasoning. Per-paper calls keep each input small so `select_model`-style thresholds stay in the cheap band; batching 30 papers into one prompt is exactly what pushes you over `_SONNET_ITEM_THRESHOLD = 30`. |
| Code review (C++ memory/ownership, Qt signal lifetimes) | **sonnet default, opus for the pre-submission pass** | Routine PR review is sonnet. Opus = "deep review" — buy it once per milestone on the code that gets marked, not on every branch. |
| Architecture decisions (Slicer extension vs. SlicerCustomAppTemplate fork; tier0/tier1 stack split; VTK render backend) | **opus** | Literally the command's opus case: "architecture, ambiguous requirements". These decisions are irreversible at 8-month scale — a wrong call costs more than 19x on one prompt. Cap: budget these explicitly, ~6-10 for the whole project. |
| Evaluation-harness math (FPS/frame-time percentiles, memory footprint stats, tier comparison in `harness/report.py`) | **sonnet** | Statistical correctness is high-risk (it goes in the report) but not ambiguous. Sonnet writes it; a haiku pass verifies the arithmetic against a hand-computed fixture. Do not let opus near routine stats. |

Escalation is one-way and logged. `cost-aware-llm-pipeline` best practice: "**Log model selection decisions** so you can tune thresholds based on real data."

---

## 2. Local lightweight filter before invoking Claude

The skill's own routing function keys on `text_length` and `item_count`:

```python
_SONNET_TEXT_THRESHOLD = 10_000  # chars
_SONNET_ITEM_THRESHOLD = 30      # items
```

Consequence for this team: **every character you fail to filter locally pushes you toward the 4x model.** Filtering is not hygiene, it is tier control. Reduce below 10,000 chars and you stay on haiku.

### Concrete filters

**CMake / build errors** — never paste a full Slicer build log (100k+ lines):
```bash
# Fedora / Linux
cmake --build build 2>&1 | grep -E "^(CMake )?(Error|error):" -A 4 | head -60
ninja -C build 2>&1 | grep -E "error:|undefined reference|No rule to make target" | head -40
```
```powershell
# Windows
cmake --build build --config Release 2>&1 | Select-String -Pattern "error C|error LNK|CMake Error" -Context 0,3 | Select-Object -First 40
```

**Finding the definition before asking** — cheaper than asking Claude to guess:
```bash
ctags -R --languages=C++,Python --exclude=build .
readtags -n vtkSlicerVolumeRenderingLogic          # exact file:line
rg -n --glob '!build/**' --glob '!*.png' "Slicer_DIR|find_package\(Slicer" -g CMakeLists.txt
rg -n "class qSlicer.*Module\b" --type cpp -m 20
```

**C++ static analysis** — let clang-tidy find it for free:
```bash
clang-tidy -p build src/Modules/Loadable/MyModule/*.cxx 2>&1 \
  | grep -E "warning:|error:" | cut -c1-200 | head -40
```
clang-tidy findings are deterministic; fixing them is a **haiku** task. Only unexplained findings go to sonnet.

**pytest output reduction** — for scripted modules:
```bash
pytest -q --tb=line -x 2>&1 | tail -30          # one line per failure
pytest -q --tb=short --no-header -rf 2>&1 | head -50
```
Never paste `--tb=long` for a suite. One failure, short traceback, one call.

**Log/diff size gate** before any paste:
```bash
wc -c filtered.txt   # >10000 -> filter again, do not escalate
git diff --stat && git diff -- '*.cxx' '*.h' | head -400
```

### Decision rule (escalate only when all of these hold)

1. `wc -c` of the filtered evidence is **< 10,000 chars**. If not, filter harder — do not escalate to buy context.
2. `rg` / `readtags` / `clang-tidy` returned a result you **cannot interpret**, or returned nothing where something was expected.
3. You can name the file(s) and the failing symbol. If you can't, you owe another `rg` pass, not a prompt.
4. Two haiku attempts have failed on the same error signature → escalate one tier. Never two tiers.
5. If the question is "which of these designs" rather than "why does this fail" → skip haiku, go straight to the tier in the table.

Retry discipline, per the skill: `_MAX_RETRIES = 3` with exponential backoff on transient errors only — "Never retry on authentication or validation errors". Human corollary: re-prompting the same failed question at the same tier is retrying a permanent failure. Change the evidence or change the tier.

---

## 3. Prompt caching and context reuse for a large inherited codebase

`cost-aware-llm-pipeline` mechanism:

```python
{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}},  # Cache this
{"type": "text", "text": user_input},                                            # Variable part
```

Best practice as written: "**Use prompt caching** for system prompts over 1024 tokens — saves both cost and latency."

### Never paste (this is the whole point on a Slicer fork)

- Any file under `Slicer/` upstream, `build/`, `dist/`, `__pycache__/`, or `.git/`
- Full `CMakeCache.txt`, `CMakeFiles/*.log`, `CMakeOutput.log`, `CMakeError.log`
- VTK/ITK/CTK headers — they are inherited, unmodifiable by this team, and enormous
- Full `SlicerCustomAppTemplate` boilerplate on every turn
- DICOM pixel data, or any real patient file (cost *and* ethics)
- `harness/results/**` raw run dumps — paste `harness/report.py` output, not inputs

Rule of thumb: if the team cannot edit the file, it does not belong in a prompt. Paste the *symbol*, found via ctags, not the file.

### Stable cached preamble (write once, ~1-2k tokens, keep in `CLAUDE.md`)

Summarise, do not paste:
- Which SlicerCustomAppTemplate commit/tag is forked, and the 5-10 files the team actually owns
- Module inventory: name → language → path → one-line purpose (this is the codemap; regenerate with `/update-codemaps`, not by hand)
- Build invocation for both platforms, verbatim (Fedora ninja line + Windows MSVC line)
- Naming/ownership conventions: `vtkSmartPointer` for VTK, Qt parent-child for widgets, `vtkMRMLNode` observer teardown rule
- The 3-5 recurring error signatures and their known fixes

Everything above is stable for weeks. It is exactly the "system prompt over 1024 tokens" the skill says to cache. The variable part is one filtered error + one file.

### Session hygiene

- One session per task class. A build-triage session and an architecture session must not share context — mixing them re-sends the wrong preamble at the wrong tier.
- The related skill `strategic-compact` is named in `cost-tracking`'s Related section as "Context compaction to reduce repeated token spend". Compact before a session's context turns over rather than after.

---

## 4. Budget tracking

**Command:** `/cost-report` (and `/cost-report csv` for export).
**Skill:** `cost-tracking` for ad-hoc questions ("what did this session cost?").
**Database:** `~/.claude-cost-tracker/usage.db`, table `usage`, one row per tool call / model interaction.

Preflight, exactly as the skill specifies:
```bash
command -v sqlite3 >/dev/null && echo "sqlite3 available" || echo "sqlite3 missing"
test -f ~/.claude-cost-tracker/usage.db && echo "Database found" || echo "Database not found"
```

Hard rules from the skill: "Do not estimate costs from raw token counts when `cost_usd` is present." "Do not assume the database exists without checking." "If the database is missing, do not fabricate usage data."

**Cadence**
- Daily (whoever coded that day): the one-line summary query — takes 2 seconds.
- Weekly, at team standup: full `/cost-report` — summary, by project, by tool, last 7 days.
- Monthly: `/cost-report csv` → commit to `docs/` as the budget audit trail for the FYP report.

**Metrics to watch (6)**

| Metric | Query source | Trigger |
|---|---|---|
| `today_cost` vs `yesterday_cost` | summary query | >2x jump = someone pasted a build log |
| Cost by `project` | project breakdown | any non-Corporea-Brain project outranking it = misrouted work |
| Cost by `tool_name` | tool breakdown | `Read`/`Bash` dominating = insufficient local filtering (Section 2) |
| Average cost per session | `SUM(cost_usd)/COUNT(DISTINCT session_id)` | rising trend = context not being compacted |
| 7-day cost slope | last-seven-days query | flat-to-down is the target; up two weeks running = review the routing table |
| Opus-row share | `SELECT model, SUM(cost_usd) FROM usage GROUP BY model` | opus >20% of spend = architecture questions leaking into daily work |

The `model` column is in the documented schema and in the CSV export column list, so the last metric is available without new tooling.

---

## 5. Per-task token-budget convention (from token-budget-advisor)

The skill defines four levels (25/50/75/100%) and states shortcuts are honoured immediately: "If the user already signals a level, respond at that level immediately without asking" and "If the user set a level earlier in the session, **maintain it silently**."

The team types one of three named levels at the start of a request. Named after our own workflow, mapped onto the skill's levels:

| Team keyword | Skill level | Target length (per the skill's table) | Use for |
|---|---|---|---|
| **TRIAGE** | 25% Essential — say "short version" or "25% depth" | 2-4 sentences max; direct answer, no context/examples/alternatives | Build errors, DICOM tag lookups, "which header declares X", CMake one-liners |
| **BUILD** | 50% Moderate — say "50% depth" | 1-3 paragraphs; answer + necessary context + 1 example | Scaffolding, module porting, harness math, everyday implementation |
| **DECIDE** | 75% Detailed — say "detailed answer" or "75% depth" | Structured response; multiple examples, pros/cons, alternatives | Architecture calls, tier0/tier1 tradeoffs, pre-submission code review |

100% Exhaustive is not in the team convention. If someone needs it, they say so explicitly and note it in the weekly cost review.

Since a level persists silently for the session, **the level is chosen once when the session opens** — which is why Section 3 requires one session per task class. A DECIDE-level session doing TRIAGE work is the most expensive mistake available here.

Estimation is heuristic: the skill states "no real tokenizer. Accuracy ~85-90%, variance ±15%." Treat the numbers as directional.

---

## 6. Honest limitations — what the team does not have yet

1. **The cost database almost certainly does not exist.** `cost-tracking` and `/cost-report` both require `~/.claude-cost-tracker/usage.db` to be *already populated by a separate hook or plugin*. Neither file ships that hook — `cost-tracking` says it "is intended for users who already have a cost-tracking hook or plugin writing usage rows". **Until that hook is installed on all 3-5 machines, Section 4 is inert.** Run the two preflight checks before believing any of it. The skill also cautions: "Do not recommend installing unreviewed hooks or plugins that execute arbitrary code" — so vetting that hook is a prerequisite task, not a footnote.

2. **Per-machine, not per-team.** The DB is local (`~/`). There is no aggregation across 5 laptops in anything read here. Team-level budget = 5 separate CSV exports manually combined. No shared dashboard exists.

3. **`/model-route` recommends; it does not enforce.** Its Required Output is advisory text (recommended model, confidence, why, fallback). Nothing in these files switches models automatically or blocks an expensive call. Routing compliance is a human habit backed by the weekly `model`-column check.

4. **`select_model()` is example code, not installed tooling.** The thresholds (10,000 chars / 30 items) live in a `cost-aware-llm-pipeline` code sample for applications *you build*. They do not govern Claude Code sessions. We reuse them as human heuristics only.

5. **Prompt caching in Claude Code is not directly controllable.** The `cache_control: ephemeral` mechanism shown is Messages-API-level. In Claude Code the team's lever is indirect — a stable `CLAUDE.md` preamble and disciplined session scoping. Do not promise measured cache savings in the report.

6. **Token estimates are heuristic** (~85-90%, ±15%, `words × 1.3` for prose / `chars / 4` for code). Never quote a token figure as measured.

7. **Windows gap.** The filter commands in Section 2 are Fedora-first; only the CMake one has a PowerShell equivalent here. `ctags`/`readtags`/`clang-tidy`/`rg` need installing and verifying on the Windows machines before the "filter locally first" rule is enforceable team-wide. Until then Windows devs will over-paste, and the cost data will show it.
