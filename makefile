# Makefile for automating deployment

# Define the Docker Compose files
DOCKER_COMPOSE_PROD = docker/docker-compose.prod.yml
DOCKER_COMPOSE_DEV = docker/docker-compose.dev.yml

# Define the Docker Compose commands
UP_PROD = docker-compose -f $(DOCKER_COMPOSE_PROD) up -d
UP_DEV = docker-compose -f $(DOCKER_COMPOSE_DEV) up -d

# Define the Docker Compose down commands
DOWN_PROD = docker-compose -f $(DOCKER_COMPOSE_PROD) down
DOWN_DEV = docker-compose -f $(DOCKER_COMPOSE_DEV) down

# Define the build commands
BUILD_PROD = docker-compose -f $(DOCKER_COMPOSE_PROD) build
BUILD_DEV = docker-compose -f $(DOCKER_COMPOSE_DEV) build

# Define the logs commands
LOGS_PROD = docker-compose -f $(DOCKER_COMPOSE_PROD) logs -f
LOGS_DEV = docker-compose -f $(DOCKER_COMPOSE_DEV) logs -f

# Define the targets
.PHONY: up-prod up-dev down-prod down-dev build-prod build-dev logs-prod logs-dev

# Target: up-prod
up-prod:
	$(UP_PROD) --force-recreate

# Target: up-dev
up-dev:
	$(UP_DEV) --force-recreate

# Target: down-prod
down-prod:
	$(DOWN_PROD)

# Target: down-dev
down-dev:
	$(DOWN_DEV)

# Target: build-prod
build-prod:
	$(BUILD_PROD) --no-cache

# Target: build-dev
build-dev:
	$(BUILD_DEV) --no-cache

# Target: logs-prod
logs-prod:
	$(LOGS_PROD)

# Target: logs-dev
logs-dev:
	$(LOGS_DEV)
