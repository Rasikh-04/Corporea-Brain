# 17 — Release and packaging

Unglamorous, examinable, and cheap if designed in. Expensive if retrofitted.

<a id="artifacts"></a>

## Release artifacts

| Artifact | Platform | Contents |
|---|---|---|
| Installer | Linux, Windows | Application, curated module set, default UI bundle, atlas assets, organ manifests |
| Model bundle | Both | Segmentation and parcellation weights, fetched separately, licence-permitting |
| Dataset downloader | Both | Scripts only. **Never the data.** |
| Evaluation bundle | Both | Harness, declared splits, results tables. Runs without the application. |
| Demo build | Both | Application plus a curated public case set plus the presentation UI bundle |
| Documentation | Both | This set, as shipped |

<a id="versioning"></a>

## Versioning

`MAJOR.MINOR.PATCH`, plus a build stamp carrying the commit sha.

Version is displayed in the About dialog and **written into every export and every derived
artifact.** A result that cannot be traced to an application version is not admissible in the
results chapter.

Additionally versioned independently, because they change on different clocks:

- Pipeline version. Bumped when any stage's behaviour changes.
- Data model `schema_version`.
- Organ manifest `schema_version`.
- UI bundle `schema_version`.
- Model versions, per model.

An export carries all of them. This is what makes the reproducibility claim checkable rather
than asserted.

<a id="contents"></a>

## What goes in the installer, and what never does

**In:** application binaries, curated modules, default UI bundle, atlas meshes and
parcellation label maps that are licence-clean for redistribution, organ manifests, the
disclaimer, `ATTRIBUTIONS.md`, and the deficit-hypothesis mapping table with its citations.

**Never in, under any circumstances:**

- Any patient-derived data, including public dataset samples. Dataset agreements forbid
  redistribution and derived data is still derived from the data.
- Model weights whose licence forbids redistribution. Those are fetched separately, and the
  installer states which ones and from where.
- Credentials, keys or tokens of any kind.
- Test fixtures containing real identifiers.
- Development tooling, build artifacts or symbol files beyond what a crash report needs.

The pre-publication audit checklist in [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) runs
against the built installer, not only against the repository.

<a id="offline-gate"></a>

## Offline verification as a release gate

"Works from a DICOM folder on a USB stick, on a laptop, with no PACS and no internet" is the
headline claim for the target setting. **A headline claim is tested deliberately.**

The gate: on a clean machine, network disabled at the OS level, install from the installer,
cold start, import a study from removable media, run the full pipeline to attribution, export a
report. Any outbound connection attempt fails the release, detected at packet level.

This runs on a machine that has never had the development environment installed, because a
development machine has every dependency already and will pass a test the target machine
fails. The benchmark work already established this pattern with its evaluator bundle for a
machine with no compiler and no SDK; reuse it.

<a id="platforms"></a>

## Per-platform packaging

| Platform | Format | Notes |
|---|---|---|
| Linux | The format the Slicer build produces, plus a tarball | Verify on a distribution that is not the build machine's |
| Windows | NSIS installer | Verify on a machine with no Visual Studio and no runtime pre-installed. This is where missing redistributables surface. |

Both are produced by the same build from the same source, per NFR-12. A platform that requires
a source change to build is a defect, not a variant.

<a id="signing"></a>

## Signing, honestly

We do not have a code-signing certificate and are not going to buy one for a final year
project.

Consequences, stated plainly rather than discovered by a clinician:

- Windows will show an unknown-publisher warning. The installation instructions say so, in
  advance, and explain what the user is seeing.
- Checksums are published for every artifact, and the instructions tell the user how to verify
  them. That is the honest substitute and it is better than silence.
- The report names this as a limitation of the deployment, not of the software.

<a id="update"></a>

## Update strategy

**No automatic update. No update check. No outbound connection, ever.** This follows directly
from the network posture in
[`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md).

Updates are a new installer, installed deliberately. On install, the application:

1. Detects an existing record store and its `schema_version`.
2. **Writes a verified backup before any migration.**
3. Runs forward-only migrations, tested against a golden fixture store.
4. Refuses to open a store with a schema newer than it understands. It never opens it
   read-only-and-hope, which is how data gets silently truncated.

<a id="rollback"></a>

## Rollback

Reinstall the previous version and restore the pre-migration backup. That is the whole
mechanism, and it works because the backup is mandatory and verified.

A migration that cannot be rolled back this way does not ship. If a schema change is genuinely
one-way, it is an ADR, not a commit.

<a id="checklist"></a>

## Release checklist

Every line is a hard gate.

- [ ] All CI green, including the nightly golden-case regression
- [ ] Orientation assertion passing
- [ ] Metric known-answer test passing
- [ ] PHI-in-logs assertion passing
- [ ] UI bundle lint passing for every shipped bundle
- [ ] Offline test passing on a clean machine
- [ ] Performance gate within the declared ratio, with the `batch_id` recorded
- [ ] Pre-publication audit checklist complete against the built installer
- [ ] `ATTRIBUTIONS.md` regenerated and matching the licence registers
- [ ] Disclaimer verified in application, README and a generated export
- [ ] Migration tested from the previous release's fixture store, including the backup step
- [ ] Checksums published
- [ ] Install verified on a machine with no development environment
- [ ] `HANDOFF.md` and `CONTRIBUTIONS.md` current

<a id="demo"></a>

## The demo build

A separate configuration, not a separate codebase.

Differences: the presentation UI bundle, a curated public case set with pre-warmed caches so
nothing takes ninety seconds on stage, and teaching mode enabled.

Two rules:

1. **The demo build makes no claim the release build cannot make.** Same numbers, same
   uncertainty, same disclaimer. A demo that shows something the product does not do is the
   fastest way to lose a viva.
2. **Rehearse end to end at least three times before the day**, on the actual machine, with the
   actual projector. The twelve-minute script has a centre of gravity in the middle — the
   analysis and timeline beats — and rehearsal is what protects it when the demo runs long.

---

**Related:** [`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) ·
[`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md) ·
[`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md)
