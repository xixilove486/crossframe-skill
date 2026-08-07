#!/usr/bin/env bash
set -euo pipefail

repo="xi-kari/crossframe-skill"
skills_root="${HOME}/.codex/skills"
installer="${HOME}/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py"

usage() {
  cat <<'EOF'
Usage: scripts/install-codex.sh [--repo owner/name] [--dest DIR] [--installer FILE]

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

if [[ ! -f "$installer" ]]; then
  echo "Codex skill installer not found: $installer" >&2
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

mkdir -p "$skills_root"

resolved_skills_root="$("$python_bin" -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$skills_root")"

for skill_path in "${skills[@]}"; do
  skill_name="${skill_path##*/}"
  dest_dir="$skills_root/$skill_name"
  installed="$dest_dir/SKILL.md"
  resolved_dest="$("$python_bin" -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$dest_dir")"

  case "$resolved_dest" in
    "$resolved_skills_root"/*) ;;
    *)
      echo "Unsafe destination: $dest_dir" >&2
      exit 1
      ;;
  esac

  backup_parent=""
  backup_dir=""
  if [[ -e "$dest_dir" ]]; then
    backup_parent="$(mktemp -d "${TMPDIR:-/tmp}/crossframe-skill-install-backup-${skill_name}.XXXXXX")"
    backup_dir="$backup_parent/$skill_name"
    mv "$dest_dir" "$backup_dir"
  fi

  restore_backup() {
    rm -rf "$dest_dir"
    if [[ -n "$backup_dir" && -e "$backup_dir" ]]; then
      mv "$backup_dir" "$dest_dir"
      rmdir "$backup_parent" 2>/dev/null || true
    fi
  }

  if ! "$python_bin" "$installer" --repo "$repo" --path "$skill_path" --dest "$resolved_skills_root"; then
    restore_backup
    echo "Installer failed for $skill_name" >&2
    exit 1
  fi

  if [[ ! -f "$installed" ]]; then
    restore_backup
    echo "Install did not create expected file: $installed" >&2
    exit 1
  fi

  if [[ -n "$backup_parent" && -e "$backup_parent" ]]; then
    rm -rf "$backup_parent"
  fi

  echo "Installed $skill_name skill to $installed"
done
