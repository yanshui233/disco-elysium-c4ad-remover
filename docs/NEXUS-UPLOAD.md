# Packaging and upload guide

Two things get published, and they are **not** the same archive.

| Destination | What it carries | Why |
|---|---|---|
| **Nexus Mods** | Patcher only, no game data | Nexus ToS + avoiding a DMCA. The patcher edits the copy on the user's disk. |
| **GitHub** | Full repository | Source, docs, optional plugin, issue tracker. |

## ⚠️ Do not upload `disco_Data\level2`

Shipping a patched `level2` would mean redistributing a 5 MB ZA/UM asset file.
It is both against Nexus rules and unnecessary — the patcher does the same job
locally in under a second. Everything here is deliberately asset-free.

---

## 1. Nexus Mods

### File 1 — Main file

Build a flat archive from the `windows/` folder plus the README and licence:

```
DiscoElysium_ZeroParades_AdRemover_Windows_v1.2.0.zip
├── install.bat
├── uninstall.bat      (full removal: restore + delete the backup)
├── revert.bat         (restore, keep the backup)
├── verify.bat
├── patch.ps1
├── c4ad_mod.py        (same patch, for Steam Deck / non-Windows users)
├── README.txt         (export of README.md)
└── LICENSE.txt
```

> Keep the `windows/` files at the archive root so a user who extracts into
> a folder can just double-click `install.bat`. If you prefer to preserve the
> repo layout, ship `windows\...` instead and say so in the description.

Nexus will accept `.zip`, `.7z` or `.rar`. Use **zip** for Steam Deck users.

### File 2 — Optional file

Offer the BepInEx route separately so the two never collide:

```
DiscoElysium_ZeroParades_C4Ad_BepInEx_src_v1.2.0.zip
├── C4AdRemover.cs
├── C4AdRemover.csproj
└── BUILD.md
```

Mark it **Optional** and label it clearly: *"requires BepInEx 6, source only,
you compile it yourself"*. It is not prebuilt.

### Suggested page metadata

| Field | Value |
|---|---|
| Mod name | `Zero Parades Banner Remover (C4Ad)` |
| Category | `Miscellaneous` |
| Game version | the build that contains the banner |
| Requirements | none |
| Short description | see below |

**Short description**

> Removes the ZERO PARADES advert ZA/UM patched into the main menu and pause
> screen. Moves the banner off-screen. No mod loader, no injection, fully
> reversible.

**Full description** — the block below is Markdown, kept for readability and for
the GitHub README. The Nexus description editor renders **BBCode, not Markdown**,
so for the actual upload use the ready-converted, copy-paste version in
`docs/NEXUS-DESCRIPTION-BBCode.txt` instead.

<details>
<summary>Markdown source (do not paste this into Nexus)</summary>

```markdown
## What this does

Removes the **ZERO PARADES** promotional banner that was added to the Disco
Elysium main menu and pause screen in the late-2025 update.

It moves the banner's UI element off-screen (`RectTransform.m_AnchoredPosition.y`
`0 → -10000`). Nothing is re-serialised, nothing is injected, no mod loader is
involved.

## Why not just disable the element?

Because it doesn't work — and this is the part most quick fixes get wrong. The
game **re-activates** the `C4Ad` object from code every time the menu loads, so
flipping its `m_IsActive` byte to `0` is silently ignored (and throws a harmless
`NullReferenceException`). Moving the transform is not touched by any code, so
the banner actually stays gone.

## Install (Windows, no Python needed)

1. Extract the archive anywhere.
2. Close the game.
3. Run `install.bat`.

It auto-detects Steam and GOG installs, backs up the original next to it, and
verifies the result. Extracting the archive into the game folder itself works
too — detection uses the script's own location first. If detection fails, drag
your game folder onto `install.bat`.

## Uninstall

Run `uninstall.bat` for a full removal: it restores the original file, deletes
the backup the installer created, and verifies the result is what ZA/UM shipped.
Use `revert.bat` instead if you only want to roll the patch back but keep the
backup around.

`uninstall.bat` also works if you deleted the backup — it recognises its own
patch and writes the four bytes back in place, and it repairs the `m_IsActive`
byte if an old v1.0.0 release left it at `0`. If the file is neither the original
nor the patched state, it changes nothing and tells you why. Verifying the game
files in Steam/GOG is always an option too.

## After a game update

Updates replace the file and the banner returns. Just run `install.bat` again —
the element is located by structural fingerprint, not a fixed offset, so it
keeps working on new builds.

## Technical

- File: `disco_Data\level2` (`Init.unity`, always-resident scene)
- Object: `GameObject "C4Ad"` under
  `UI / Global UI Canvas / Global UI Fitter / Menu Rock-in`
- Its component holds
  `https://store.steampowered.com/app/2863680?utm_source=disco_elysium_banner`
  — that is how it was identified
- Patch: `RectTransform.m_AnchoredPosition.y`, one `float32`, `0 → -10000`
- It is the only promotional object in the game files (checked across all
  scenes and all 1827 asset bundles), so it covers the main menu and the pause screen

Full write-up is in the GitHub repository.

## Notes

- Safe for saves, achievements and Steam Deck (use `c4ad_mod.py` there).
- This archive contains no Disco Elysium assets — it patches the copy on your
  own disk.
```

</details>

### Permissions

Suggested, pick what you're comfortable with:

- *Modification* — allow, so the method can be ported if a future update breaks it
- *Conversion / re-upload* — allow with credit
- *Assets* — this mod uses no third-party assets

---

## 2. GitHub

Push the whole repository. Before the first commit:

1. Replace `<YOUR NAME OR HANDLE>` in `LICENSE`. **Done** — it reads
   `Copyright (c) 2026 盐水 <1248102646@qq.com>`.
2. Confirm `.gitignore` is present (it blocks `*.c4ad-backup`, `bin/`, `obj/`).
3. **Never** commit a `level2` copy or a `.c4ad-backup`.

The local repository is already initialised, committed and tagged — you only
need to add the remote and push:

```bash
cd disco-elysium-c4ad-remover
git remote add origin https://github.com/<you>/disco-elysium-c4ad-remover.git
git push -u origin main
git push origin v1.2.0
```

Then create a release tagged `v1.2.0` and attach the two Nexus archives as
release assets, so both audiences are served from one place.

### Repository description / topics

> Removes the ZERO PARADES advert from Disco Elysium's main menu. Off-screen
> patch, no mod loader, fully reversible.

Topics: `disco-elysium`, `mod`, `unity`, `il2cpp`, `zero-parades`, `ad-remover`

---

## 3. Pre-upload checklist

- [x] `LICENSE` placeholder replaced with your name (`盐水 <1248102646@qq.com>`)
- [ ] `windows/patch.ps1`, `install.bat`, `uninstall.bat`, `revert.bat`, `verify.bat` at archive root
- [ ] `README` exported to `README.txt` inside the Nexus zip (Nexus does not render `.md` from archives)
- [ ] Description pasted from `docs/NEXUS-DESCRIPTION-BBCode.txt`, **not** the Markdown block (Nexus renders BBCode only)
- [ ] Uninstall requirement satisfied: `uninstall.bat` (full removal) and `revert.bat` (keep backup) both ship, and the description has an `Uninstall` section — Nexus requires mods to be cleanly removable
- [ ] No `.c4ad-backup`, no `level2`, no `bin/` or `obj/` in either archive
- [ ] Tested the zip on a clean extract: `install.bat` → run game → banner gone
- [ ] Version number consistent between archive name, `CHANGELOG.md` and the Nexus file entry
