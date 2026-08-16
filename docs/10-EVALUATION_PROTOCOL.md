# 10 — Evaluation protocol

This is what separates an FYP from a demo, and it is where the marks are.

<a id="ordering"></a>

## The ordering rule

> **Build the measuring instrument before the thing it measures.**

The evaluation harness lands before the segmenter. Not after, not alongside. A team that
builds the segmenter first will discover in week 30 that its pipeline was broken in week 10,
and there will be no time left.

Corollary, and it is a real exercise not a slogan: **write the Chapter 4 results tables now,
with the numbers blank.** If you cannot design the empty table, you do not yet know what you
are measuring. The empty tables are in this document.

<a id="claims"></a>

## The claims, and how each is proved

| # | Claim | Method | Data | Metric | Clinician needed |
|---|---|---|---|---|---|
| **E1** | The system segments stroke and glioma lesions with performance comparable to published baselines | Held-out test split, standard metrics | ATLAS v2.0, BraTS, CT-ICH — all public | Dice, HD95, ASSD, volume error with Bland-Altman | No |
| **E2** | The system attributes lesions to anatomical regions in agreement with expert reading | Compare system region output to the radiology report or an expert annotation | 20 to 50 cases with reports | Agreement rate, Cohen's kappa, confusion by region category | **Yes** |
| **E3** | The system detects change across timepoints reliably | Longitudinal test set | OASIS-3 longitudinal, or repeated public scans | Test-retest variability, change-detection sensitivity | No |
| **E4** | The pipeline runs within stated resource limits, offline | Instrumented benchmark on the reference machine | Any | Wall time per stage, peak RAM, peak VRAM, fps, network-disabled pass/fail | No |
| **E5** | Clinicians find the output usable and useful | Task-based session, SUS, structured rubric | 5 to 8 clinicians or trainees | SUS score, task time, completion rate, rubric scores, think-aloud themes | **Yes** |
| **E6** | The structured record is faster or more complete than current practice | Comparison against the existing documentation method | Simulated or retrospective cases | Time to complete, field completeness rate | Yes, or trainees |
| **E7** | *(if local data lands)* Performance holds on local retrospective cases | External validation | 20 to 50 local de-identified cases | As E1 and E2, reported separately | Yes |

**Note the deliberate design property: E1, E3 and E4 need no clinician and no patient data.**
If every external dependency fails — ethics, hospital access, clinician availability — there
is still a defensible evaluation chapter. Preserve that property. Do not let a design change
make E1 depend on local data.

<a id="metrics"></a>

## Metric definitions and their failure modes

| Metric | What it measures | Failure mode you must handle |
|---|---|---|
| **Dice** | Volumetric overlap | **Severely misleading for small lesions.** A 2 ml acute stroke can be localised perfectly and still score badly. Always report stratified by lesion size. |
| **HD95** | 95th percentile Hausdorff distance, boundary agreement | Sensitive to a single distant false-positive component. Report alongside a connected-component count. |
| **ASSD** | Average symmetric surface distance | More stable than HD95, less intuitive. Report both. |
| **Volume error** | Absolute and relative volume difference | Report as Bland-Altman with limits of agreement, not as a mean. A mean error near zero can hide large scatter. |
| **Cohen's kappa** | Agreement beyond chance, for region attribution | Depends on the category set. Fix and document the region categories before scoring anything. |
| **ICC** | Agreement for continuous measures | State which form (1,1 / 2,1 / 3,1). Reviewers check this. |
| **Sensitivity / specificity** | Detection performance | Prevalence-dependent. Report PPV and NPV with the prevalence stated. |
| **SUS** | Perceived usability | Not diagnostic of anything specific. Pair with task time and think-aloud. |

**Stratification is mandatory for E1.** Report by lesion volume band and by disorder. An
unstratified median hides exactly the failure the examiner will ask about.

<a id="harness"></a>

## The harness as a shipped component

`eval/` is a real component with its own tests, not a notebook.

Requirements:

- Takes predictions and ground truth, emits Dice, HD95, ASSD, volume error and Bland-Altman.
- **Writes the results table automatically**, in the exact format that goes into the thesis.
  Hand-transcribing numbers into a document is how numbers drift.
- Runs from the command line, headless, against file artifacts. **It never imports the
  application**, so results are reproducible without a GUI (architecture seam 4).
- Records the model version, pipeline version, dataset version and split identifier with every
  result row. A result with no version stamp is discarded.
- Has its own unit tests, including a known-answer test: two synthetic masks with a
  hand-computed Dice, so a broken metric is caught immediately.

The known-answer test is the single highest-value test in the repository. Write it first.

<a id="datasets"></a>

## Datasets and splits

| Purpose | Dataset | Access friction | Lead time |
|---|---|---|---|
| Stroke lesion segmentation and evaluation | ATLAS v2.0; ISLES editions | Registration or challenge terms | 1 to 4 weeks |
| Glioma sub-region segmentation | BraTS current edition, BraTS-Africa | Registration, terms acceptance | 1 to 3 weeks |
| Haemorrhage on CT | PhysioNet CT-ICH | Low friction | days to 2 weeks |
| Longitudinal change | OASIS-3 | Data use agreement | 2 to 8 weeks |
| Reference and template | MNI152, the chosen parcellation, JHU white matter | Mostly open | days |
| External validation | Local retrospective de-identified cases | **Ethics plus institutional agreement plus hospital IT** | **3 to 6 months, may fail** |

Rules:

- Splits are declared once, in a committed file, by case identifier. Never re-split.
- The test split is touched once, at the end. Model selection happens on validation only.
- **Never commit the data.** Downloader scripts only. Dataset agreements forbid redistribution
  and a public repository is a breach.
- The local-data workstream starts immediately, in parallel, with a named owner, and the
  evaluation is designed so that it failing costs a bonus chapter and nothing else.
- 20 to 50 well-characterised local cases with reports is the right target. The figure of 300
  to 500 in the early notes is a research-study number, not an FYP number.

<a id="tables"></a>

## Empty results tables

Fill these. Do not redesign them late.

**Table 4.1 — Segmentation performance, by disorder and lesion size band (E1)**

| Disorder | Size band (ml) | n | Dice median [IQR] | HD95 mm median [IQR] | ASSD mm median [IQR] | Volume error ml, bias [95% LoA] |
|---|---|---|---|---|---|---|
| Ischemic stroke | < 5 | | | | | |
| Ischemic stroke | 5 to 25 | | | | | |
| Ischemic stroke | > 25 | | | | | |
| Glioma, whole tumour | all | | | | | |
| Glioma, tumour core | all | | | | | |
| Glioma, enhancing | all | | | | | |

**Table 4.2 — Region attribution agreement against expert reading (E2)**

| Region category | n cases | System-identified | Expert-identified | Both | Agreement % | Cohen's kappa |
|---|---|---|---|---|---|---|
| Frontal | | | | | | |
| Temporal | | | | | | |
| Parietal | | | | | | |
| Occipital | | | | | | |
| Deep grey | | | | | | |
| Brainstem, cerebellum | | | | | | |
| White matter tract | | | | | | |

**Table 4.3 — Longitudinal change detection (E3)**

| Measure | n pairs | Test-retest CV % | Minimum detectable change | Sensitivity to known change |
|---|---|---|---|---|
| Lesion volume | | | | |
| Involved region count | | | | |

**Table 4.4 — Resource and offline compliance (E4)**

| Stage | Wall time s, median [range] | Peak RAM MB | Peak VRAM MB |
|---|---|---|---|
| Ingest and classify | | | |
| Convert and de-identify | | | |
| Preprocess | | | |
| Parcellation | | | |
| Segmentation | | | |
| Attribution | | | |
| **End to end** | | | |

Plus: cold start s · installer size MB · sustained fps at declared volume size ·
**network-disabled full-pipeline run: PASS / FAIL**.

**Table 4.5 — Expert usefulness rubric (E5)**

Mean [SD] over n cases and m clinicians, per rubric item. The five items are the claims the
system makes about itself, so that a clinician disagreeing with one says which.

| Rubric item | n cases | m clinicians | Mean [SD] |
|---|---|---|---|
| Findings are complete | | | |
| Findings are correctly ranked | | | |
| Region attribution is defensible | | | |
| Uncertainty is communicated | | | |
| Would use in a review meeting | | | |

**Table 4.6 — Usability**

| Measure | n participants | Value |
|---|---|---|
| SUS mean [SD] | | |
| Task completion rate | | |
| Median task time | | |

<a id="attribution-protocol"></a>

## Region-attribution agreement protocol

The protocol matters more than the number, because this is the claim most open to attack.

1. **Fix the region category set before any scoring**, and commit it. Scoring at full
   parcellation granularity will produce an artificially poor kappa because experts write
   "left frontal" and the atlas says "left superior frontal gyrus". Map both to a declared
   category set and state the mapping.
2. The expert reads the case **blind to the system output**. Reversing this order invalidates
   the comparison.
3. Two experts on a subset, to obtain inter-rater agreement. **The system cannot be
   meaningfully judged against a standard whose own reliability is unknown.** If the two
   experts agree at kappa 0.6, the system agreeing at 0.55 is a very different result from what
   it looks like in isolation.
4. Disagreements are adjudicated and categorised: system missed, system over-called,
   granularity mismatch, or genuine ambiguity. The categories are as informative as the number.
5. Report the mapping, the category set, the blinding and the inter-rater figure alongside the
   result. A kappa with no protocol is not evidence.

<a id="rubric"></a>

## Expert review rubric

Six items, scored 1 to 5 per case, roughly two minutes per case. **Get sign-off on the rubric
before running it.**

1. The region attribution matched my own reading.
2. The quantification told me something I would not easily have judged by eye.
3. The uncertainty presentation was appropriate — neither falsely confident nor uselessly
   vague.
4. The longitudinal view would change how I follow this patient.
5. I would use this in clinic if it were available.
6. Free text: what is wrong with it.

Item 6 produces the quotes. Quotes are what make an evaluation chapter readable.

<a id="usability"></a>

## Usability protocol

- 5 to 8 participants, clinicians or trainees, stated as a limitation.
- Defined core task, timed, with completion recorded.
- SUS administered afterwards, unmodified — a modified SUS is not comparable to anything.
- Think-aloud during the task, recorded and coded for themes.
- NFR-05 learnability is measured here: minutes of instruction before task completion.
- **The measurement session is not a demo.** Do not help. Silence when the participant is
  stuck is data.

<a id="stats"></a>

## Statistical treatment

- Report medians and interquartile ranges for segmentation metrics. They are not normally
  distributed and a mean plus standard deviation misrepresents them.
- Report n everywhere, including in table cells.
- No significance testing without a pre-stated hypothesis and a power justification. An FYP
  with a post-hoc p-value is worse than one with none.
- Confidence intervals on agreement statistics.
- **Report failures.** Cases the pipeline could not process are part of the result, with their
  failure class from the pipeline taxonomy. Silently dropping them inflates every number in
  the table and is the easiest thing for an examiner to catch.

<a id="never"></a>

## Reporting rules, and what must never be claimed

Never claim:

- **Diagnostic accuracy.** We are not running a diagnostic accuracy study and do not have the
  design for one.
- **Improved patient outcomes.** Requires a trial.
- **Clinical readiness or regulatory status.**
- **Superiority to any commercial system.** We have not tested one and could not obtain one.

Always report:

- The fidelity tier each capability was built at, and never a claim above it.
- Every limitation found, especially the mass-effect caveat and the atlas gaps. A
  well-analysed poor result marks better than an unexplained good one.
- The operating point chosen on the sensitivity-specificity curve, and why — which follows
  from the clinical guidance that missing is worse than over-flagging.

---

**Related:** [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) ·
[`07-SRS.md`](07-SRS.md) ·
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) ·
[`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md) ·
[research plan Part 9](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-9)
