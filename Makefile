.DEFAULT_GOAL := help
.PHONY: env help lint

env: ## Create or update conda environment
	conda env create --file environment.yaml 2>/dev/null \
		|| conda env update --file environment.yaml --prune

format: ## Format all Python files
	isort src/ && black src/

help: ## Show available commands
	@echo "usage: make [target] ..."
	@echo
	@echo "targets:"
	@egrep "^(.+)\:\ ##\ (.+)" ${MAKEFILE_LIST} | column -t -c 2 -s ":#"
