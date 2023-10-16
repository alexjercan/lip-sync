.DEFAULT_GOAL := help
.PHONY: help format lint

help: ## Display this help
	@cat Makefile | grep -E "^\w+$:"

format: ## Format the project
	poetry run isort lip_sync/
	poetry run black lip_sync/

lint: ## Lint the project
	poetry run pylint lip_sync/
	poetry run mypy lip_sync/ --ignore-missing-imports

