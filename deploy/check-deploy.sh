#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

COMPOSE_ARGS=(
  -f infra/compose/docker-compose.yaml
  -f infra/compose/docker-compose.prod.yaml
  --env-file infra/env/infra.env
)

required_env_files=(
  "infra/env/infra.env"
  "infra/env/auth.env"
  "infra/env/transactions.env"
  "infra/env/classification.env"
  "infra/env/budgets.env"
  "infra/env/goals.env"
  "infra/env/notifications.env"
)

problems=()
warnings=()

if ! command -v docker >/dev/null 2>&1; then
  problems+=("docker is not installed or not in PATH")
fi

if command -v docker >/dev/null 2>&1; then
  if ! docker compose version >/dev/null 2>&1; then
    problems+=("Docker Compose plugin is not available")
  fi
fi

if ! command -v git >/dev/null 2>&1; then
  problems+=("git is not installed or not in PATH")
fi

if ! command -v make >/dev/null 2>&1; then
  warnings+=("make is not installed; use ./deploy/deploy.sh directly")
fi

for env_file in "${required_env_files[@]}"; do
  if [[ ! -f "${env_file}" ]]; then
    problems+=("missing ${env_file}; create it from ${env_file}.example")
  fi
done

if (( ${#problems[@]} == 0 )); then
  if ! docker compose "${COMPOSE_ARGS[@]}" config >/dev/null; then
    problems+=("docker compose config failed")
  fi
fi

if [[ ! -f "frontend/dist/index.html" ]]; then
  problems+=("missing frontend/dist/index.html; build frontend outside Docker before deploy")
fi

if (( ${#warnings[@]} > 0 )); then
  echo "Warnings:"
  printf '  - %s\n' "${warnings[@]}"
fi

if (( ${#problems[@]} > 0 )); then
  echo "Problems:"
  printf '  - %s\n' "${problems[@]}"
  exit 1
fi

echo "OK: deploy prerequisites and compose config look valid."
