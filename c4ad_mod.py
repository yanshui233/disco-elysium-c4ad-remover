#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Disco Elysium - ZERO PARADES (C4Ad) menu banner remover
=======================================================

Removes the ZERO PARADES promotional banner that ZA/UM added to the
Disco Elysium main menu / pause screen in the late-2025 update.

WHAT THE BANNER IS
------------------
It is a plain UI GameObject named "C4Ad", living in the always-resident
startup scene shipped as `disco_Data/level2`.  Its hierarchy is

    UI / Global UI Canvas / Global UI Fitter / Menu Rock-in / C4Ad

and its MonoBehaviours carry these links, which is how it was identified:

    https://store.steampowered.com/app/2863680?utm_source=disco_elysium_banner
    https://tr.ee/G3AE7E35q4
    https://tr.ee/wciWi2tlXc

(Steam app 2863680 = ZERO PARADES: For Dead Spies)

WHY THE OBVIOUS FIX DOES NOT WORK
---------------------------------
The natural idea is to set the GameObject's `m_IsActive` byte to 0.  It
does not work: the game re-activates C4Ad from code at runtime, so the
serialised value is simply overwritten every time the menu loads.
(Worse, disabling it while the game still expects it live throws a
harmless-but-noisy NullReferenceException in MouseOverHighlight.)

WHAT THIS TOOL DOES INSTEAD
---------------------------
It moves the banner off-screen by rewriting the RectTransform's
`m_AnchoredPosition.y`.  The runtime never touches this value, so the
banner stays gone and the object graph stays fully intact (no NRE).

    RectTransform.m_AnchoredPosition.y : 0  ->  -10000

Nothing is re-serialised; exactly one float (4 bytes) changes.

The position is located structurally, not by a hardcoded offset:

  1. find the GameObject's serialised name field  <int32 4> "C4Ad"
  2. walk backwards to confirm the GameObject layout (component count,
     layer) actually matches, so we never touch a coincidental string
  3. find the one RectTransform whose anchoredPosition / sizeDelta
     match the banner's known transform, and rewrite its .y

REQUIREMENTS
------------
Python 3.7+ and nothing else.  No third-party packages.

USAGE
-----
    python c4ad_mod.py scan       # report current state, change nothing
    python c4ad_mod.py apply      # back up the file, then patch it
    python c4ad_mod.py revert     # restore the untouched original (keep backup)
    python c4ad_mod.py uninstall  # full removal: restore + delete the backup
    python c4ad_mod.py verify     # re-scan and confirm the patch took effect

    --game <path>   game root folder (the one containing disco.exe / disco_Data)
                    auto-detected from Steam / GOG when omitted.

    uninstall
    ---------
    Puts the game back exactly as ZA/UM shipped it and removes every file this
    tool created:

      1. if the backup `<level2>.c4ad-backup` exists -> restore from it;
      2. otherwise, if the file still carries our exact patch signature, the
         four patched bytes are written back in place (no backup needed);
      3. the backup is then deleted, and the result is verified to be the
         pristine original (m_AnchoredPosition.y == 0, m_IsActive == 1).

    Use `--keep-backup` to restore without deleting the backup (that is exactly
    what `revert` does).

Tested on: Windows, Steam build, Unity 2020.3.12f1, level2 size 5134712.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import sys

LEVEL_REL = os.path.join("disco_Data", "level2")
TARGET_NAME = "C4Ad"
BACKUP_SUFFIX = ".c4ad-backup"
EXE_NAMES = ("disco.exe", "Disco Elysium.exe")
__version__ = "1.2.0"

# Serialised name field of the C4Ad GameObject:  <int32 4> "C4Ad"
NAME_ANCHOR = struct.pack("<i", len(TARGET_NAME)) + TARGET_NAME.encode("ascii")

# Known transform of the C4Ad RectTransform in the shipped build.  Used only
# as a *structural* fingerprint to pick the right object -- not as an offset.
RT_ANCHORED_X = 360.198
RT_SIZE_DELTA = (462.79, 308.5207)   # x, y

OFFSCREEN_Y = -10000.0               # where we move the banner
KNOWN_SIZE = 5134712

# GameObject layout, little-endian, 4-byte aligned:
#   int32 m_Component count
#   ComponentPair[]        (12 bytes each: int32 fileID + int64 pathID)
#   int32 m_Layer
#   int32 m_Name length + UTF-8 bytes (padded to 4)
#   uint16 m_Tag
#   uint8  m_IsActive
# The name field is preceded by its own length, i.e. our anchor.  Walking
# backwards we can recompute where the object starts and validate it.


# --------------------------------------------------------------------------- #
# game folder discovery
# --------------------------------------------------------------------------- #

def _valid_game_dir(path):
    if not path or not os.path.isdir(path):
        return False
    return os.path.isfile(os.path.join(path, *LEVEL_REL.split(os.sep))) or any(
        os.path.isfile(os.path.join(path, exe)) for exe in EXE_NAMES
    )


def _drive_mounted(path):
    """Is the drive letter in `path` currently available?

    A stale Steam library entry can point at a drive that is no longer present
    (unplugged external disk).  Probing such a path is pointless and noisy, so
    those entries are dropped before they become candidates.
    """
    if not path:
        return False
    if sys.platform != "win32":
        return True
    drive, _ = os.path.splitdrive(path)
    return bool(drive) and os.path.isdir(drive + os.sep)


def _steam_libraries_windows():
    libs = []
    try:
        import winreg  # noqa: WPS433
    except ImportError:
        return libs
    steam_root = None
    for hive, key, value in (
        (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
    ):
        try:
            with winreg.OpenKey(hive, key) as k:
                steam_root = winreg.QueryValueEx(k, value)[0]
                break
        except OSError:
            continue
    if not steam_root:
        return libs
    if _drive_mounted(steam_root):
        libs.append(steam_root)
    vdf = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
    if os.path.isfile(vdf):
        try:
            with open(vdf, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            text = ""
        for line in text.splitlines():
            line = line.strip()
            if line.lower().startswith('"path"'):
                parts = line.split('"')
                if len(parts) >= 4:
                    lib = parts[3].replace("\\\\", "\\")
                    # Skip libraries on drives that are not mounted right now.
                    if lib and _drive_mounted(lib):
                        libs.append(lib)
    return libs


def _gog_hints_windows():
    hints = []
    try:
        import winreg  # noqa: WPS433
    except ImportError:
        return hints
    for hive, root in (
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\GOG.com\Games"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GOG.com\Games"),
    ):
        try:
            with winreg.OpenKey(hive, root) as k:
                for i in range(winreg.QueryInfoKey(k)[0]):
                    sub = winreg.EnumKey(k, i)
                    try:
                        with winreg.OpenKey(k, sub) as sk:
                            name = winreg.QueryValueEx(sk, "gameName")[0]
                            path = winreg.QueryValueEx(sk, "path")[0]
                            if "disco" in str(name).lower():
                                hints.append(path)
                    except OSError:
                        continue
        except OSError:
            continue
    return hints


def detect_game_dir():
    """Best-effort auto-detection. Returns a path or None."""
    env = os.environ.get("DISCO_ELYSIUM_DIR")
    if _valid_game_dir(env):
        return env

    candidates = []

    # Where this script itself lives: users frequently extract the tool straight
    # into the game folder (or one level below it), which is the strongest hint
    # and keeps working when Steam detection fails.  _valid_game_dir() rejects
    # every folder that is not actually a Disco Elysium install, so walking up
    # a couple of levels is safe.
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:                      # __file__ missing (frozen / -c)
        here = os.getcwd()
    up = here
    for _ in range(3):
        candidates.append(up)
        parent = os.path.dirname(up)
        if parent == up:
            break
        up = parent
    candidates.append(os.getcwd())

    if sys.platform == "win32":
        for root in _steam_libraries_windows():
            candidates.append(os.path.join(root, "steamapps", "common", "Disco Elysium"))
        candidates += _gog_hints_windows()
        candidates += [
            r"C:\Program Files (x86)\GOG Galaxy\Games\Disco Elysium",
            r"C:\Program Files\GOG Galaxy\Games\Disco Elysium",
            r"C:\GOG Games\Disco Elysium",
            r"D:\GOG Games\Disco Elysium",
            r"D:\Steam\steamapps\common\Disco Elysium",
            r"E:\Steam\steamapps\common\Disco Elysium",
            r"C:\Steam\steamapps\common\Disco Elysium",
        ]
    else:
        home = os.path.expanduser("~")
        candidates += [
            os.path.join(home, ".steam", "steam", "steamapps", "common", "Disco Elysium"),
            os.path.join(home, ".local", "share", "Steam", "steamapps", "common", "Disco Elysium"),
            os.path.join(home, ".steam", "debian-installation", "steamapps", "common", "Disco Elysium"),
            os.path.join(home, "GOG Games", "Disco Elysium"),
        ]

    seen = set()
    for cand in candidates:
        if not cand:
            continue
        norm = os.path.normcase(os.path.normpath(cand))
        if norm in seen:
            continue
        seen.add(norm)
        if _valid_game_dir(cand):
            return cand
    return None


# --------------------------------------------------------------------------- #
# structural location of the C4Ad RectTransform
# --------------------------------------------------------------------------- #

def _validate_gameobject(blob, name_off):
    """Return (object_start, component_count) if `name_off` really is a
    GameObject's m_Name field, else (None, None)."""
    if name_off < 4:
        return None, None
    # int32 m_Layer sits immediately before the name-length field
    layer = struct.unpack_from("<i", blob, name_off - 4)[0]
    if layer < 0 or layer > 63:
        return None, None
    for count in range(1, 65):
        start = name_off - 8 - 12 * count
        if start < 0:
            break
        if struct.unpack_from("<i", blob, start)[0] == count:
            return start, count
    return None, None


def _find_rect_offset(blob):
    """Return the file offset of C4Ad's RectTransform.m_AnchoredPosition.y."""
    # Primary fingerprint: the banner's anchoredPosition.x is unique in the file.
    needle = struct.pack("<f", RT_ANCHORED_X)
    start = 0
    while True:
        k = blob.find(needle, start)
        if k < 0:
            break
        start = k + 1
        if k + 16 > len(blob):
            continue
        y = struct.unpack_from("<f", blob, k + 4)[0]
        sx, sy = struct.unpack_from("<2f", blob, k + 8)
        y_ok = abs(y) < 1e-3 or abs(y - OFFSCREEN_Y) < 1.0
        size_ok = abs(sx - RT_SIZE_DELTA[0]) < 0.5 and abs(sy - RT_SIZE_DELTA[1]) < 0.5
        if y_ok and size_ok:
            return k + 4

    # Fallback fingerprint: the sizeDelta pair alone.
    needle = struct.pack("<2f", *RT_SIZE_DELTA)
    k = blob.find(needle)
    if k >= 8:
        y = struct.unpack_from("<f", blob, k - 4)[0]
        if abs(y) < 1e-3 or abs(y - OFFSCREEN_Y) < 1.0:
            return k - 4
    return None


def _isactive_offset(blob, name_off):
    """File offset of the GameObject's `m_IsActive` byte, or None.

    Layout after the name-length int32 at `name_off`:
        int32 length | name bytes padded to 4 | uint16 m_Tag | uint8 m_IsActive
    """
    if name_off is None or name_off + 4 > len(blob):
        return None
    name_len = struct.unpack_from("<i", blob, name_off)[0]
    if name_len < 0 or name_len > 255:
        return None
    padded = name_len + ((4 - name_len % 4) % 4)
    off = name_off + 4 + padded + 2
    if off >= len(blob) or blob[off] > 1:
        return None
    return off


def locate(blob, allow_multiple=False):
    """Return (offset_of_anchored_y, info_dict) or (None, reason)."""
    anchors = []
    start = 0
    while True:
        i = blob.find(NAME_ANCHOR, start)
        if i < 0:
            break
        anchors.append(i)
        start = i + 1
    if not anchors:
        return None, "GameObject '%s' not found" % TARGET_NAME

    valid = [a for a in anchors if _validate_gameobject(blob, a)[0] is not None]
    if not valid:
        return None, "GameObject '%s' found but its layout did not validate" % TARGET_NAME
    if len(valid) > 1 and not allow_multiple:
        return None, ("ambiguous: %d GameObject matches" % len(valid))

    off = _find_rect_offset(blob)
    if off is None:
        return None, ("RectTransform of '%s' not found "
                      "(transform fingerprint mismatch)" % TARGET_NAME)

    go_start, count = _validate_gameobject(blob, valid[0])
    info = {
        "name_offset": valid[0],
        "object_offset": go_start,
        "components": count,
        "anchored_y_offset": off,
        "is_active_offset": _isactive_offset(blob, valid[0]),
    }
    return off, info


def backup_path(level_path):
    return level_path + BACKUP_SUFFIX


def game_running():
    if sys.platform != "win32":
        return False
    try:
        import subprocess
        # keep it as bytes: the console code page is not always UTF-8
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq disco.exe"],
            capture_output=True, timeout=10,
        ).stdout or b""
        return b"disco.exe" in out.lower()
    except Exception:
        return False


def _state_of(y):
    if abs(y - OFFSCREEN_Y) < 1.0:
        return "banner MOVED OFF-SCREEN (patch active)"
    if abs(y) < 1e-3:
        return "banner VISIBLE (original)"
    return "unexpected value %.3f (unknown build?)" % y


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def _resolve_paths(args):
    game = args.game or detect_game_dir()
    if not game:
        sys.exit(
            "[x] Could not find the game folder automatically.\n"
            "    Pass it explicitly, e.g.\n"
            '        python c4ad_mod.py scan --game "D:\\Steam\\steamapps\\common\\Disco Elysium"'
        )
    game = os.path.abspath(game)
    level = os.path.join(game, *LEVEL_REL.split(os.sep))
    if not os.path.isfile(level):
        sys.exit("[x] Missing file: %s" % level)
    return game, level


def cmd_scan(args):
    game, level = _resolve_paths(args)
    blob = open(level, "rb").read()
    off, info = locate(blob, args.force)
    print("[i] game    : %s" % game)
    print("[i] file    : %s  (%d bytes)" % (level, len(blob)))
    if off is None:
        print("[!] %s" % info)
        print("    Either this build never had the banner, or the file layout changed.")
        return 1
    y = struct.unpack_from("<f", blob, off)[0]
    iso = info.get("is_active_offset")
    print("[i] object  : %s   (GameObject @ %d, %d components)"
          % (TARGET_NAME, info["object_offset"], info["components"]))
    print("[i] offset  : %d  (RectTransform.m_AnchoredPosition.y)" % off)
    print("[i] value   : %.3f  -> %s" % (y, _state_of(y)))
    print("[i] m_IsActive : %s   (1 = shipped value; 0 = legacy v1.0.0 patch)"
          % ("?" if iso is None else blob[iso]))
    return 0


def cmd_apply(args):
    game, level = _resolve_paths(args)
    if game_running():
        sys.exit("[x] disco.exe is running. Close the game first, then retry.")
    blob = bytearray(open(level, "rb").read())
    off, info = locate(bytes(blob), args.force)
    if off is None:
        sys.exit("[!] %s -- nothing changed." % info)

    y = struct.unpack_from("<f", blob, off)[0]
    if abs(y - OFFSCREEN_Y) < 1.0:
        print("[=] Already patched, nothing to do.")
        return 0

    bak = backup_path(level)
    if not os.path.isfile(bak):
        shutil.copy2(level, bak)
        print("[+] backup  : %s" % bak)
    else:
        print("[i] backup  : reusing existing %s" % bak)

    struct.pack_into("<f", blob, off, OFFSCREEN_Y)
    tmp = level + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(blob)
    os.replace(tmp, level)
    print("[+] patched : offset %d  y %.3f -> %.1f" % (off, y, OFFSCREEN_Y))

    off2, info2 = locate(open(level, "rb").read(), args.force)
    if off2 is None or abs(struct.unpack_from("<f", open(level, "rb").read(), off2)[0]
                           - OFFSCREEN_Y) > 1.0:
        sys.exit("[x] verification FAILED -- run 'revert' now.")
    print("[OK] verified: %s moved off-screen (y=%.1f)" % (TARGET_NAME, OFFSCREEN_Y))
    return 0


def cmd_revert(args):
    game, level = _resolve_paths(args)
    bak = backup_path(level)
    if not os.path.isfile(bak):
        sys.exit("[x] No backup at %s -- cannot revert." % bak)
    if game_running():
        sys.exit("[x] disco.exe is running. Close the game first, then retry.")
    shutil.copy2(bak, level)
    print("[+] restored original from backup.")
    blob = open(level, "rb").read()
    off, info = locate(blob, True)
    if off is None:
        print("[i] %s" % info)
        return 0
    y = struct.unpack_from("<f", blob, off)[0]
    print("[i] %s.m_AnchoredPosition.y = %.3f  (%s)" % (TARGET_NAME, y, _state_of(y)))
    return 0


def cmd_uninstall(args):
    """Full removal: restore the original file and delete what we created."""
    game, level = _resolve_paths(args)
    bak = backup_path(level)

    if game_running():
        sys.exit("[x] disco.exe is running. Close the game first, then retry.")

    blob = open(level, "rb").read()
    off, info = locate(blob, True)
    if off is None:
        sys.exit("[!] %s -- nothing changed." % info)
    y = struct.unpack_from("<f", blob, off)[0]
    print("[i] game    : %s" % game)
    print("[i] file    : %s  (%d bytes)" % (level, len(blob)))
    print("[i] value   : %.3f  -> %s" % (y, _state_of(y)))

    if os.path.isfile(bak):
        shutil.copy2(bak, level)
        print("[+] restored original from backup: %s" % os.path.basename(bak))
    elif abs(y) < 1e-3:
        print("[=] file is already the original (y=0); no restore needed.")
    else:
        # No backup, but the file still carries our signature: writing the four
        # bytes back is exact, because that is the only thing we ever change.
        if abs(y - OFFSCREEN_Y) >= 1.0:
            sys.exit("[x] File is neither the original nor our patched state "
                     "(y=%.3f) and no backup exists -- refusing to guess." % y)
        blob2 = bytearray(blob)
        struct.pack_into("<f", blob2, off, 0.0)
        _atomic_write(level, blob2)
        print("[+] no backup found -- un-patched in place: y %.1f -> 0.0" % y)

    # Belt and braces: an old v1.0.0 patch may have left m_IsActive at 0
    # (harmless at runtime, but noisy).  Force it back to the shipped value.
    blob3 = bytearray(open(level, "rb").read())
    off3, info3 = locate(bytes(blob3), True)
    if off3 is not None:
        iso = info3.get("is_active_offset")
        if iso is not None and blob3[iso] != 1:
            blob3[iso] = 1
            _atomic_write(level, blob3)
            print("[+] m_IsActive reset to 1 (repairs an old v1.0.0 patch)")
    final = open(level, "rb").read()
    off2, info2 = locate(final, True)
    if off2 is None:
        sys.exit("[x] verification FAILED after uninstall -- restore manually.")
    y2 = struct.unpack_from("<f", final, off2)[0]
    act2 = final[info2["is_active_offset"]] if info2.get("is_active_offset") is not None else 1
    if abs(y2) > 1e-3 or act2 != 1:
        sys.exit("[x] verification FAILED: y=%.3f m_IsActive=%d" % (y2, act2))

    if os.path.isfile(bak) and not args.keep_backup:
        os.remove(bak)
        print("[+] backup removed: %s" % os.path.basename(bak))
    elif os.path.isfile(bak):
        print("[i] backup kept (--keep-backup): %s" % os.path.basename(bak))

    print("[OK] uninstalled: level2 is back to the original (y=0.000, m_IsActive=1)")
    for extra in _sibling_backups(level):
        print("[i] note: unrelated backup still present: %s (you may delete it)"
              % os.path.basename(extra))
    return 0


def _sibling_backups(level):
    """Other `level2*backup*` files next to the game file (informational)."""
    folder = os.path.dirname(level)
    base = os.path.basename(level)
    ours = base + BACKUP_SUFFIX
    out = []
    try:
        for name in sorted(os.listdir(folder)):
            if name == ours:
                continue
            low = name.lower()
            if low.startswith(base.lower()) and "backup" in low:
                out.append(os.path.join(folder, name))
    except OSError:
        pass
    return out


def _atomic_write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def cmd_verify(args):
    game, level = _resolve_paths(args)
    blob = open(level, "rb").read()
    off, info = locate(blob, args.force)
    print("[i] file    : %s  (%d bytes)" % (level, len(blob)))
    print("[i] expected size for known builds: %d" % KNOWN_SIZE)
    if off is None:
        print("[!] %s" % info)
        return 1
    y = struct.unpack_from("<f", blob, off)[0]
    print("[i] offset  : %d" % off)
    print("[i] value   : %.3f" % y)
    if abs(y - OFFSCREEN_Y) < 1.0:
        print("[OK] banner is moved off-screen (ad removed).")
        return 0
    print("[!] banner is STILL on screen.")
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Disco Elysium -- ZERO PARADES (C4Ad) banner remover  v%s"
                    % __version__,
    )
    ap.add_argument("action", choices=["scan", "apply", "revert", "uninstall", "verify"])
    ap.add_argument("--game", default=None, help="game root folder (contains disco_Data)")
    ap.add_argument("--force", action="store_true",
                    help="proceed even if several C4Ad-like matches are found")
    ap.add_argument("--keep-backup", dest="keep_backup", action="store_true",
                    help="uninstall: restore the file but keep the backup")
    args = ap.parse_args(argv)
    return {
        "scan": cmd_scan, "apply": cmd_apply,
        "revert": cmd_revert, "uninstall": cmd_uninstall,
        "verify": cmd_verify,
    }[args.action](args)


if __name__ == "__main__":
    sys.exit(main())
