# ADR-010 — Slicer superbuild is pinned to v5.12.3

**Status:** Accepted
**Date:** 2026-08-16
**Owner:** Lead
**Reviewers:**
**Blocks:** The Slicer superbuild ([`15-BUILD_AND_ENVIRONMENT.md`](../15-BUILD_AND_ENVIRONMENT.md#superbuild))

## Context

[`15-BUILD_AND_ENVIRONMENT.md`](../15-BUILD_AND_ENVIRONMENT.md#superbuild) has carried a
`<PINNED_REVISION>` placeholder since it was written, never filled in. SlicerCustomAppTemplate's
own default (via its `cookiecutter`/`jinja2-github` generation step) is to track Slicer's
default branch at generation time, which is exactly the moving target this project's
reproducibility stance rejects — see rule 6, provenance on every derived artifact, and the
pipeline's own `requirements.lock.txt` precedent in the same document. The superbuild has not
been attempted on any project machine yet, so this is a first pin, not a version bump.

## Options considered

| Option | Pros | Cons | Cost |
|---|---|---|---|
| **v5.12.3** | Latest stable point release; most current fixes | Least community build-troubleshooting history of the candidates | One tag |
| v5.10.0 | Previous stable line; more forum/build reports if v5.12 hits a rough edge | Older, will need a re-pin sooner | One tag |
| Track `main` (the template's own default) | Always current | Not reproducible — the exact failure mode this ADR exists to close | Unbounded |

## Decision

Pin the Slicer superbuild to **git tag `v5.12.3`** (commit
`9034c71a8fce68ab312458b3d7d16f610562263d` on `Slicer/Slicer`). This is the value written into
`<PINNED_REVISION>` in `docs/15-BUILD_AND_ENVIRONMENT.md`.

## Consequences

**Accepted costs.** If v5.12.3 hits an undocumented build failure on Fedora 44's toolchain, there
is less existing community troubleshooting for it than for v5.10.0. The known-traps table in
`docs/15-BUILD_AND_ENVIRONMENT.md` is where any new failure gets recorded, per that document's
own rule.

**What this closes.** The Slicer version is no longer an open variable. Every downstream
version — VTK, ITK, CTK, the bundled Qt — follows from this tag. SlicerCustomAppTemplate is
configured against this build, not against `main`.

**What this enables.** The superbuild can actually be started; `docs/15-BUILD_AND_ENVIRONMENT.md`
had a placeholder blocking the literal command.

## Evidence

Tag list fetched from the `Slicer/Slicer` GitHub API on 2026-08-16: `v5.12.3` is the newest
stable tag (`v5.12.2`, `v5.12.1`, `v5.12.0`, `v5.10.0` follow). SlicerCustomAppTemplate's README
confirms it has no hard version floor or ceiling of its own — it generates against whatever
`GIT_TAG` is supplied, defaulting to `main` only when none is given.

## Revisit trigger

The superbuild fails against v5.12.3 in a way the known-traps table cannot resolve within a
day of attempts, **or** a later Slicer release fixes a defect that blocks a specific project
requirement (recorded here if it happens, per the note in `docs/15-BUILD_AND_ENVIRONMENT.md`
that changing the pin is itself an ADR).
