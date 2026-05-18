SHELL := /bin/bash

COMPOSE := docker compose -f infra/compose/docker-compose.yaml -f infra/compose/docker-compose.prod.yaml --env-file infra/env/infra.env
MIGRATION_TARGETS := auth_service:services/authentification class_service:services/classification transactions_service:services/transactions budgets_service:services/budgets goals_service:services/goals notification_service:services/notifications

.PHONY: init-env check-deploy deploy check-frontend-static up down restart build ps logs migrate pull clean

init-env:
	./deploy/init-env.sh

check-deploy:
	./deploy/check-deploy.sh

deploy:
	./deploy/deploy.sh

check-frontend-static:
	test -f frontend/dist/index.html

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200

migrate:
	@set -e; \
	for target in $(MIGRATION_TARGETS); do \
		service_name="$${target%%:*}"; \
		service_dir="$${target#*:}"; \
		if [[ -f "$${service_dir}/alembic.ini" ]]; then \
			echo "Running migrations for $${service_name}"; \
			$(COMPOSE) exec -T "$${service_name}" alembic upgrade head; \
		fi; \
	done

pull:
	git pull --ff-only

clean:
	docker system prune -f
