# Software Mirror Monitoring & Benchmarking System (Mirror Monitor)

Mirror Monitor is a background daemon and real-time web dashboard designed to test, monitor, and benchmark package repository mirrors. Its primary goal is to automatically evaluate mirror infrastructure, measure network latency, and estimate effective bandwidth in order to optimize package downloads and improve development workflows in DevOps and software engineering environments.

## Key Features

- **Automated Scheduled Monitoring:** Periodically benchmarks mirrors in the background using APScheduler.
- **Real-Time On-Demand Testing:** Run live network benchmarks instantly from the web dashboard.
- **Intelligent Bandwidth Management:** Uses chunked streaming downloads from real mirror files to estimate throughput without consuming excessive network bandwidth.
- **Optimized Dashboard:** Modern TailwindCSS-based user interface featuring state locking mechanisms to prevent duplicate requests and unnecessary server load.
- **Independent Testing Layer:** Includes isolated unit tests for both Python backend logic and frontend JavaScript utilities, with a package.json-free frontend testing setup.

---

## Project Structure

```text
├── src/
│   ├── main.py            # Application entry point and FastAPI controller
│   ├── benchmarker.py     # Mirror benchmarking and network testing engine
│   ├── mirrors.json       # List of monitored mirrors
│   └── static/            # Frontend assets (HTML and JavaScript)
├── tests/
│   ├── backend/           # Backend unit tests using Pytest
│   │   └── test_monitor.py
│   └── frontend/          # Frontend unit tests using Vitest
│       └── dashboard.test.js
├── Dockerfile             # Docker image definition
├── eslint.config.js       # Global ESLint configuration (no package.json required)
├── Makefile               # Project automation tasks
├── requirements.txt       # Python dependencies
└── pyproject.toml         # Ruff configuration
```

## Installation & Setup Guide

The project can be deployed using either a native Python environment or a Docker container.

### Option 1: Local Deployment Using Make

**Prerequisites:**

- Python 3
- Node.js / npm
- GNU Make

#### 1. Install frontend development tools

Run the following command once to install linting and testing utilities:

```bash
make install-tools
```

#### 2. Create the virtual environment, install dependencies, and start the server

```bash
make run
```

Once the application starts, open your browser and navigate to:

```text
http://localhost:8000
```

### Option 2: Docker Deployment

**Prerequisites:**

- Docker Engine installed and running

#### 1. Build and start the container

```bash
make docker-run
```

#### 2. View container logs

```bash
make docker-logs
```

---

## Testing & Quality Assurance

The project includes independent testing layers for both backend and frontend components to ensure reliability, even under network failure scenarios.

### Backend Tests (Pytest)

Backend tests verify:

- Correctness of statistical summary calculations.
- Handling of edge cases where all mirrors are offline.
- Protection against critical runtime issues such as `ZeroDivisionError`.

### Frontend Tests (Vitest)

Frontend tests validate:

- Utility functions used by the dashboard.
- Automatic generation of operating-system configuration scripts.
- Execution within a mocked sandbox environment using Node.js's native `vm` module, without requiring a real browser.

Run tests using:

```bash
make test          # Run all backend and frontend tests
make test-backend  # Run Python tests only
make test-frontend # Run JavaScript tests only
```

---

## CLI Cheat Sheet

| Command | Description |
|----------|-------------|
| `make init` | Create the `.venv` virtual environment and install Python dependencies and testing tools. |
| `make install-tools` | Install frontend development tools globally (ESLint, Prettier, Vitest). |
| `make lint` | Run Ruff and ESLint static code analysis. |
| `make format` | Automatically format source code according to project standards. |
| `make clean` | Remove temporary files, Python cache directories, and the virtual environment. |
| `make docker-clean` | Stop and completely remove the project's Docker container and image. |

---

## Use Cases

Mirror Monitor is particularly useful for:

- Linux distribution mirror selection
- Package repository benchmarking
- DevOps infrastructure monitoring
- CI/CD environment optimization
- Network performance analysis
- Software repository performance evaluation
