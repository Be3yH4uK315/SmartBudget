#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_DIR="${PROJECT_ROOT}/infra/env"

examples=(
  "infra.env"
  "auth.env"
  "transactions.env"
  "classification.env"
  "budgets.env"
  "goals.env"
  "notifications.env"
)

created=()

for env_name in "${examples[@]}"; do
  source_file="${ENV_DIR}/${env_name}.example"
  target_file="${ENV_DIR}/${env_name}"

  if [[ ! -f "${source_file}" ]]; then
    echo "Missing example file: ${source_file}" >&2
    exit 1
  fi

  if [[ -f "${target_file}" ]]; then
    continue
  fi

  cp "${source_file}" "${target_file}"
  created+=("infra/env/${env_name}")
done

if (( ${#created[@]} == 0 )); then
  echo "No env files created. Existing env files were left unchanged."
else
  echo "Created env files:"
  printf '  - %s\n' "${created[@]}"
fi

echo
echo "Edit infra/env/*.env and replace CHANGE_ME placeholders before deploy."
