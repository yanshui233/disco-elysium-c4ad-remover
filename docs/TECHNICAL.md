# Technical notes — locating and removing `C4Ad`

Everything here was measured on a real install. No step is inferred.

## 1. Target environment

| | |
|---|---|
| Game root | `D:\Steam\steamapps\common\Disco Elysium` |
| Steam appid / build | `632470` / buildid `23980936` |
| Backend | Unity **2020.3.12f1**, **IL2CPP** — `GameAssembly.dll` + `disco_Data\il2cpp_data\Metadata\global-metadata.dat` |
| Scene table | `disco_Data\globalgamemanagers` → `level2 = Init.unity`, `level3 = Lobby.unity` |

`level2` is the `Init` scene: it is loaded at startup and stays resident, which
is why a menu object lives there rather than in `Lobby`. Note that the scene is
shipped **inline** as `disco_Data/level2` (a raw serialised file, version 22) —
the 1827 Addressables bundles under `aa/StandaloneWindows64/` contain **no**
`Scenes/` entries, so nothing about `C4Ad` can come from a bundle.

## 2. How the object was found

1. **Strings pass.** `grep -a` over `disco_Data\level*`, `*.assets` and
   `globalgamemanagers` for `C4Ad`, `2863680`, `MAIN_MENU_C4` produced hits in
   `level2` only.
2. The hit is a `MonoBehaviour` whose serialised fields contain:

```
https://store.steampowered.com/app/2863680?utm_source=disco_elysium_banner
https://tr.ee/G3AE7E35q4
https://tr.ee/wciWi2tlXc
```

`app/2863680` is *ZERO PARADES: For Dead Spies*; `utm_source=disco_elysium_banner`
is the campaign tag, i.e. this is the banner itself.

3. **Hierarchy walk** (via `Transform.m_Father` / `m_Children`):

```
UI
└─ Global UI Canvas
   └─ Global UI Fitter
      └─ Menu Rock-in
         └─ C4Ad                <-- the banner root
            └─ (Text)  localization key: MAIN_MENU_C4_TAGLINE
```

4. **It is the only promotional object.** A full scan of all 31682 objects in
   `level2`, of every `level*` scene, and of all 1827 Addressables bundles found
   no second copy — so removing it covers both the main menu and the pause
   screen. There is exactly one `C4Ad`.

## 3. Why disabling the object does NOT work (and what does)

The natural patch is to set the GameObject's `m_IsActive` byte to `0`. That was
tried first and **it fails in practice**: after patching the byte and starting a
fresh game session, the banner was still on screen.

Two things were established from that:

- The game **re-activates `C4Ad` from code at runtime**, overwriting the
  serialised `m_IsActive` value each time the menu loads.
- Disabling the object while the rest of the menu still expects it live also
  produces a `NullReferenceException` in `MouseOverHighlight.RefreshHighlightMaterials()`
  (one per session, non-fatal, no crash dump).

The fix that actually works is to leave the object alive but **move it
off-screen**, by rewriting its RectTransform's `m_AnchoredPosition.y`. No code
touches that value, the object graph is untouched, and the NRE disappears.

This was confirmed visually: with the coordinate patch applied the banner is
gone from the menu; with the file restored to pristine the banner is back and
the NRE returns.

## 4. The patch: one float

`level2` is 5,134,712 bytes. `C4Ad`'s `GameObject` object data starts at file
offset **1,527,664**, and its `RectTransform` object starts at **3,024,744**
(8-byte aligned, as Unity requires).

`RectTransform` is serialised with its `m_AnchoredPosition` (a `Vector2`) at
object-relative offset **+96**:

| field | object offset |
|---|---|
| `m_GameObject` (PPtr) | 0 |
| `m_LocalRotation` (`Quaternion`) | 12 |
| `m_LocalPosition` (`Vector3`) | 28 |
| `m_LocalScale` (`Vector3`) | 40 |
| `m_Children` / anchors | … |
| **`m_AnchoredPosition` (`Vector2`)** | **96** (x) / **100** (y) |
| `m_SizeDelta` (`Vector2`) | 104 |

```
file offset 3024844  ( = 3024744 + 100 )
float32   0.0  ->  -10000.0
```

Nothing is re-serialised; the file length does not change. The banner sits at
`anchoredPosition = (360.198, 0)` inside a fixed-size screen canvas, so pushing
`.y` to `-10000` places it far outside the visible area.

### Verification performed

```
cmp -l level2.c4ad-backup level2
→ the only differing bytes are the four that make up the single float
```

The banner's `anchoredPosition.x` (`360.198`) and `sizeDelta` (`(462.79, 308.5207)`)
are unchanged, i.e. only `.y` moved.

In-game confirmation (window capture of the main menu, before/after):

| shot | mean abs. difference vs. reference | meaning |
|---|---|---|
| patched build | **5.19** to the "banner gone" reference | matches banner-absent |
| patched build | 17.99 to the "banner present" reference | clearly differs |
| `NullReferenceException` count | **0** | the old NRE is gone |

## 5. Why the tool does not hard-code the offset

Hard-coded offsets break the moment ZA/UM ships a new build. Instead the
patcher locates the target structurally:

1. **The GameObject.** The serialised name field is preceded by its own length,
   so

   ```
   04 00 00 00  43 34 41 64      ==  <int32 4>  "C4Ad"
   ```

   is a self-validating anchor and appears exactly once in `level2`.

2. **Layout validation.** Walking backwards from the anchor, the patcher
   recomputes where the GameObject object must start and checks that the
   `int32` there really is the component count (6 for `C4Ad`) and that the
   `m_Layer` value before the name is sane. A coincidental string can't pass
   this.

3. **The transform.** `C4Ad`'s `RectTransform` is then found by fingerprint:
   its `anchoredPosition.x` value (`360.198`) is **unique in the whole file**,
   and the patcher additionally checks that the following `float`s look like
   the banner's `sizeDelta`. Only then does it rewrite `.y`.

If more than one candidate ever appears, the patcher refuses to act and prints
the offsets rather than guessing.

## 6. Reproducing the analysis

The scripts used live in [`../research/`](../research/). The relevant ones:

```
research/pure_scan.py     — the byte-anchor scan, no dependencies
research/t4.py            — find objects containing "2863680"
research/t6.py, t9.py     — walk the GameObject hierarchy
research/t10.py           — read C4Ad's components / activation state
research/scan_scenes.py   — map levelN to scene names
```

They need `UnityPy` (`pip install UnityPy`). `pure_scan.py` needs nothing.

## 7. Doing it by hand

If you would rather verify than trust the tooling:

```python
import struct
data = bytearray(open(r"...\disco_Data\level2", "rb").read())

# 1) confirm the object exists
i = data.find(b"\x04\x00\x00\x00C4Ad")
assert i == 1527744, i

# 2) the transform: anchoredPosition.x == 360.198 is unique in the file
k = data.find(struct.pack("<f", 360.198))
print(hex(k), struct.unpack_from("<2f", data, k))        # (360.198, 0.0)

# 3) move it off-screen
struct.pack_into("<f", data, k + 4, -10000.0)
open(r"...\disco_Data\level2", "wb").write(data)
```

## 8. Limitations

- The BepInEx plugin in `alt-bepinex/` is **unbuilt and untested**. Only the
  Python and PowerShell patchers are verified.
- If a future build renames `C4Ad`, moves it into an Addressables bundle, or
  changes its transform, the fingerprint will not match and the tool will report
  "not found" and make no changes. It fails safely.
- The `m_AnchoredPosition.x = 360.198` fingerprint is specific to the shipped
  build. If ZA/UM repositions the banner, the analysis has to be redone (the
  tool will say so rather than patch the wrong thing).
