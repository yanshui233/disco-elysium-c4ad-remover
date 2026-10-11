# alt-bepinex — optional runtime plugin

> **This is the optional route.** The main solution is `c4ad_mod.py` /
> `windows/install.bat` — a one-byte file patch that is already verified.
> Only use the plugin if you want the fix to survive game updates without
> re-running a patcher.
>
> Do not use both at the same time.

## Why only source is provided

Disco Elysium is a **Unity IL2CPP** build (`GameAssembly.dll` +
`il2cpp_data\Metadata\global-metadata.dat`). A plugin cannot reference game
types directly: BepInEx has to generate interop assemblies from
`global-metadata.dat` first, and those DLLs only appear **after the game has
been launched once**. A prebuilt plugin would be useless to anyone whose install
does not match the exact build it was compiled against.

## Build steps

1. **Install BepInEx 6 (Bleeding Edge) — Unity IL2CPP, x64.**
   Download `BepInEx-Unity.IL2CPP-win-x64-6.0.0-be.*.zip` and extract it into
   your game root, next to `disco.exe`.

2. **Launch the game once**, reach the main menu, then quit.
   This makes BepInEx generate `BepInEx\interop\*.dll` and `BepInEx\core\`.
   Check `BepInEx\LogOutput.log` to confirm the loader works.

3. **Build the plugin.**

   ```bash
   cd alt-bepinex
   dotnet build -c Release
   ```

   `GameDir` defaults to `D:\Steam\steamapps\common\Disco Elysium`. For a
   different path:

   ```bash
   dotnet build -c Release -p:GameDir="X:\...\Disco Elysium"
   ```

   On success `C4AdRemover.dll` is copied into `BepInEx\plugins\`.

4. **Launch the game.** The ZERO PARADES banner should be gone, and
   `BepInEx\LogOutput.log` should show `C4AdRemover loaded` and
   `C4Ad destroyed.`

## How it works

`AdKiller` polls `GameObject.Find("C4Ad")` every 0.5 s and destroys it. The
object lives in the always-resident `Init` scene, so a low-frequency poll is
enough and also catches the case where it gets reinstantiated.

## Known caveats

- Relies on the object name staying `C4Ad`. If ZA/UM renames it, the plugin
  silently does nothing (`c4ad_mod.py scan` will also report "not found").
- BepInEx 6 is bleeding-edge; the version number moves. Tracking
  `6.0.0-be.*` is fine.
- **Not compiled or runtime-tested.** Only the Python and PowerShell patchers
  have been verified end-to-end.
