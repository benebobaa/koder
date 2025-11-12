# Makefile for Todo List API
# Common development and build tasks

# Variables
APP_NAME=todo-api
BINARY_NAME=bin/$(APP_NAME)
DOCKER_IMAGE=$(APP_NAME):latest
MIGRATIONS_DIR=migrations

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  build      - Build the application binary"
	@echo "  run        - Run the application locally"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run application with Docker Compose"
	@echo "  migrate     - Run database migrations"
	@echo "  dev         - Run in development mode with hot reload"
	@echo "  lint        - Run linter"
	@echo "  fmt         - Format code"
	@echo "  deps        - Download dependencies"
	@echo "  vendor      - Vendor dependencies"

# Build the application
.PHONY: build
build: deps
	@echo "Building $(APP_NAME)..."
	@mkdir -p bin
	go build -o $(BINARY_NAME) ./cmd/api
	@echo "Build complete: $(BINARY_NAME)"

# Run the application locally
.PHONY: run
run: build
	@echo "Starting $(APP_NAME)..."
	@./$(BINARY_NAME)

# Run tests
.PHONY: test
test:
	@echo "Running tests..."
	go test -v ./...

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf bin/
	@rm -rf vendor/
	@go clean

# Build Docker image
.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .
	@echo "Docker image built: $(DOCKER_IMAGE)"

# Run with Docker Compose
.PHONY: docker-run
docker-run:
	@echo "Starting application with Docker Compose..."
	docker-compose up --build

# Stop Docker Compose
.PHONY: docker-stop
docker-stop:
	@echo "Stopping Docker Compose..."
	docker-compose down

# Run database migrations
.PHONY: migrate
migrate:
	@echo "Running database migrations..."
	@if [ -f "$(MIGRATIONS_DIR)/001_create_todos_table.sql" ]; then \
		echo "Found migration file: 001_create_todos_table.sql"; \
		echo "Note: In a production environment, you would use a proper migration tool"; \
		echo "For now, you can manually run the SQL file against your database."; \
	else \
		echo "No migration files found in $(MIGRATIONS_DIR)/"; \
	fi

# Development mode with hot reload (requires air)
.PHONY: dev
dev:
	@if command -v air > /dev/null; then \
		echo "Starting development server with hot reload..."; \
		air; \
	else \
		echo "Air not found. Installing..."; \
		go install github.com/cosmtrek/air@latest; \
		echo "Starting development server with hot reload..."; \
		air; \
	fi

# Run linter
.PHONY: lint
lint:
	@if command -v golangci-lint > /dev/null; then \
		echo "Running linter..."; \
		golangci-lint run; \
	else \
		echo "golangci-lint not found. Installing..."; \
		curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin v1.54.2; \
		echo "Running linter..."; \
		golangci-lint run; \
	fi

# Format code
.PHONY: fmt
fmt:
	@echo "Formatting code..."
	go fmt ./...
	@echo "Code formatted"

# Download dependencies
.PHONY: deps
deps:
	@echo "Downloading dependencies..."
	go mod download
	go mod verify
	@echo "Dependencies downloaded"

# Vendor dependencies
.PHONY: vendor
vendor:
	@echo "Vendoring dependencies..."
	go mod vendor
	@echo "Dependencies vendored"

# Generate documentation
.PHONY: docs
docs:
	@echo "Generating documentation..."
	@if command -v swag > /dev/null; then \
		swag init -g cmd/api/main.go; \
		echo "Swagger documentation generated"; \
	else \
		echo "swag not found. Install with: go install github.com/swaggo/swag/cmd/swag@latest"; \
	fi

# Security audit
.PHONY: audit
audit:
	@echo "Running security audit..."
	go mod tidy
	go vet ./...
	@if command -v gosec > /dev/null; then \
		gosec ./...; \
	else \
		echo "gosec not found. Install with: go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest"; \
	fi

# Setup development environment
.PHONY: setup
setup:
	@echo "Setting up development environment..."
	@echo "1. Installing dependencies..."
	$(MAKE) deps
	@echo "2. Installing development tools..."
	go install github.com/cosmtrek/air@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/swaggo/swag/cmd/swag@latest
	@echo "3. Building application..."
	$(MAKE) build
	@echo "Setup complete!"
	@echo ""
	@echo "Available commands:"
	@echo "  make run     - Run the application"
	@echo "  make dev     - Run with hot reload"
	@echo "  make test    - Run tests"
	@echo "  make lint    - Run linter"

# Production build
.PHONY: prod-build
prod-build:
	@echo "Building production binary..."
	CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o $(BINARY_NAME) ./cmd/api
	@echo "Production build complete: $(BINARY_NAME)"

# Show application info
.PHONY: info
info:
	@echo "Application: $(APP_NAME)"
	@echo "Binary: $(BINARY_NAME)"
	@echo "Docker Image: $(DOCKER_IMAGE)"
	@echo "Go Version: $(shell go version)"
	@echo ""
	@echo "Dependencies:"
	@go list -m all | head -10