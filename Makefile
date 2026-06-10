# Variables
PYTHON = .venv/bin/python
PIP = .venv/bin/pip
IMAGE_NAME = mirror-monitor
CONTAINER_NAME = mirror-app

.PHONY: init run clean docker-build docker-run docker-logs docker-clean

# ۱. آماده‌سازی محیط مجازی و نصب وابستگی‌ها
init:
	@echo "Creating virtual environment and installing dependencies..."
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# ۲. اجرای پروژه در محیط بومی پایتون
run:
	@if [ ! -d ".venv" ]; then make init; fi
	@echo "Starting Mirror Monitor application..."
	$(PYTHON) main.py

# ۳. ساخت ایمیج داکر
docker-build:
	@echo "Building Docker image [$(IMAGE_NAME)]..."
	docker build -t $(IMAGE_NAME) .

# ۴. اجرای برنامه داخل کانتینر داکر
docker-run:
	@echo "Stopping existing containers if any..."
	@docker rm -f $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Running Docker container [$(CONTAINER_NAME)] on port 8000..."
	docker run -d -p 8000:8000 --name $(CONTAINER_NAME) $(IMAGE_NAME)

# ۵. مشاهده لاگ‌های داکر
docker-logs:
	docker logs -f $(CONTAINER_NAME)

# ۶. پاکسازی محیط داکر
docker-clean:
	@echo "Cleaning up Docker container and image..."
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

# ۷. پاکسازی عمومی پروژه
clean:
	@echo "Cleaning temporary python cache files and .venv..."
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
