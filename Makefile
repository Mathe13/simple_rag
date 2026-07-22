.PHONY: start stop build test

# Start all docker compose containers in detached mode
start:
	docker compose up -d

# Stop all docker compose containers
stop:
	docker compose down

# Build all docker compose containers
build:
	docker compose build

# Run pytest on all modules that have a 'tests' directory
# Uses 'uv run pytest' in each module's directory to ensure the correct environment is used.
test:
	@mkdir -p test_results
	@ROOT_DIR=$$(pwd); \
	for dir in $$(find . -type d -name "tests" -not -path "*/\.venv/*" -not -path "*/\.git/*" | sed 's|/tests$$||' | sort -u); do \
		echo "========================================"; \
		echo "Running tests in $$dir..."; \
		echo "========================================"; \
		DIR_NAME=$$(echo $$dir | sed 's|^\./||' | sed 's|/|_|g'); \
		[ -z "$$DIR_NAME" ] && DIR_NAME="root"; \
		(cd $$dir && uv run pytest --junitxml="$$ROOT_DIR/test_results/$${DIR_NAME}_report.xml") || exit 1; \
	done
