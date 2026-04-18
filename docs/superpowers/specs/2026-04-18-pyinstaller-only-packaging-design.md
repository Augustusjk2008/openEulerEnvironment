# PyInstaller-Only Packaging Design

**Date:** 2026-04-18
**Status:** Approved for spec review
**Scope:** Consolidate the repository from two Windows packaging flows down to a single maintained PyInstaller path.

---

## Context

The repository currently keeps two parallel Windows desktop packaging workflows:

- a PyInstaller path used by the main `run.bat` commands
- a newer cx_Freeze path with separate environment bootstrap logic, wheelhouse preparation, and dedicated tests

The user has confirmed that the resulting packaged application is effectively the same in practice and wants the repository simplified to one packaging route.

Right now the dual-path setup creates unnecessary maintenance overhead:

- `run.bat` exposes two families of packaging commands
- README and project guidance must explain both paths
- build helper code and tests exist for both paths
- the cx_Freeze route requires extra Python bootstrap rules that are unrelated to the preferred day-to-day packaging flow

This work is a repository simplification task, not a packaging feature expansion.

---

## Goals

- Keep exactly one supported Windows packaging workflow
- Preserve the existing Win7-oriented PyInstaller behavior
- Remove cx_Freeze-specific maintenance surface from code, scripts, docs, and tests
- Make the supported packaging story easier to understand for maintainers and public readers

## Non-Goals

- No redesign of the PyInstaller build itself
- No change to runtime application behavior
- No attempt to add installers, MSI generation, or release automation
- No refactor of unrelated build helpers or deployment scripts

---

## Chosen Approach

Keep PyInstaller as the only supported packaging path and remove the cx_Freeze path entirely.

This is the preferred option because:

1. PyInstaller is already the primary path exposed by `run.bat`
2. the repository already contains Win7 compatibility support for the PyInstaller route
3. removing cx_Freeze eliminates an entire secondary bootstrap environment and duplicate build/test surface

This is better than keeping both systems because dual support provides little observable product value while increasing repo complexity.

---

## Repository Shape After This Pass

After the cleanup, packaging support should read as one clear story:

- `run.bat build`, `install`, `pack`, and `all` refer only to PyInstaller packaging
- packaging documentation references only PyInstaller
- helper modules and tests only cover the retained PyInstaller path

The repository should no longer contain first-class cx_Freeze entry points, requirements, or helper tests.

---

## Planned Change Areas

### 1. Packaging entry script

`run.bat` will be simplified to a single command family:

- keep `simple`
- keep `dev`
- keep `build`
- keep `install`
- keep `pack`
- keep `all`
- keep `help`

Remove:

- `cxfreeze-env`
- `cxfreeze-build`
- `cxfreeze-install`
- `cxfreeze-all`
- cx_Freeze-specific helper labels and help text
- cx_Freeze-specific environment bootstrap variables

### 2. Packaging implementation files

Delete cx_Freeze-only files:

- `setup_cxfreeze.py`
- `build_helpers/cxfreeze_config.py`
- `requirements-cxfreeze38.txt`

Retain PyInstaller files:

- `openEulerManage.spec`
- `openEulerManage.exe.spec` if still intentionally kept as a tracked packaging artifact
- `pyimod04_pywin32.py`
- `build_helpers/pyinstaller_pywin32.py`
- `build_helpers/pyi_rth_pywin32_compat.py`

### 3. Tests

Add or update a repository-surface test to assert that the public packaging story only exposes one supported packaging route.

Then remove cx_Freeze-specific unit tests:

- `tests/unit/test_cxfreeze_config.py`

Public repo hygiene checks should cover:

- no `cxfreeze-*` command names in `run.bat`
- no cx_Freeze packaging guidance in README
- no retained cx_Freeze requirements/bootstrap references in the public repo surface

### 4. Documentation and maintainer guidance

Update:

- `README.md`
- `AGENTS.md`

These files should describe:

- PyInstaller as the only maintained packaging path
- Python 3.8 as the required packaging interpreter
- Win7 compatibility considerations tied to the PyInstaller route

If any version notes or related docs mention cx_Freeze as an active supported path, they should be reviewed and either updated or left clearly as historical release notes rather than current guidance.

---

## Data and Behavior Decisions

### Supported packaging path

The only supported packaging output is the PyInstaller onedir package already produced by the existing `build` flow.

### Python version rule

The current Python 3.8 requirement for packaging remains in place because it is tied to the retained Win7-compatible PyInstaller workflow.

### Packaging source of truth

`run.bat` and the PyInstaller spec files become the operational source of truth for packaging.

README and AGENTS must match that operational path exactly.

---

## Risks and Mitigations

### Risk: deleting cx_Freeze files breaks an undocumented local workflow

Mitigation:

- keep the cleanup scoped to files that are clearly dedicated to cx_Freeze
- retain PyInstaller packaging behavior unchanged
- update maintainer docs immediately so the repository states the new single-path policy explicitly

### Risk: docs and tests drift from script behavior

Mitigation:

- add repository-surface assertions for the supported packaging story
- run targeted unit tests plus the current public unit baseline after cleanup

### Risk: spec file expectations around tracked packaging artifacts are unclear

Mitigation:

- preserve the existing PyInstaller spec artifacts already used by the repo
- only remove files whose purpose is exclusively cx_Freeze support

---

## Testing Plan

Implementation should follow a test-first sequence:

1. extend a repository-surface test with assertions that the repo no longer exposes cx_Freeze as a supported path
2. run that test and confirm it fails before implementation
3. remove cx_Freeze code, docs, and helper files
4. rerun targeted tests and the public unit baseline

Expected verification commands:

- `pytest tests/unit/test_public_release_repository.py -q`
- `pytest tests/unit -q -m "not gui and not ubuntu_vm and not real_device"`
- `rg -n "cxfreeze|cx_Freeze|requirements-cxfreeze38|setup_cxfreeze" run.bat README.md AGENTS.md tests/unit`

---

## Acceptance Criteria

This pass is complete when:

- `run.bat` exposes only the PyInstaller packaging flow
- cx_Freeze-only helper files and tests are removed
- public and maintainer docs describe only one supported packaging path
- targeted packaging-surface tests pass
- the public unit baseline still passes

---

## Out of Scope Follow-Up

After this pass, reasonable next steps could include:

- deciding whether both `openEulerManage.spec` and `openEulerManage.exe.spec` are still needed
- cleaning up historical packaging notes in release documents
- automating packaging verification in CI if Windows packaging stability becomes a priority

Those are intentionally separate from this simplification pass.
