# Minimal Public Release Design

**Date:** 2026-04-18
**Status:** Approved for spec review
**Scope:** Prepare the repository for a minimal public GitHub release without changing product behavior or doing a large refactor.

---

## Context

The repository already contains a working PyQt5 desktop application, packaging scripts, and a solid unit-test baseline. It is not yet in a shape that reads as a public open source repository because:

- the root of the repository does not explain the project to outside readers
- local machine assumptions are embedded in scripts and docs
- version information is inconsistent across code and documents
- some resources and document references are missing
- repository hygiene is mixed with local and internal artifacts

The goal is not to redesign the project. The goal is to make the current project understandable, publishable, and less coupled to one developer's environment.

---

## Goals

- Add the minimum public repository metadata required for GitHub publication
- Make the first repository visit understandable without reading internal docs
- Remove or reduce obvious personal-environment assumptions from tracked files
- Define a public test path that can run in CI
- Keep the current code structure and application behavior stable

## Non-Goals

- No large-scale code refactor
- No feature redesign or UI rewrite
- No PyPI packaging effort
- No full release engineering overhaul
- No contributor-process expansion beyond the minimal public release need

---

## Chosen Approach

Use a minimal-public-release pass instead of a broader repo restructuring pass.

This approach keeps risk low and preserves the current working repository while fixing the highest-visibility public issues:

1. Add missing public-facing root files
2. Normalize repository hygiene and version signals
3. De-localize scripts and docs enough for outside users to follow them
4. Add a small CI workflow that validates the public test baseline

This is preferred over deeper restructuring because the current request is about publication readiness, not internal architecture cleanup.

---

## Repository Shape After This Pass

### Root-level public entry

The repository root will expose:

- `README.md` as the primary public landing page
- `LICENSE` with MIT terms
- `.github/workflows/ci.yml` for a minimal public test workflow

The README will describe:

- what the project is
- what it can do
- the current platform and environment assumptions
- how to run it locally
- how tests are split between public and environment-specific tiers
- where to find the existing docs

### Documentation positioning

The existing Chinese docs remain valid project material and should stay in the repo. The public release pass should not rewrite the full docs set.

Instead:

- README becomes the public index
- user and feature docs stay in `docs/`
- internal review and phase materials stop being part of the public entry path
- obviously broken doc references should be corrected or removed from the main public narrative

### Version strategy

A single current release version will be chosen and aligned across:

- UI-visible version text
- packaging metadata
- README release status
- release notes reference

For this pass, the repository should reflect the latest documented version already present in the repo, unless code inspection shows a stronger canonical source. Based on current repo state, the expected target is `0.0.8`.

---

## Planned Change Areas

### 1. Public metadata

Add:

- `README.md`
- `LICENSE`
- `.github/workflows/ci.yml`

These files make the repo publishable and give outside users a supported path.

### 2. Repository hygiene

Adjust tracked/ignored content to remove clearly local artifacts from version control expectations.

This includes:

- ignoring local coverage output such as `.coverage`
- keeping real build source files tracked, including packaging spec files
- not treating personal tool config as public project documentation

The goal is to stop leaking machine-specific state without hiding actual project assets.

### 3. Script de-localization

Current scripts embed:

- fixed local install directories
- a fixed conda environment name
- a fixed VM host/IP

These should be changed from "project defaults" to either:

- documented examples
- overridable variables
- or explicit environment-specific notes in comments/docs

This pass does not need to fully redesign every script. It needs to make them legible and non-prescriptive for public readers.

### 4. Doc and asset consistency

Fix the highest-signal mismatches that hurt public trust:

- version text mismatch across files
- references to missing screenshots
- references to missing runtime assets
- dependency declarations that conflict with actual optional features

If an asset is genuinely required at runtime, it should either be added, made optional in code, or documented clearly.

### 5. Public CI baseline

Add a GitHub Actions workflow that runs only the stable, public test subset. It should exclude:

- GUI-only paths requiring extra local setup
- Ubuntu VM integration paths
- real-device tests

The workflow should prove that the repository has a maintainable baseline without pretending all environment-bound tests are portable.

---

## File-Level Design

### New files

- `README.md`
- `LICENSE`
- `.github/workflows/ci.yml`
- `docs/superpowers/specs/2026-04-18-minimal-public-release-design.md`

### Existing files expected to change

- `.gitignore`
- `requirements.txt`
- `run.bat`
- `run_tests.bat`
- `run_tests.ps1`
- `setup_cxfreeze.py`
- `src/ui/interfaces/home_interface.py`
- `docs/00.本程序怎么使用.md`
- possibly `src/main.py` or a small shared version/location helper if needed
- possibly docs that contain the most visible hard-coded personal environment references

### Existing files expected to remain unchanged in this pass

- core application architecture
- most feature implementation files
- integration and device test logic beyond public-facing explanation/parameter cleanup

---

## Data and Behavior Decisions

### Public run instructions

Public instructions will prefer direct Python execution and pytest commands over local workstation wrappers. Existing `run.bat` can remain, but it should stop reading like the only supported path.

### Environment-specific tests

The repository will explicitly document three test tiers:

- public unit baseline
- environment-bound integration tests
- device/E2E tests

This avoids the current ambiguity where a public reader sees many tests but cannot tell which ones are expected to pass on a generic machine.

### Optional dependencies

Dependencies tied to optional features should be labeled clearly. If a feature such as Word export depends on `python-docx`, the dependency story must no longer be confusing in the public docs.

---

## Risks and Mitigations

### Risk: cleanup breaks local internal workflows

Mitigation:

- prefer parameterization and comments over deleting internal paths outright
- keep packaging files and project scripts intact unless they are clearly incorrect

### Risk: version alignment chooses the wrong canonical number

Mitigation:

- align to the latest documented release already present in repo state
- update all visible version surfaces together in one pass

### Risk: public docs over-promise portability

Mitigation:

- state Windows focus explicitly
- state which tests require external VM/device setup
- keep CI limited to the verified public subset

---

## Testing Plan

The cleanup pass will be validated by:

- running the public unit-test subset locally
- validating the new CI command matches the local public subset
- checking that root docs and changed references resolve correctly
- confirming no obviously local/private tracked files remain part of the intended public surface

Expected validation target:

- `pytest tests/unit -q -m "not gui and not ubuntu_vm and not real_device"`

Additional checks may include quick import or file-reference validation when docs/scripts are updated.

---

## Acceptance Criteria

This pass is complete when:

- the repository has a usable public `README.md`
- the repository has an MIT `LICENSE`
- the root no longer exposes obvious personal-machine assumptions as the default story
- visible version strings are consistent
- broken top-level doc references are removed or fixed
- a minimal public CI workflow exists
- the public unit baseline still passes

---

## Out of Scope Follow-Up

After this pass, likely next steps are:

- contributor guidance
- issue and PR templates
- release packaging polish
- better screenshot and asset management
- deeper docs restructuring

Those are intentionally deferred so this publication pass stays small and reliable.
