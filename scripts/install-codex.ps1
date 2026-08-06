param(
  [string]$Repo = "xi-kari/crossframe-skill",
  [string]$DestinationRoot = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\skills"),
  [string]$InstallerPath = (Join-Path ([Environment]::GetFolderPath("UserProfile")) ".codex\skills\.system\skill-installer\scripts\install-skill-from-github.py")
)

$ErrorActionPreference = "Stop"
$installerWasSupplied = $PSBoundParameters.ContainsKey("InstallerPath")

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

function Get-ValidatedChildPath {
  param(
    [Parameter(Mandatory = $true)][string]$Root,
    [Parameter(Mandatory = $true)][string]$Candidate,
    [Parameter(Mandatory = $true)][string]$Label
  )

  $rootPath = [System.IO.Path]::GetFullPath($Root)
  $candidatePath = [System.IO.Path]::GetFullPath($Candidate)
  $separator = [System.IO.Path]::DirectorySeparatorChar.ToString()
  $rootPrefix = $rootPath
  if (-not $rootPrefix.EndsWith($separator)) {
    $rootPrefix += $separator
  }

  if (-not $candidatePath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe ${Label}: $candidatePath"
  }

  return $candidatePath
}

function Invoke-PythonProcess {
  param(
    [Parameter(Mandatory = $true)][string[]]$CommandArguments,
    [Parameter(Mandatory = $true)][string]$FailureMessage
  )

  if ($pyLauncher) {
    & $pyLauncher.Source -3 @CommandArguments
  }
  else {
    & $pythonExe.Source @CommandArguments
  }

  if ($LASTEXITCODE -ne 0) {
    throw "$FailureMessage with exit code $LASTEXITCODE"
  }
}

function Assert-CanonicalSource {
  param(
    [Parameter(Mandatory = $true)][string]$CandidateRoot
  )

  $resolvedRoot = (Resolve-Path -LiteralPath $CandidateRoot).Path
  $mirrorScript = Join-Path $resolvedRoot "scripts\sync_skill_mirrors.py"
  if (-not (Test-Path -LiteralPath $mirrorScript -PathType Leaf)) {
    throw "Canonical mirror checker not found: $mirrorScript"
  }
  foreach ($skillPath in $skills) {
    $sourceSkill = Join-Path $resolvedRoot ($skillPath -replace "/", [System.IO.Path]::DirectorySeparatorChar)
    if (-not (Test-Path -LiteralPath $sourceSkill -PathType Container)) {
      throw "Missing canonical skill directory: $sourceSkill"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $sourceSkill "SKILL.md") -PathType Leaf)) {
      throw "Missing canonical skill entrypoint: $sourceSkill"
    }
  }

  return $resolvedRoot
}

function Resolve-GitHubCloneSpec {
  param(
    [Parameter(Mandatory = $true)][string]$Repository
  )

  if ($Repository -match "^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$") {
    $slug = $Repository
    if ($slug.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
      $slug = $slug.Substring(0, $slug.Length - 4)
    }
    return @("https://github.com/$slug.git", "main")
  }

  try {
    $uri = [System.Uri]$Repository
  }
  catch {
    throw "Remote -Repo must be an owner/repo name or a GitHub URL: $Repository"
  }

  if (-not $uri.IsAbsoluteUri -or $uri.Host -ne "github.com") {
    throw "Remote -Repo must be an owner/repo name or a GitHub URL: $Repository"
  }

  $segments = @($uri.AbsolutePath.Trim("/").Split("/", [System.StringSplitOptions]::RemoveEmptyEntries))
  if ($segments.Count -lt 2) {
    throw "Invalid GitHub repository URL: $Repository"
  }

  $owner = $segments[0]
  $name = $segments[1]
  if ($name.EndsWith(".git", [System.StringComparison]::OrdinalIgnoreCase)) {
    $name = $name.Substring(0, $name.Length - 4)
  }
  $ref = "main"
  if ($segments.Count -gt 2) {
    if ($segments.Count -lt 4 -or $segments[2] -notin @("tree", "blob")) {
      throw "Unsupported GitHub repository URL: $Repository"
    }
    $ref = [System.Uri]::UnescapeDataString($segments[3])
  }

  return @("https://github.com/$owner/$name.git", $ref)
}

function Invoke-CodexSkillInstaller {
  param(
    [Parameter(Mandatory = $true)][string]$SkillPath
  )

  if ($pyLauncher) {
    & $pyLauncher.Source -3 $installer --repo $installerRepo --path $SkillPath --dest $resolvedSkillsRoot
  }
  else {
    & $pythonExe.Source $installer --repo $installerRepo --path $SkillPath --dest $resolvedSkillsRoot
  }

  if ($LASTEXITCODE -ne 0) {
    $skillName = Split-Path -Leaf $SkillPath
    throw "Installer failed for $skillName with exit code $LASTEXITCODE"
  }
}

function Invoke-InstallationRollback {
  param(
    [Parameter(Mandatory = $true)]$PromotedSkills,
    [Parameter(Mandatory = $true)]$BackedUpSkills,
    [Parameter(Mandatory = $true)][string]$LiveRoot,
    [Parameter(Mandatory = $true)][string]$StageRoot,
    [Parameter(Mandatory = $true)][string]$BackupRoot
  )

  $rollbackSucceeded = $true

  for ($index = $PromotedSkills.Count - 1; $index -ge 0; $index--) {
    $skillName = $PromotedSkills[$index]
    $livePath = Get-ValidatedChildPath -Root $LiveRoot -Candidate (Join-Path $LiveRoot $skillName) -Label "rollback destination"
    $stagePath = Get-ValidatedChildPath -Root $StageRoot -Candidate (Join-Path $StageRoot $skillName) -Label "rollback staging path"
    if (Test-Path -LiteralPath $livePath) {
      try {
        Move-Item -LiteralPath $livePath -Destination $stagePath
      }
      catch {
        try {
          Remove-Item -LiteralPath $livePath -Recurse -Force
        }
        catch {
          $rollbackSucceeded = $false
          Write-Warning "Could not roll back promoted skill ${skillName}: $($_.Exception.Message)"
        }
      }
    }
  }

  for ($index = $BackedUpSkills.Count - 1; $index -ge 0; $index--) {
    $skillName = $BackedUpSkills[$index]
    $livePath = Get-ValidatedChildPath -Root $LiveRoot -Candidate (Join-Path $LiveRoot $skillName) -Label "restore destination"
    $backupPath = Get-ValidatedChildPath -Root $BackupRoot -Candidate (Join-Path $BackupRoot $skillName) -Label "restore backup"
    try {
      if (Test-Path -LiteralPath $livePath) {
        Remove-Item -LiteralPath $livePath -Recurse -Force
      }
      if (Test-Path -LiteralPath $backupPath) {
        Move-Item -LiteralPath $backupPath -Destination $livePath
      }
    }
    catch {
      $rollbackSucceeded = $false
      Write-Warning "Could not restore backup for ${skillName}: $($_.Exception.Message)"
    }
  }

  return $rollbackSucceeded
}

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyLauncher -and -not $pythonExe) {
  throw "Python not found. Install Python Launcher `py` or make `python` available on PATH."
}

$repoExists = Test-Path -LiteralPath $Repo -ErrorAction SilentlyContinue
$localRepository = $repoExists -and (Test-Path -LiteralPath $Repo -PathType Container)
if ($repoExists -and -not $localRepository) {
  throw "Local -Repo is not a directory: $Repo"
}

$useInstaller = $installerWasSupplied -or -not $localRepository
$installer = $InstallerPath
if ($useInstaller) {
  if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
    throw "Codex skill installer not found: $installer"
  }
  $installer = (Resolve-Path -LiteralPath $installer).Path
}

$null = New-Item -ItemType Directory -Path $DestinationRoot -Force
$destinationRootResolved = (Resolve-Path -LiteralPath $DestinationRoot).Path
$transactionName = ".crossframe-install-" + [System.Guid]::NewGuid().ToString("N")
$transactionRoot = Get-ValidatedChildPath -Root $destinationRootResolved -Candidate (Join-Path $destinationRootResolved $transactionName) -Label "transaction directory"
$cleanupTransaction = $true

try {
  $null = New-Item -ItemType Directory -Path $transactionRoot
  $transactionRoot = (Resolve-Path -LiteralPath $transactionRoot).Path
  $transactionRoot = Get-ValidatedChildPath -Root $destinationRootResolved -Candidate $transactionRoot -Label "transaction directory"
  $stagingRoot = Get-ValidatedChildPath -Root $transactionRoot -Candidate (Join-Path $transactionRoot "staging") -Label "staging directory"
  $backupRoot = Get-ValidatedChildPath -Root $transactionRoot -Candidate (Join-Path $transactionRoot "backups") -Label "backup directory"
  $null = New-Item -ItemType Directory -Path $stagingRoot, $backupRoot

  if ($localRepository) {
    $canonicalRoot = Assert-CanonicalSource -CandidateRoot $Repo
    $installerRepo = $canonicalRoot
  }
  else {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if (-not $git) {
      throw "Git is required to materialize and verify the canonical remote repository."
    }
    $cloneSpec = @(Resolve-GitHubCloneSpec -Repository $Repo)
    $canonicalCandidate = Get-ValidatedChildPath -Root $transactionRoot -Candidate (Join-Path $transactionRoot "canonical") -Label "canonical source"
    & $git.Source clone --depth 1 --single-branch --branch $cloneSpec[1] $cloneSpec[0] $canonicalCandidate
    if ($LASTEXITCODE -ne 0) {
      throw "Could not materialize canonical repository with exit code $LASTEXITCODE"
    }
    $canonicalRoot = Assert-CanonicalSource -CandidateRoot $canonicalCandidate
    $installerRepo = $Repo
  }

  $resolvedSkillsRoot = $stagingRoot
  $mirrorScript = Join-Path $canonicalRoot "scripts\sync_skill_mirrors.py"
  if (-not $useInstaller) {
    Invoke-PythonProcess -CommandArguments @($mirrorScript, "--repo", $canonicalRoot, "--mirror", $stagingRoot) -FailureMessage "Canonical staging install failed"
  }

  foreach ($skillPath in $skills) {
    $skillName = Split-Path -Leaf $skillPath
    $stagedSkill = Get-ValidatedChildPath -Root $stagingRoot -Candidate (Join-Path $stagingRoot $skillName) -Label "staged skill"
    if ($useInstaller) {
      Invoke-CodexSkillInstaller -SkillPath $skillPath
    }

    $installed = Join-Path $stagedSkill "SKILL.md"
    if (-not (Test-Path -LiteralPath $installed -PathType Leaf)) {
      throw "Install did not create expected file: $installed"
    }
  }

  Invoke-PythonProcess -CommandArguments @($mirrorScript, "--repo", $canonicalRoot, "--mirror", $stagingRoot, "--check") -FailureMessage "Staged skill verification failed"

  $backedUpSkills = [System.Collections.Generic.List[string]]::new()
  $promotedSkills = [System.Collections.Generic.List[string]]::new()
  try {
    foreach ($skillPath in $skills) {
      $skillName = Split-Path -Leaf $skillPath
      $livePath = Get-ValidatedChildPath -Root $destinationRootResolved -Candidate (Join-Path $destinationRootResolved $skillName) -Label "destination"
      $backupPath = Get-ValidatedChildPath -Root $backupRoot -Candidate (Join-Path $backupRoot $skillName) -Label "backup"
      if (Test-Path -LiteralPath $livePath) {
        Move-Item -LiteralPath $livePath -Destination $backupPath
        $backedUpSkills.Add($skillName)
      }
    }

    foreach ($skillPath in $skills) {
      $skillName = Split-Path -Leaf $skillPath
      $stagedSkill = Get-ValidatedChildPath -Root $stagingRoot -Candidate (Join-Path $stagingRoot $skillName) -Label "promotion source"
      $livePath = Get-ValidatedChildPath -Root $destinationRootResolved -Candidate (Join-Path $destinationRootResolved $skillName) -Label "promotion destination"
      Move-Item -LiteralPath $stagedSkill -Destination $livePath
      $promotedSkills.Add($skillName)
    }
  }
  catch {
    $rollbackSucceeded = Invoke-InstallationRollback -PromotedSkills $promotedSkills -BackedUpSkills $backedUpSkills -LiveRoot $destinationRootResolved -StageRoot $stagingRoot -BackupRoot $backupRoot
    if (-not $rollbackSucceeded) {
      $cleanupTransaction = $false
      Write-Warning "Rollback was incomplete; retained transaction data at $transactionRoot"
    }
    throw
  }
}
finally {
  if ($cleanupTransaction -and (Test-Path -LiteralPath $transactionRoot)) {
    $validatedTransaction = Get-ValidatedChildPath -Root $destinationRootResolved -Candidate $transactionRoot -Label "transaction cleanup"
    Remove-Item -LiteralPath $validatedTransaction -Recurse -Force
  }
}

foreach ($skillPath in $skills) {
  $skillName = Split-Path -Leaf $skillPath
  $installed = Join-Path (Join-Path $destinationRootResolved $skillName) "SKILL.md"
  Write-Host "Installed $skillName skill to $installed"
}
