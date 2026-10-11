# Disco Elysium — ZERO PARADES Banner Remover

Removes the **ZERO PARADES** promotional banner that ZA/UM injected into the
Disco Elysium main menu and pause screen in the late-2025 update
(game object `C4Ad`).

No mod loader. No DLL injection. No third-party runtime. It rewrites **one
float** in one game data file, and ships nothing that belongs to ZA/UM.

[中文说明见下方](#中文说明)

---

## Why this exists

In late 2025 ZA/UM patched a `Buy ZERO PARADES` button into the main menu of a
game that had already been sold for six years, plus a promotional banner on
every `ESC` pause. The community reaction was hostile — review bombing, build
rollbacks, and a "de-ad" mod that was taken down.

This is a minimal, verifiable, fully reversible fix. It edits the game's own
file on your own disk. It does not contain or distribute any Disco Elysium
game asset.

---

## What it actually changes

| | |
|---|---|
| File | `<game>\disco_Data\level2` |
| Object | `GameObject` named `C4Ad` |
| Path in scene | `UI / Global UI Canvas / Global UI Fitter / Menu Rock-in / C4Ad` |
| Change | `RectTransform.m_AnchoredPosition.y` `0` → `-10000` |
| Effect | the banner is moved off-screen |
| Bytes touched | **4** (one `float32`); nothing is re-serialised |

### Why not just disable the object?

The obvious approach — setting the GameObject's `m_IsActive` byte to `0` —
**does not work**. The game re-activates `C4Ad` from code every time the menu
loads, so the serialised value is overwritten at runtime and the banner keeps
showing. Disabling it also makes the menu throw a (harmless but noisy)
`NullReferenceException` in `MouseOverHighlight`.

Moving the transform off-screen is not touched by any code, so it sticks. The
object graph stays fully intact, which is why there are no side effects.
See [`docs/TECHNICAL.md`](docs/TECHNICAL.md) for the full evidence chain.

---

## Requirements

- Disco Elysium (Steam / GOG), Windows 64-bit, **version that contains the banner**
- One of:
  - **Nothing else** — use the included PowerShell installer, or
  - **Python 3.7+** — use `c4ad_mod.py` (cross-platform, also fine on Steam Deck / Proton / Linux)

Close the game before installing.

---

## Install

### Windows — one click (no Python needed)

1. Download the release archive and extract it anywhere.
2. Run **`install.bat`**.
3. It finds your game automatically, creates a backup, patches the file and verifies the result.

Extracting the archive straight into your game folder works too — detection
starts from the script's own location. It also skips Steam libraries that sit
on a drive you don't have mounted any more, so a stale `libraryfolders.vdf`
entry can't stop it.

```
[i] game : D:\Steam\steamapps\common\Disco Elysium
[i] file : ...\disco_Data\level2
[i] offset  : 3024844  (RectTransform.m_AnchoredPosition.y)
[i] value   : 0
[i] state   : banner VISIBLE (original)
[i] m_IsActive : 1   (1 = shipped value; 0 = legacy v1.0.0 patch)
[+] backup  : ...\disco_Data\level2.c4ad-backup
[OK] verified: C4Ad moved off-screen (y=-10000)
```

If auto-detection fails, drag your game folder onto `install.bat`, or pass it:

```
install.bat "D:\Steam\steamapps\common\Disco Elysium"
```

Check the current state any time with `windows\verify.bat`.

### Any platform — Python

```
python c4ad_mod.py scan     # report state, change nothing
python c4ad_mod.py apply    # back up + patch
python c4ad_mod.py verify   # confirm it took effect
```

Auto-detects Steam and GOG installs. Override with `--game "<path>"`.

---

## Uninstall

Full removal restores the original file **and** deletes the backup this tool
created:

```
windows\uninstall.bat
```
or
```
python c4ad_mod.py uninstall
```

```
[+] restored original from backup: level2.c4ad-backup
[+] backup removed: level2.c4ad-backup
[OK] uninstalled: level2 is back to the original (y=0.000, m_IsActive=1)
```

You can also delete the game file and let Steam/GOG verify the files, which
downloads a fresh copy of `level2`.

### Restore but keep the backup

Use `windows\revert.bat` (or `python c4ad_mod.py revert`) if you only want the
patched file rolled back and want to keep `.c4ad-backup` around. Add
`--keep-backup` (Python) / `-KeepBackup` (PowerShell) to `uninstall` for the
same behaviour.

### If the backup is missing

`uninstall` still works. When there is no `.c4ad-backup` it detects its own
patch signature and writes the four bytes back in place, then verifies the
result is the shipped original. It also resets `m_IsActive` to `1` in case an
old v1.0.0 patch left it at `0`. If the file is neither the original nor our
patched state and no backup exists, it refuses to guess and changes nothing.

---

## After a game update

A Steam/GOG update or "verify integrity" replaces `level2` and the banner comes
back. Re-run `install.bat` — it takes a second and picks up the new file
automatically, because both the object and its transform are located by
structural fingerprint rather than by a hard-coded offset.

If you want it to survive updates without re-running anything, use the optional
[BepInEx plugin](alt-bepinex/BUILD.md) instead. Don't use both at once.

---

## FAQ

**Does this break my saves?**
No. It only moves a menu element. Saves live in
`%USERPROFILE%\AppData\LocalLow\ZAUM Studio\Disco Elysium\SaveGames`.

**Does it break achievements or multiplayer?**
No. No code is touched, nothing is injected, no network behaviour changes.

**Will this get me banned / flagged?**
There is no anti-cheat and no online component in this game. It's a few bytes in
a data file on your own disk.

**Is it just the main menu, or the pause screen too?**
`C4Ad` lives in the always-resident UI canvas and is the only promotional
object present in the game files, so moving it covers every place the banner
appears.

**I tried disabling `C4Ad` myself and it came back — why?**
Because the game re-activates it at runtime. That is exactly why this tool moves
the transform instead.

**My file size differs from 5134712 — is that okay?**
Probably. The patcher reports it and continues; the transform is found by
fingerprint, not by offset. If it says "RectTransform not found", your build
either has no banner or changed layout — open an issue with your
`build_info.txt`.

---

## Repository layout

```
c4ad_mod.py          cross-platform patcher (Python 3, standard library only)
windows/             Windows installer: patch.ps1 + install/revert/uninstall/verify .bat
alt-bepinex/         optional runtime plugin (C#) that removes C4Ad on every launch
docs/                technical write-up and Nexus upload notes
research/            the ad-hoc analysis scripts used to locate C4Ad
```

---

## License

MIT — see [LICENSE](LICENSE). Applies to the tooling in this repository only.
Disco Elysium and ZERO PARADES are property of their respective owners; this
project contains none of their assets.

## 中文说明

移除 ZA/UM 在 2025 年末更新中塞进《极乐迪斯科》主菜单与暂停界面的
**ZERO PARADES** 广告横幅（对象名 `C4Ad`）。

**原理**：改 `disco_Data\level2` 里 C4Ad 这个 UI 对象的
`RectTransform.m_AnchoredPosition.y`，把它从 `0` 改成 `-10000`，也就是
**把广告横幅移出屏幕外**。

> ⚠️ 注意：直接把对象 `m_IsActive` 改成 `0`（"禁用"）是**没用的** —— 游戏会在
> 每次进菜单时用代码把它重新激活，而且还会在 `MouseOverHighlight` 里抛一个
> 无害但烦人的空引用异常。所以本工具不碰 `m_IsActive`，只挪位置：游戏代码
> 不会覆盖这个坐标，改动永久生效，也不会产生任何报错。

无 mod loader、不注入、不重新打包，改的就是你自己硬盘上的游戏文件，本仓库
不含任何 ZA/UM 的游戏资产。

**用法（Windows，免装 Python）**：解压后双击 `windows\install.bat`，
它会自动找到游戏目录、备份、打补丁并校验。查看当前状态用 `windows\verify.bat`。
若自动定位失败，把游戏文件夹拖到 `install.bat` 上，或执行
`install.bat "D:\Steam\steamapps\common\Disco Elysium"`。

**卸载（三种粒度）**：
- `windows\uninstall.bat` —— **完整卸载**：还原原文件 + 删掉备份 + 校验，一步回到出厂状态；
- `windows\revert.bat` —— 只还原文件，保留备份（想留后路用这个）；
- 备份文件被误删也没关系：`uninstall` 会识别自己的补丁特征并把那 4 个字节原地写回，
  同时把 `m_IsActive` 复位为 `1`（修掉旧 v1.0.0 版本留下的隐患）。

**其它平台 / Steam Deck**：`python c4ad_mod.py apply`（仅需 Python 3，无第三方依赖），
`revert` 只还原保留备份，`uninstall` 完整卸载。

**注意**：游戏更新或 Steam 校验文件会把广告带回来，重新跑一次 `install.bat` 即可
（它是按对象与变换的结构特征扫描定位的，不依赖固定偏移，所以新版本也能用）。
