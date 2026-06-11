# Variables
PYTHON = .venv/bin/python
PIP = .venv/bin/pip
RUFF = .venv/bin/ruff
PYTEST = .venv/bin/pytest
IMAGE_NAME = mirror-monitor
CONTAINER_NAME = mirror-app

# Front-end target files
STATIC_DIR = src/static

.PHONY: init install-tools lint format run clean docker-build docker-run docker-logs docker-clean test test-backend test-frontend

# ۱. آماده‌سازی محیط مجازی و نصب وابستگی‌های پایتون
init:
	@echo "Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install ruff pytest httpx

# ۲. نصب ابزارهای فرانت‌اند به صورت سراسری و بدون نیاز به package.json
install-tools:
	@echo "Installing frontend linting, formatting, and Vitest testing tools globally..."
	npm install -g prettier eslint vitest

# ۳. بررسی خطاها و مرتب‌سازی خودکار کدهای بک‌اند و فرانت‌اند (Linting)
lint:
	@if [ ! -f "$(RUFF)" ]; then echo "Ruff not found. Running make init..."; make init; fi
	@echo "=== Linting Backend (Ruff) ==="
	$(RUFF) check --fix .
	@echo "=== Linting Frontend JS (ESLint Global) ==="
	@if command -v eslint >/dev/null 2>&1; then \
		eslint --fix $(STATIC_DIR); \
	else \
		echo "ESLint not installed globally. Running 'make install-tools' first..."; exit 1; \
	fi

# ۴. مرتب‌سازی ساختار مکتوب کدها (Formatting)
format:
	@if [ ! -f "$(RUFF)" ]; then echo "Ruff not found. Running make init..."; make init; fi
	@echo "=== Formatting Backend (Ruff) ==="
	$(RUFF) format .
	@echo "=== Formatting Frontend (Prettier) ==="
	@if command -v prettier >/dev/null 2>&1; then \
		prettier --write $(STATIC_DIR); \
	else \
		echo "Prettier not installed globally. Running 'make install-tools' first..."; exit 1; \
	fi

# ۵. اجرای پروژه در محیط بومی پایتون
run:
	@if [ ! -d ".venv" ]; then make init; fi
	@echo "Starting Mirror Monitor application..."
	cd src && ../$(PYTHON) main.py

# ۶. ساخت ایمیج داکر
docker-build:
	@echo "Building Docker image [$(IMAGE_NAME)]..."
	docker build -t $(IMAGE_NAME) .

# ۷. اجرای برنامه داخل کانتینر داکر
docker-run:
	@echo "Stopping existing containers if any..."
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Running Docker container [$(CONTAINER_NAME)] on port 8000..."
	docker run -d -p 8000:8000 --name $(CONTAINER_NAME) $(IMAGE_NAME)

# ۸. مشاهده لاگ‌های داکر
docker-logs:
	docker logs -f $(CONTAINER_NAME)

# ۹. پاکسازی محیط داکر
docker-clean:
	@echo "Cleaning up Docker container and image..."
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true

# ۱۰. پاکسازی عمومی پروژه
clean:
	@echo "Cleaning temporary python cache files and .venv..."
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# ۱۱. لایه اجرای تست‌های یکپارچه سیستم (Testing Layer)
test: test-backend test-frontend

test-backend:
test-backend:
	@if [ ! -f "$(PYTEST)" ]; then \
		echo "Pytest not found inside venv. Re-initializing environment..."; \
		make init; \
	fi
	@echo "=== Running Backend Unit Tests (Pytest) ==="
	PYTHONPATH=src $(PYTEST) -v

test-frontend:
	@echo "=== Running Frontend Tests (Vitest Standalone) ==="
	@if command -v vitest >/dev/null 2>&1; then \
		echo "Executing: vitest run"; \
		vitest run; \
	else \
		echo "Error: Vitest is not installed globally. Please run 'make install-tools' first."; exit 1; \
	fi