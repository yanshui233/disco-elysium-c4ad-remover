#requires -version 5.1
<#
    Disco Elysium - ZERO PARADES (C4Ad) banner remover  --  Windows patcher
    ---------------------------------------------------------------------
    Removes the ZERO PARADES promo banner from the main menu / pause screen.

    Pure PowerShell, no Python and no third-party tools required.

    v1.2.0 -- adds a real `uninstall` action: restores the original file and
              removes the backup this tool created, then verifies the result.
              With no backup present it rewrites the four patched bytes in
              place, so removal works even if the backup was lost or deleted.

    v1.1.1 -- game-folder detection is far more forgiving now:
              * the script's own location (and its parents) are tried first, so
                extracting the archive into the game folder always works;
              * Steam libraries sitting on a drive that is not currently
                mounted are skipped instead of aborting the scan -- a stale
                libraryfolders.vdf entry used to throw DriveNotFoundException.

    The banner is a UI GameObject named "C4Ad" inside <game>\disco_Data\level2.

    Setting its m_IsActive byte to 0 does NOT work: the game re-activates the
    object from code each time the menu loads.  Disabling it also triggers a
    harmless NullReferenceException in MouseOverHighlight.

    Instead we move the banner off-screen by rewriting its RectTransform's
    m_AnchoredPosition.y.  The runtime never touches that value, and the
    object graph stays intact (no NRE).

        RectTransform.m_AnchoredPosition.y : 0  ->  -10000

    The transform is located structurally (its anchoredPosition.x is unique in
    the file and its sizeDelta matches), so no hardcoded file offset is used.

    Usage:
        patch.ps1 -Action scan
        patch.ps1 -Action apply
        patch.ps1 -Action revert
        patch.ps1 -Action uninstall
        patch.ps1 -Action verify
        patch.ps1 -Action apply -GameDir "D:\Steam\steamapps\common\Disco Elysium"

    uninstall fully removes the mod: it restores <level2> from the backup (or,
    when no backup exists, writes the four patched bytes back in place), deletes
    the backup, and verifies the file is the shipped original again.  Pass
    -KeepBackup to restore without deleting the backup (same as revert).
#>

[CmdletBinding()]
param(
    [ValidateSet('scan', 'apply', 'revert', 'uninstall', 'verify')]
    [string]$Action = 'apply',

    [string]$GameDir = '',

    [switch]$KeepBackup
)

$ErrorActionPreference = 'Stop'

$LevelRel     = Join-Path 'disco_Data' 'level2'
$TargetName   = 'C4Ad'
$BackupSuffix = '.c4ad-backup'
$KnownSize    = 5134712

$RT_ANCHORED_X = [single]360.198
$RT_SIZE_X     = [single]462.79
$RT_SIZE_Y     = [single]308.5207
$OFFSCREEN_Y   = [single](-10000.0)

function Write-Line($text, $color) {
    if ($color) { Write-Host $text -ForegroundColor $color } else { Write-Host $text }
}

# --- safe path helpers ------------------------------------------------------
# Test-Path / Join-Path THROW when a drive letter does not exist -- for example
# a stale Steam library entry left behind in libraryfolders.vdf by an external
# disk that is no longer plugged in.  Since this script runs with
# $ErrorActionPreference = 'Stop', one such entry used to abort the whole
# detection and the patch never ran.  These wrappers never throw.
function Test-DirSafe([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $false }
    try { return [bool](Test-Path -LiteralPath $p -PathType Container -ErrorAction SilentlyContinue) }
    catch { return $false }
}

function Test-FileSafe([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $false }
    try { return [bool](Test-Path -LiteralPath $p -PathType Leaf -ErrorAction SilentlyContinue) }
    catch { return $false }
}

# [System.IO.Path]::Combine only concatenates strings -- it never probes a
# drive, so it cannot fail on a missing one.  "H:" is normalised to "H:\" so
# the result is absolute and not drive-relative.
function Join-PathSafe([string]$base, [string]$leaf) {
    if ([string]::IsNullOrWhiteSpace($base)) { return $null }
    $b = $base.Trim()
    if ($b -match '^[A-Za-z]:$') { $b += '\' }
    return [System.IO.Path]::Combine($b, $leaf)
}

function Get-LevelPath($dir) {
    return (Join-PathSafe $dir $LevelRel)
}

function Test-GameDir($dir) {
    if (-not (Test-DirSafe $dir)) { return $false }
    return (Test-FileSafe (Join-PathSafe $dir $LevelRel)) -or
           (Test-FileSafe (Join-PathSafe $dir 'disco.exe'))
}

function Get-SteamLibraries {
    $libs = New-Object System.Collections.Generic.List[string]
    $root = $null
    foreach ($probe in @(
        @{ Hive = 'HKCU:\Software\Valve\Steam';     Prop = 'SteamPath' },
        @{ Hive = 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam'; Prop = 'InstallPath' }
    )) {
        try {
            $v = (Get-ItemProperty -Path $probe.Hive -Name $probe.Prop -ErrorAction Stop).($probe.Prop)
            if ($v) { $root = $v; break }
        } catch { }
    }
    if (-not $root) { return $libs }
    if (Test-DirSafe $root) { $libs.Add($root) }
    $vdf = Join-PathSafe $root 'steamapps\libraryfolders.vdf'
    if (Test-FileSafe $vdf) {
        foreach ($line in @(Get-Content -LiteralPath $vdf -ErrorAction SilentlyContinue)) {
            if ($line -match '^\s*"path"\s+"(.+?)"') {
                $lib = ($matches[1] -replace '\\\\', '\').Trim()
                if ($lib -match '^[A-Za-z]:$') { $lib += '\' }
                # Drop libraries whose drive is not currently mounted (unplugged
                # external disk, removed partition, ...).  Otherwise the later
                # Join-Path throws DriveNotFoundException and kills the scan.
                if ($lib -and (Test-DirSafe $lib)) { $libs.Add($lib) }
            }
        }
    }
    return $libs
}

function Get-GogHint {
    foreach ($hive in @(
        'HKLM:\SOFTWARE\WOW6432Node\GOG.com\Games',
        'HKLM:\SOFTWARE\GOG.com\Games'
    )) {
        if (-not (Test-Path -LiteralPath $hive)) { continue }
        foreach ($sub in (Get-ChildItem -LiteralPath $hive -ErrorAction SilentlyContinue)) {
            $p = Get-ItemProperty -LiteralPath $sub.PSPath -ErrorAction SilentlyContinue
            if ($p -and $p.gameName -and $p.gameName -match 'disco' -and $p.path) {
                return $p.path
            }
        }
    }
    return $null
}

function Find-GameDir {
    if (Test-GameDir $script:GameDir) {
        $r = Resolve-Path -LiteralPath $script:GameDir -ErrorAction SilentlyContinue
        return $(if ($r) { $r.Path } else { $script:GameDir })
    }

    if ($env:DISCO_ELYSIUM_DIR -and (Test-GameDir $env:DISCO_ELYSIUM_DIR)) {
        return $env:DISCO_ELYSIUM_DIR
    }

    $candidates = New-Object System.Collections.Generic.List[string]

    # 1. Where this script itself lives.  Plenty of people extract the archive
    #    straight into the game folder (this is exactly what happened in the
    #    field report), so the script's own location is the strongest hint --
    #    and it still works when Steam detection fails completely.
    $here = $PSScriptRoot
    if ($here) {
        $candidates.Add($here)
        $up = $here
        foreach ($_ in 1..2) {
            $up = Split-Path -Parent $up
            if (-not $up) { break }
            $candidates.Add($up)
        }
    }
    $cwd = (Get-Location).Path
    if ($cwd) { $candidates.Add($cwd) }

    # 2. Steam libraries.  Every entry is already drive-validated and every
    #    join below is non-throwing, so one dead library cannot break this.
    foreach ($lib in (Get-SteamLibraries)) {
        $p = Join-PathSafe $lib 'steamapps\common\Disco Elysium'
        if ($p) { $candidates.Add($p) }
    }

    # 3. GOG installs.
    $gog = Get-GogHint
    if ($gog) { $candidates.Add($gog) }
    foreach ($c in @(
        'C:\Program Files (x86)\GOG Galaxy\Games\Disco Elysium',
        'C:\Program Files\GOG Galaxy\Games\Disco Elysium',
        'C:\GOG Games\Disco Elysium',
        'D:\GOG Games\Disco Elysium',
        'C:\Steam\steamapps\common\Disco Elysium',
        'D:\Steam\steamapps\common\Disco Elysium',
        'E:\Steam\steamapps\common\Disco Elysium'
    )) { $candidates.Add($c) }

    $seen = New-Object System.Collections.Generic.HashSet[string]
    foreach ($c in $candidates) {
        if ([string]::IsNullOrWhiteSpace($c)) { continue }
        if (-not $seen.Add($c.ToLowerInvariant())) { continue }
        if (-not (Test-GameDir $c)) { continue }
        $r = Resolve-Path -LiteralPath $c -ErrorAction SilentlyContinue
        return $(if ($r) { $r.Path } else { $c })
    }
    return $null
}

# Byte-exact 1:1 mapping: byte 0xNN becomes char U+00NN, so string indices
# are file offsets.
function Get-Latin1String([byte[]]$bytes) {
    return [System.Text.Encoding]::GetEncoding(28591).GetString($bytes)
}

# Locate C4Ad's RectTransform.m_AnchoredPosition.y.  Returns the file offset,
# or -1 when not found.  The banner's anchoredPosition.x is unique in the file;
# the following floats are checked to confirm we really found the transform.
function Get-TargetOffset([byte[]]$bytes) {
    $needleBytes = [System.BitConverter]::GetBytes($RT_ANCHORED_X)
    $text   = Get-Latin1String $bytes
    $needle = Get-Latin1String $needleBytes

    $start = 0
    while ($start -lt $text.Length) {
        $i = $text.IndexOf($needle, $start, [System.StringComparison]::Ordinal)
        if ($i -lt 0) { break }
        $start = $i + 1
        if ($i + 16 -gt $bytes.Length) { continue }

        $y  = [System.BitConverter]::ToSingle($bytes, $i + 4)
        $sx = [System.BitConverter]::ToSingle($bytes, $i + 8)
        $sy = [System.BitConverter]::ToSingle($bytes, $i + 12)

        $yOk = ([Math]::Abs($y) -lt 0.001) -or ([Math]::Abs($y - $OFFSCREEN_Y) -lt 1.0)
        $sizeOk = ([Math]::Abs($sx - $RT_SIZE_X) -lt 0.5) -and ([Math]::Abs($sy - $RT_SIZE_Y) -lt 0.5)
        if ($yOk -and $sizeOk) {
            return $i + 4
        }
    }

    # Fallback: sizeDelta pair alone.
    $needle2 = New-Object byte[] 8
    [Array]::Copy([System.BitConverter]::GetBytes($RT_SIZE_X), 0, $needle2, 0, 4)
    [Array]::Copy([System.BitConverter]::GetBytes($RT_SIZE_Y), 0, $needle2, 4, 4)
    $t2 = Get-Latin1String $needle2
    $j = $text.IndexOf($t2, [System.StringComparison]::Ordinal)
    if ($j -ge 8) {
        $y2 = [System.BitConverter]::ToSingle($bytes, $j - 4)
        if (([Math]::Abs($y2) -lt 0.001) -or ([Math]::Abs($y2 - $OFFSCREEN_Y) -lt 1.0)) {
            return $j - 4
        }
    }
    return -1
}

# File offset of the GameObject's m_IsActive byte, or -1.
# Layout after the name-length int32: name bytes padded to 4, uint16 m_Tag,
# uint8 m_IsActive.
function Get-IsActiveOffset([byte[]]$bytes) {
    $name  = [System.Text.Encoding]::ASCII.GetBytes($TargetName)
    $lenB  = [System.BitConverter]::GetBytes([int]$name.Length)
    $needle = Get-Latin1String ([byte[]]($lenB + $name))
    $text  = Get-Latin1String $bytes

    $start = 0
    while ($start -lt $text.Length) {
        $i = $text.IndexOf($needle, $start, [System.StringComparison]::Ordinal)
        if ($i -lt 0) { break }
        $start = $i + 1
        $padded = $name.Length + ((4 - ($name.Length % 4)) % 4)
        $iso = $i + 4 + $padded + 2
        if ($iso -ge $bytes.Length) { continue }
        if ($bytes[$iso] -le 1) { return $iso }
    }
    return -1
}

function Get-StateText([single]$y) {
    if ([Math]::Abs($y - $OFFSCREEN_Y) -lt 1.0) { return 'banner MOVED OFF-SCREEN (patch active)' }
    if ([Math]::Abs($y) -lt 0.001)              { return 'banner VISIBLE (original)' }
    return ('unexpected value {0} (unknown build?)' -f $y)
}

function Test-GameRunning {
    try {
        return $null -ne (Get-Process -Name 'disco' -ErrorAction SilentlyContinue)
    } catch { return $false }
}

function Invoke-Action {
    $dir = Find-GameDir
    if (-not $dir) {
        Write-Line '[x] Could not locate Disco Elysium automatically.' 'Red'
        Write-Line '    Pass the folder manually, e.g.:' 'Yellow'
        Write-Line '    patch.ps1 -Action apply -GameDir "D:\Steam\steamapps\common\Disco Elysium"' 'Yellow'
        Write-Line '    ...or drag the game folder onto install.bat.' 'Yellow'
        return 1
    }
    $level = Get-LevelPath $dir
    if (-not (Test-FileSafe $level)) {
        Write-Line ("[x] Missing file: {0}" -f $level) 'Red'
        return 1
    }

    Write-Line ("[i] game : {0}" -f $dir)
    Write-Line ("[i] file : {0}" -f $level)

    $bytes = [System.IO.File]::ReadAllBytes($level)
    $off   = Get-TargetOffset $bytes

    if ($off -lt 0) {
        Write-Line ("[!] '{0}' RectTransform not found." -f $TargetName) 'Yellow'
        Write-Line '    This build may not contain the banner, or its layout changed.' 'Yellow'
        return 1
    }

    $y = [System.BitConverter]::ToSingle($bytes, $off)
    Write-Line ("[i] object  : {0}" -f $TargetName)
    Write-Line ("[i] offset  : {0}  (RectTransform.m_AnchoredPosition.y)" -f $off)
    Write-Line ("[i] value   : {0}" -f $y)
    Write-Line ("[i] state   : {0}" -f (Get-StateText $y))
    $iso = Get-IsActiveOffset $bytes
    if ($iso -ge 0) {
        Write-Line ("[i] m_IsActive : {0}   (1 = shipped value; 0 = legacy v1.0.0 patch)" -f $bytes[$iso])
    }

    if ($bytes.Length -ne $KnownSize) {
        Write-Line ("[!] file size {0} differs from known build {1} - continuing anyway." -f $bytes.Length, $KnownSize) 'Yellow'
    }

    switch ($Action) {
        'scan' {
            return 0
        }
        'verify' {
            if ([Math]::Abs($y - $OFFSCREEN_Y) -lt 1.0) { Write-Line '[OK] banner is moved off-screen (ad removed).' 'Green'; return 0 }
            Write-Line '[!] banner is STILL on screen.' 'Red'
            return 1
        }
        'apply' {
            if ([Math]::Abs($y - $OFFSCREEN_Y) -lt 1.0) { Write-Line '[=] Already patched, nothing to do.' 'Green'; return 0 }
            if (Test-GameRunning) {
                Write-Line '[x] disco.exe is running. Close the game first, then retry.' 'Red'
                return 1
            }
            $bak = $level + $BackupSuffix
            if (-not (Test-Path -LiteralPath $bak -PathType Leaf)) {
                Copy-Item -LiteralPath $level -Destination $bak -Force
                Write-Line ("[+] backup  : {0}" -f $bak) 'Green'
            } else {
                Write-Line ("[i] backup  : reusing existing {0}" -f $bak)
            }
            $new = [System.BitConverter]::GetBytes($OFFSCREEN_Y)
            [Array]::Copy($new, 0, $bytes, $off, 4)
            [System.IO.File]::WriteAllBytes($level, $bytes)

            $after = [System.IO.File]::ReadAllBytes($level)
            $off2  = Get-TargetOffset $after
            if ($off2 -lt 0 -or [Math]::Abs([System.BitConverter]::ToSingle($after, $off2) - $OFFSCREEN_Y) -ge 1.0) {
                Write-Line '[x] verification FAILED - run revert now.' 'Red'
                return 1
            }
            Write-Line ("[OK] verified: {0} moved off-screen (y={1})" -f $TargetName, $OFFSCREEN_Y) 'Green'
            return 0
        }
        'revert' {
            $bak = $level + $BackupSuffix
            if (-not (Test-Path -LiteralPath $bak -PathType Leaf)) {
                Write-Line ("[x] No backup at {0} - cannot revert." -f $bak) 'Red'
                return 1
            }
            if (Test-GameRunning) {
                Write-Line '[x] disco.exe is running. Close the game first, then retry.' 'Red'
                return 1
            }
            Copy-Item -LiteralPath $bak -Destination $level -Force
            $after = [System.IO.File]::ReadAllBytes($level)
            $off2  = Get-TargetOffset $after
            $v2 = if ($off2 -ge 0) { [System.BitConverter]::ToSingle($after, $off2) } else { '?' }
            Write-Line '[+] restored original from backup.' 'Green'
            Write-Line ("[i] {0}.m_AnchoredPosition.y = {1}" -f $TargetName, $v2)
            return 0
        }
        'uninstall' {
            $bak = $level + $BackupSuffix
            if (Test-GameRunning) {
                Write-Line '[x] disco.exe is running. Close the game first, then retry.' 'Red'
                return 1
            }
            if (Test-FileSafe $bak) {
                Copy-Item -LiteralPath $bak -Destination $level -Force
                Write-Line ("[+] restored original from backup: {0}" -f (Split-Path -Leaf $bak)) 'Green'
            } elseif ([Math]::Abs($y) -lt 0.001) {
                Write-Line '[=] file is already the original (y=0); no restore needed.'
            } elseif ([Math]::Abs($y - $OFFSCREEN_Y) -lt 1.0) {
                # No backup, but the file still carries our exact signature.
                # Writing the four bytes back is exact: that is all we change.
                $b2 = [System.IO.File]::ReadAllBytes($level)
                $offB = Get-TargetOffset $b2
                [Array]::Copy([System.BitConverter]::GetBytes([single]0.0), 0, $b2, $offB, 4)
                [System.IO.File]::WriteAllBytes($level, $b2)
                Write-Line '[+] no backup found -- un-patched in place: y -> 0.0' 'Green'
            } else {
                Write-Line ("[x] File is neither the original nor our patched state (y={0}) and no backup exists -- refusing to guess." -f $y) 'Red'
                return 1
            }

            # An old v1.0.0 patch may have left m_IsActive at 0.  Harmless at
            # runtime, but it is not the shipped value -- put it back.
            $b3 = [System.IO.File]::ReadAllBytes($level)
            $iso3 = Get-IsActiveOffset $b3
            if ($iso3 -ge 0 -and $b3[$iso3] -ne 1) {
                $b3[$iso3] = 1
                [System.IO.File]::WriteAllBytes($level, $b3)
                Write-Line '[+] m_IsActive reset to 1 (repairs an old v1.0.0 patch)' 'Green'
            }

            $fin  = [System.IO.File]::ReadAllBytes($level)
            $offF = Get-TargetOffset $fin
            $yF   = if ($offF -ge 0) { [System.BitConverter]::ToSingle($fin, $offF) } else { [single]::NaN }
            $isoF = Get-IsActiveOffset $fin
            $actF = if ($isoF -ge 0) { $fin[$isoF] } else { 1 }
            if ([Math]::Abs($yF) -gt 0.001 -or $actF -ne 1) {
                Write-Line ("[x] verification FAILED: y={0} m_IsActive={1}" -f $yF, $actF) 'Red'
                return 1
            }

            if ((Test-FileSafe $bak) -and -not $KeepBackup) {
                Remove-Item -LiteralPath $bak -Force
                Write-Line ("[+] backup removed: {0}" -f (Split-Path -Leaf $bak)) 'Green'
            } elseif (Test-FileSafe $bak) {
                Write-Line ("[i] backup kept (-KeepBackup): {0}" -f (Split-Path -Leaf $bak))
            }

            Write-Line '[OK] uninstalled: level2 is back to the original (y=0.000, m_IsActive=1)' 'Green'

            $dirL  = Split-Path -Parent $level
            $baseN = Split-Path -Leaf $level
            $ours  = $baseN + $BackupSuffix
            foreach ($f in (Get-ChildItem -LiteralPath $dirL -File -ErrorAction SilentlyContinue)) {
                if ($f.Name -eq $ours) { continue }
                if ($f.Name.ToLowerInvariant().StartsWith($baseN.ToLowerInvariant()) -and
                    $f.Name.ToLowerInvariant().Contains('backup')) {
                    Write-Line ("[i] note: unrelated backup still present: {0} (you may delete it)" -f $f.Name)
                }
            }
            return 0
        }
    }
}

exit (Invoke-Action)
