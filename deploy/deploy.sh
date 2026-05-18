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

migration_targets=(
  "auth_service:services/authentification"
  "class_service:services/classification"
  "transactions_service:services/transactions"
  "budgets_service:services/budgets"
  "goals_service:services/goals"
  "notification_service:services/notifications"
)

for env_file in "${required_env_files[@]}"; do
  if [[ ! -f "${env_file}" ]]; then
    echo "Missing ${env_file}" >&2
    echo "Create it with: cp ${env_file}.example ${env_file}" >&2
    echo "Or run: ./deploy/init-env.sh" >&2
    exit 1
  fi
done

if [[ ! -f "frontend/dist/index.html" ]]; then
  echo "Missing frontend/dist/index.html" >&2
  echo "Build frontend outside Docker first and place static files in frontend/dist." >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git pull --ff-only
fi

docker compose "${COMPOSE_ARGS[@]}" build
docker compose "${COMPOSE_ARGS[@]}" up -d

for target in "${migration_targets[@]}"; do
  service_name="${target%%:*}"
  service_dir="${target#*:}"

  if [[ -f "${service_dir}/alembic.ini" ]]; then
    echo "Running migrations for ${service_name}"
    docker compose "${COMPOSE_ARGS[@]}" exec -T "${service_name}" alembic upgrade head
  fi
done

docker compose "${COMPOSE_ARGS[@]}" ps

echo
echo "Deploy completed successfully."
