# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.2.0] - 2026-10-11

### Added
- **A real uninstall.** `windows/uninstall.bat`, and `python c4ad_mod.py uninstall`,
  restore the game file **and** delete the backup the tool created, then verify
  the result is the shipped original (`m_AnchoredPosition.y == 0`,
  `m_IsActive == 1`). Previously only `revert` existed, which restored the file
  but deliberately left `.c4ad-backup` behind.
- Works even when the backup is gone: if no `.c4ad-backup` exists but the file
  still carries this tool's exact patch signature, the four patched bytes are
  written back in place. No guessing — if the file is neither the original nor
  the patched state, nothing is touched and the tool says so.
- Uninstall also repairs files patched by the old **v1.0.0**: if `m_IsActive`
  is still `0` (the byte v1.0.0 flipped, which caused the `MouseOverHighlight`
  null reference), it is reset to the shipped value `1`.
- `uninstall --keep-backup` (Python) / `patch.ps1 -Action uninstall -KeepBackup`
  gives the old "restore but keep the backup" behaviour.
- `scan` / `verify` now also print the `m_IsActive` byte, so the legacy-v1.0.0
  state is visible at a glance.
- Uninstall reports any *other* `level2*backup*` files sitting next to the game
  file so nothing is silently left behind (it does not delete files it did not
  create).

### Changed
- `install.bat` now points at both `revert.bat` (restore, keep the backup) and
  `uninstall.bat` (full removal).

### Verified
- Six uninstall scenarios exercised on a synthetic install, for **both** the
  Python and the PowerShell implementation:
  patched + backup, patched without backup, legacy `m_IsActive=0` without
  backup, already-original, unknown/unrecognised state (correctly refuses,
  exit 1, file untouched), and `--keep-backup`.
  All returned the expected exit code and left the file in the expected state.
- Full round trip re-run with the Python patcher:
  `apply → apply (idempotent) → verify → uninstall → apply → uninstall`, 7/7
  steps matched the expected `(y, m_IsActive, backup-present)`. The PowerShell
  patcher was checked the same way for `apply` / `apply` / `verify` (all rc=0),
  and its uninstall ran end to end including backup removal.
- PowerShell parser check on `patch.ps1`: no syntax errors.

## [1.1.1] - 2026-10-11

### Fixed
- **The Windows installer could abort before patching on machines where Steam
  has a stale library entry.** If `libraryfolders.vdf` still lists a library on
  a drive that is not currently mounted (an unplugged external disk), the old
  `Join-Path` call threw `DriveNotFoundException`. Because the script runs with
  `$ErrorActionPreference = 'Stop'`, that single entry killed the whole scan and
  the user saw only *"Could not locate Disco Elysium automatically"* — even when
  the game was sitting right next to the script. Reported from the field.

### Changed
- Game-folder detection now tries, in order:
  1. the folder the script itself lives in, plus two levels above it (this
     covers extracting the archive into the game folder, or into a subfolder of
     it), and the current working directory;
  2. Steam libraries, with every entry validated against a currently mounted
     drive;
  3. the GOG registry hint and the usual manual paths.
- Every path probe now goes through non-throwing helpers, so a missing drive can
  never abort detection again. `c4ad_mod.py` got the same treatment
  (`_drive_mounted()` plus script-relative candidates).

### Added
- A clearer failure message when detection genuinely fails, pointing at the
  "drag the game folder onto `install.bat`" fallback.

### Verified
- Reproduced the original failure first (`Join-Path 'H:' …` on a dead drive
  threw `DriveNotFoundException`), then re-ran against the fixed code: the same
  path is skipped silently and detection carries on.
- End-to-end on a simulated install, with the tool extracted *into* the game
  folder and *one level below* it: auto-detection found it both times, and
  `scan → apply → verify → revert` passed with both patchers.

## [1.1.0] - 2026-10-11

### Fixed
- **The banner was still visible after patching.** Version 1.0.0 flipped
  `C4Ad.m_IsActive` to `0`, but the game re-activates the object from code at
  runtime, so the change had no effect on screen (and it triggered a harmless
  `NullReferenceException` in `MouseOverHighlight`).
- The fix is now a transform change instead: `RectTransform.m_AnchoredPosition.y`
  `0 → -10000`, which moves the banner off-screen. No code touches that value,
  the object graph stays intact, and the NRE is gone.

### Changed
- `c4ad_mod.py` and `windows/patch.ps1` now locate the RectTransform by
  structural fingerprint (`anchoredPosition.x == 360.198` is unique in the
  file, cross-checked against `sizeDelta`), gated behind a GameObject-layout
  validation — no hard-coded offset.
- `scan` / `verify` now report the transform state
  (`banner VISIBLE (original)` / `banner MOVED OFF-SCREEN`) instead of a byte.
- Docs rewritten to explain why `m_IsActive` cannot be used.

### Verified
- Full round-trip re-tested: `scan` → `apply` → `verify` → `revert` → `scan`,
  for both the Python and the PowerShell patcher; repeated `apply` is idempotent.
- In-game confirmation: main-menu capture with the patch applied is a **5.19**
  mean-abs-difference match to a known banner-absent reference, vs **17.99** to
  a banner-present one; `NullReferenceException` count in the session is **0**.

## [1.0.0] - 2026-10-11

### Added
- `c4ad_mod.py` — cross-platform patcher (`scan` / `apply` / `revert` / `verify`),
  Python 3 standard library only, no UnityPy dependency.
- Automatic game folder detection for Steam (registry + `libraryfolders.vdf`),
  GOG (registry + common paths) and common manual install locations, on Windows
  and Linux/Proton.
- `windows/patch.ps1` + `install.bat` / `revert.bat` / `verify.bat` — zero-dependency
  Windows installer. No Python required.
- Safety guards: auto-backup, abort if the game is running, abort on ambiguous
  matches, post-write verification.
- `alt-bepinex/` — optional BepInEx 6 (IL2CPP) plugin that destroys `C4Ad` at
  runtime, for users who want the fix to survive game updates. Source provided;
  build steps in `alt-bepinex/BUILD.md`.
- `docs/TECHNICAL.md` — full reverse-engineering write-up with the evidence chain.
- `docs/NEXUS-UPLOAD.md` — packaging and upload notes.

### Known limitations
- The BepInEx plugin is **not** compiled or runtime-tested; only the source and
  build instructions are provided.
- *(superseded by 1.1.0)* The `m_IsActive` patch was confirmed only at the file
  level and turned out not to affect the running game.
