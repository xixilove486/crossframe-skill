#!/usr/bin/env bash
set -euo pipefail

repo="xi-kari/crossframe-skill"
skills_root="${HOME}/.codex/skills"
installer="${HOME}/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py"
installer_was_supplied=0

usage() {
  cat <<'EOF'
Usage: scripts/install-codex.sh [--repo owner/name|DIR] [--dest DIR] [--installer FILE]

Installs the CrossFrame Skill Suite into $HOME/.codex/skills.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --repo" >&2
        exit 2
      fi
      repo="$2"
      shift 2
      ;;
    --dest)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --dest" >&2
        exit 2
      fi
      skills_root="$2"
      shift 2
      ;;
    --installer)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --installer" >&2
        exit 2
      fi
      installer="$2"
      installer_was_supplied=1
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if command -v python3 >/dev/null 2>&1; then
  python_bin="python3"
elif command -v python >/dev/null 2>&1; then
  python_bin="python"
else
  echo "python3 or python is required" >&2
  exit 1
fi

skills=(
  "skills/crossframe-suite"
  "skills/crossframe"
  "skills/crossframe-essay"
  "skills/crossframe-critical"
  "skills/crossframe-review"
  "skills/crossframe-dialogue"
  "skills/crossframe-casebook"
  "skills/crossframe-history"
  "skills/crossframe-inquiry"
  "skills/crossframe-max"
  "skills/crossframe-promax"
  "skills/crossframe-public"
  "skills/crossframe-org"
  "skills/crossframe-teach"
  "skills/crossframe-debate"
  "skills/crossframe-notebook"
)

resolve_existing_path() {
  "$python_bin" - "$1" <<'PY'
from pathlib import Path
import sys

print(Path(sys.argv[1]).expanduser().resolve(strict=True))
PY
}

resolve_child_path() {
  "$python_bin" - "$1" "$2" "$3" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve(strict=True)
candidate = Path(sys.argv[2]).resolve(strict=False)
label = sys.argv[3]
try:
    relative = candidate.relative_to(root)
except ValueError as error:
    raise SystemExit(f"unsafe {label}: {candidate}") from error
if not relative.parts:
    raise SystemExit(f"unsafe {label}: {candidate}")
print(candidate)
PY
}

github_clone_spec() {
  "$python_bin" - "$1" <<'PY'
from urllib.parse import unquote, urlparse
import re
import sys

repository = sys.argv[1]
if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
    slug = repository[:-4] if repository.lower().endswith(".git") else repository
    print(f"https://github.com/{slug}.git\tmain")
    raise SystemExit(0)

parsed = urlparse(repository)
if not parsed.scheme or parsed.hostname != "github.com":
    raise SystemExit(f"remote --repo must be an owner/repo name or a GitHub URL: {repository}")
parts = [part for part in parsed.path.split("/") if part]
if len(parts) < 2:
    raise SystemExit(f"invalid GitHub repository URL: {repository}")
owner, name = parts[:2]
if name.lower().endswith(".git"):
    name = name[:-4]
ref = "main"
if len(parts) > 2:
    if len(parts) < 4 or parts[2] not in {"tree", "blob"}:
        raise SystemExit(f"unsupported GitHub repository URL: {repository}")
    ref = unquote(parts[3])
print(f"https://github.com/{owner}/{name}.git\t{ref}")
PY
}

assert_canonical_source() {
  local candidate_root="$1"
  local mirror_script="$candidate_root/scripts/sync_skill_mirrors.py"
  if [[ ! -f "$mirror_script" ]]; then
    echo "Canonical mirror checker not found: $mirror_script" >&2
    return 1
  fi
  local skill_path source_skill
  for skill_path in "${skills[@]}"; do
    source_skill="$candidate_root/$skill_path"
    if [[ ! -d "$source_skill" || ! -f "$source_skill/SKILL.md" ]]; then
      echo "Invalid canonical skill source: $source_skill" >&2
      return 1
    fi
  done
}

local_repository=0
if [[ -e "$repo" ]]; then
  if [[ -d "$repo" ]]; then
    local_repository=1
  else
    echo "local --repo is not a directory: $repo" >&2
    exit 1
  fi
fi

use_installer=0
if [[ "$installer_was_supplied" -eq 1 || "$local_repository" -eq 0 ]]; then
  use_installer=1
fi
if [[ "$use_installer" -eq 1 && ! -f "$installer" ]]; then
  echo "Codex skill installer not found: $installer" >&2
  exit 1
fi
if [[ "$use_installer" -eq 1 ]]; then
  installer="$(resolve_existing_path "$installer")"
fi

mkdir -p "$skills_root"
destination_root="$(resolve_existing_path "$skills_root")"
transaction_root=""
cleanup_transaction=1

cleanup() {
  local status=$?
  trap - EXIT
  if [[ "$cleanup_transaction" -eq 1 && -n "${transaction_root:-}" && -e "$transaction_root" ]]; then
    if ! resolve_child_path "$destination_root" "$transaction_root" "transaction cleanup" >/dev/null; then
      status=1
    elif ! rm -rf "$transaction_root"; then
      echo "could not clean transaction directory: $transaction_root" >&2
      status=1
    fi
  fi
  exit "$status"
}
trap cleanup EXIT

transaction_root="$(mktemp -d "$destination_root/.crossframe-install-XXXXXXXX")"
transaction_root="$(resolve_existing_path "$transaction_root")"
resolve_child_path "$destination_root" "$transaction_root" "transaction directory" >/dev/null

staging_root="$transaction_root/staging"
backup_root="$transaction_root/backups"
mkdir "$staging_root" "$backup_root"
resolve_child_path "$transaction_root" "$staging_root" "staging directory" >/dev/null
resolve_child_path "$transaction_root" "$backup_root" "backup directory" >/dev/null

if [[ "$local_repository" -eq 1 ]]; then
  canonical_root="$(resolve_existing_path "$repo")"
  installer_repo="$canonical_root"
else
  if ! command -v git >/dev/null 2>&1; then
    echo "git is required to materialize and verify the canonical remote repository" >&2
    exit 1
  fi
  clone_spec="$(github_clone_spec "$repo")"
  IFS=$'\t' read -r clone_url clone_ref <<<"$clone_spec"
  canonical_root="$transaction_root/canonical"
  resolve_child_path "$transaction_root" "$canonical_root" "canonical source" >/dev/null
  if ! git clone --depth 1 --single-branch --branch "$clone_ref" "$clone_url" "$canonical_root"; then
    echo "could not materialize canonical repository" >&2
    exit 1
  fi
  canonical_root="$(resolve_existing_path "$canonical_root")"
  installer_repo="$repo"
fi

assert_canonical_source "$canonical_root"

resolved_skills_root="$staging_root"
if [[ "$use_installer" -eq 0 ]]; then
  if ! "$python_bin" "$canonical_root/scripts/sync_skill_mirrors.py" --repo "$canonical_root" --mirror "$staging_root"; then
    echo "Canonical staging install failed" >&2
    exit 1
  fi
fi

for skill_path in "${skills[@]}"; do
  skill_name="${skill_path##*/}"
  staged_skill="$staging_root/$skill_name"
  resolve_child_path "$staging_root" "$staged_skill" "staged skill" >/dev/null

  if [[ "$use_installer" -eq 1 ]]; then
    if ! "$python_bin" "$installer" --repo "$installer_repo" --path "$skill_path" --dest "$resolved_skills_root"; then
      echo "Installer failed for $skill_name" >&2
      exit 1
    fi
  fi

  if [[ ! -f "$staged_skill/SKILL.md" ]]; then
    echo "Install did not create expected file: $staged_skill/SKILL.md" >&2
    exit 1
  fi
done

if ! "$python_bin" "$canonical_root/scripts/sync_skill_mirrors.py" --repo "$canonical_root" --mirror "$staging_root" --check; then
  echo "Staged skill verification failed" >&2
  exit 1
fi

backed_up_skills=()
promoted_skills=()

commit_installation() {
  local skill_path skill_name live_path backup_path staged_skill
  for skill_path in "${skills[@]}"; do
    skill_name="${skill_path##*/}"
    live_path="$destination_root/$skill_name"
    backup_path="$backup_root/$skill_name"
    resolve_child_path "$destination_root" "$live_path" "destination" >/dev/null || return 1
    resolve_child_path "$backup_root" "$backup_path" "backup" >/dev/null || return 1
    if [[ -e "$live_path" || -L "$live_path" ]]; then
      if ! mv "$live_path" "$backup_path"; then
        echo "Could not back up existing skill: $skill_name" >&2
        return 1
      fi
      backed_up_skills+=("$skill_name")
    fi
  done

  for skill_path in "${skills[@]}"; do
    skill_name="${skill_path##*/}"
    staged_skill="$staging_root/$skill_name"
    live_path="$destination_root/$skill_name"
    resolve_child_path "$staging_root" "$staged_skill" "promotion source" >/dev/null || return 1
    resolve_child_path "$destination_root" "$live_path" "promotion destination" >/dev/null || return 1
    if ! mv "$staged_skill" "$live_path"; then
      echo "Could not promote staged skill: $skill_name" >&2
      return 1
    fi
    promoted_skills+=("$skill_name")
  done
}

rollback_installation() {
  local rollback_failed=0
  local index skill_name live_path staged_skill backup_path

  for ((index=${#promoted_skills[@]} - 1; index >= 0; index--)); do
    skill_name="${promoted_skills[index]}"
    live_path="$destination_root/$skill_name"
    staged_skill="$staging_root/$skill_name"
    if [[ -e "$live_path" || -L "$live_path" ]]; then
      if ! mv "$live_path" "$staged_skill"; then
        if ! rm -rf "$live_path"; then
          echo "Could not roll back promoted skill: $skill_name" >&2
          rollback_failed=1
        fi
      fi
    fi
  done

  for ((index=${#backed_up_skills[@]} - 1; index >= 0; index--)); do
    skill_name="${backed_up_skills[index]}"
    live_path="$destination_root/$skill_name"
    backup_path="$backup_root/$skill_name"
    if [[ -e "$live_path" || -L "$live_path" ]]; then
      if ! rm -rf "$live_path"; then
        echo "Could not clear destination while restoring: $skill_name" >&2
        rollback_failed=1
        continue
      fi
    fi
    if [[ -e "$backup_path" || -L "$backup_path" ]]; then
      if ! mv "$backup_path" "$live_path"; then
        echo "Could not restore backup: $skill_name" >&2
        rollback_failed=1
      fi
    fi
  done

  return "$rollback_failed"
}

if ! commit_installation; then
  if ! rollback_installation; then
    cleanup_transaction=0
    echo "Rollback was incomplete; retained transaction data at $transaction_root" >&2
  fi
  exit 1
fi

for skill_path in "${skills[@]}"; do
  skill_name="${skill_path##*/}"
  echo "Installed $skill_name skill to $destination_root/$skill_name/SKILL.md"
done
