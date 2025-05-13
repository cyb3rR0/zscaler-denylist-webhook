# Makefile for Zscaler Denylist Automation

# Set default Python interpreter
PYTHON := python3

# Create and activate virtual environment
venv:
	$(PYTHON) -m venv venv
	. venv/bin/activate

# Install all dependencies
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

# Run the FastAPI server locally
run:
	uvicorn webhook_server:app --host 0.0.0.0 --port 8080 --reload

# Run type checker (optional)
lint:
	$(PYTHON) -m pip install black flake8 isort
	black . && isort . && flake8 .

# Run tests (if you build them)
test:
	pytest tests/

# Remove virtualenv (optional cleanup)
clean:
	rm -rf venv __pycache__ .pytest_cache
