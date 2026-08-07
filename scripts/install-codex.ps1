param(
  [string]$Repo = "xi-kari/crossframe-skill",
  [string]$DestinationRoot = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\skills"),
  [string]$InstallerPath = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\skills\.system\skill-installer\scripts\install-skill-from-github.py")
)

$ErrorActionPreference = "Stop"

$null = New-Item -ItemType Directory -Path $DestinationRoot -Force
$resolvedSkillsRoot = (Resolve-Path -LiteralPath $DestinationRoot).Path
$installer = $InstallerPath
$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonExe = Get-Command python -ErrorAction SilentlyContinue

if (-not (Test-Path -LiteralPath $installer)) {
  throw "Codex skill installer not found: $installer"
}

if (-not $pyLauncher -and -not $pythonExe) {
  throw "Python not found. Install Python Launcher `py` or make `python` available on PATH."
}

function Invoke-CodexSkillInstaller {
  param(
    [string]$SkillPath
  )

  if ($pyLauncher) {
    & $pyLauncher.Source -3 $installer --repo $Repo --path $SkillPath --dest $resolvedSkillsRoot
    return
  }

  & $pythonExe.Source $installer --repo $Repo --path $SkillPath --dest $resolvedSkillsRoot
}

$skills = @(
  "skills/crossframe-suite",
  "skills/crossframe",
  "skills/crossframe-essay",
  "skills/crossframe-critical",
  "skills/crossframe-review",
  "skills/crossframe-dialogue",
  "skills/crossframe-casebook",
  "skills/crossframe-history",
  "skills/crossframe-inquiry",
  "skills/crossframe-max",
  "skills/crossframe-promax",
  "skills/crossframe-public",
  "skills/crossframe-org",
  "skills/crossframe-teach",
  "skills/crossframe-debate",
  "skills/crossframe-notebook"
)

foreach ($skillPath in $skills) {
  $skillName = Split-Path -Leaf $skillPath
  $destDir = [System.IO.Path]::GetFullPath((Join-Path $resolvedSkillsRoot $skillName))
  $installed = Join-Path $destDir "SKILL.md"
  $rootPrefix = $resolvedSkillsRoot
  if (-not $rootPrefix.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
    $rootPrefix += [System.IO.Path]::DirectorySeparatorChar
  }

  if (-not $destDir.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe destination: $destDir"
  }

  $backupDir = $null
  if (Test-Path -LiteralPath $destDir) {
    $backupDir = Join-Path ([System.IO.Path]::GetTempPath()) ("crossframe-skill-install-backup-$skillName-" + [System.Guid]::NewGuid().ToString("N"))
    Move-Item -LiteralPath $destDir -Destination $backupDir
  }

  try {
    Invoke-CodexSkillInstaller -SkillPath $skillPath
    if ($LASTEXITCODE -ne 0) {
      throw "Installer failed for $skillName with exit code $LASTEXITCODE"
    }

    if (-not (Test-Path -LiteralPath $installed)) {
      throw "Install did not create expected file: $installed"
    }

    if ($backupDir -and (Test-Path -LiteralPath $backupDir)) {
      Remove-Item -LiteralPath $backupDir -Recurse -Force
    }
  }
  catch {
    if (Test-Path -LiteralPath $destDir) {
      Remove-Item -LiteralPath $destDir -Recurse -Force
    }
    if ($backupDir -and (Test-Path -LiteralPath $backupDir)) {
      Move-Item -LiteralPath $backupDir -Destination $destDir
    }
    throw
  }

  Write-Host "Installed $skillName skill to $installed"
}
