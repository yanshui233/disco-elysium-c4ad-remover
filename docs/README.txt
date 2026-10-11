================================================================
  Disco Elysium - ZERO PARADES Banner Remover  (C4Ad)  v1.2.0
================================================================

Removes the ZERO PARADES advert that was patched into the Disco
Elysium main menu and pause screen.

It moves the banner's UI element off-screen by rewriting one float
in  disco_Data\level2  (the RectTransform's anchoredPosition.y).
No mod loader. No DLL injection. Fully reversible.

WHY IT MOVES INSTEAD OF DISABLING
  Setting the object's "active" flag to 0 looks like the obvious
  fix, but it does NOT work: the game re-activates the object from
  code every time the menu loads, so the banner keeps showing (and
  it throws a harmless NullReferenceException). The transform is
  never touched by code, so the banner actually stays gone and the
  error goes away.


----------------------------------------------------------------
INSTALL  (Windows - no Python required)
----------------------------------------------------------------

  1. Extract this archive somewhere, e.g. your Desktop.
  2. CLOSE the game.
  3. Double-click  install.bat

That's it. The script:

  - finds your Steam or GOG install automatically (extracting this
    archive into the game folder works too, and Steam libraries on
    drives you no longer have mounted are skipped)
  - makes a backup next to the original file
  - patches the file
  - re-reads it to confirm the change

Expected output:

  [i] game : D:\Steam\steamapps\common\Disco Elysium
  [i] object  : C4Ad
  [i] offset  : 3024844  (RectTransform.m_AnchoredPosition.y)
  [i] value   : 0
  [i] state   : banner VISIBLE (original)
  [i] m_IsActive : 1   (1 = shipped value; 0 = legacy v1.0.0 patch)
  [+] backup  : ...\disco_Data\level2.c4ad-backup
  [OK] verified: C4Ad moved off-screen (y=-10000)

If the game folder is not found, drag your game folder onto
install.bat, or open a command prompt and run:

  install.bat "D:\Steam\steamapps\common\Disco Elysium"


----------------------------------------------------------------
CHECK STATUS / UNINSTALL
----------------------------------------------------------------

  verify.bat      show whether the patch is currently applied

  uninstall.bat   FULL REMOVAL - restore the original file AND
                  delete the backup this tool made, then verify.
                  One step back to how ZA/UM shipped the game.

  revert.bat      restore the original but KEEP the backup, in
                  case you want to re-apply later.

If you deleted .c4ad-backup by accident, uninstall.bat still
works: it recognises its own patch and writes the four bytes back
in place. It also fixes the m_IsActive byte if an old v1.0.0
release left it at 0. If the file is neither the original nor the
patched state, it refuses to guess and changes nothing.


----------------------------------------------------------------
AFTER A GAME UPDATE
----------------------------------------------------------------

A Steam/GOG update, or "verify integrity of game files", replaces
level2 and the banner comes back. Just run install.bat again - the
element is found by structural fingerprint rather than a fixed
offset, so it works on new builds too.


----------------------------------------------------------------
NON-WINDOWS  /  STEAM DECK
----------------------------------------------------------------

c4ad_mod.py is the same patch in Python. It needs Python 3.7+ and
nothing else (no third-party packages).

  python c4ad_mod.py scan       report state, change nothing
  python c4ad_mod.py apply      back up + patch
  python c4ad_mod.py verify     confirm it took effect
  python c4ad_mod.py revert     restore the original, keep the backup
  python c4ad_mod.py uninstall  full removal: restore + delete backup

  --game "<path>"               if auto-detection fails
  --keep-backup                 uninstall, but keep the backup file


----------------------------------------------------------------
FREQUENTLY ASKED
----------------------------------------------------------------

Does it break saves?
  No. Only a menu element's position changes. Saves live in
  %USERPROFILE%\AppData\LocalLow\ZAUM Studio\Disco Elysium

Does it touch achievements or online features?
  No. No code is modified and nothing is injected. The game has no
  anti-cheat and no online component.

I disabled "C4Ad" myself and it came back - why?
  Because the game re-activates it at runtime. That is exactly why
  this tool moves the element off-screen instead.

Does this archive contain game files?
  No. It contains no ZA/UM assets whatsoever. It only edits the
  copy already on your own machine.

Something went wrong / "RectTransform not found":
  Nothing was changed - the tool fails without writing. Your build
  either does not contain the banner or its layout changed. Report
  it with the contents of disco_Data\StreamingAssets\build_info.txt


----------------------------------------------------------------
LICENSE
----------------------------------------------------------------

MIT. See LICENSE.txt. Disco Elysium and ZERO PARADES are the
property of their respective owners.
