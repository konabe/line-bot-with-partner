#!/usr/bin/env bash
set -euo pipefail

# Development environment setup script
# - creates a virtualenv in .venv (unless VENV_DIR is set)
# - activates it, installs dependencies, and installs pre-commit hooks

VENV_DIR=${VENV_DIR:-.venv}
PYTHON=${PYTHON:-python}

echo "Setting up development environment in ${VENV_DIR}"

if [ ! -d "${VENV_DIR}" ]; then
  ${PYTHON} -m venv "${VENV_DIR}"
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "Upgrading pip and installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt

echo "Installing pre-commit hooks..."
python -m pre_commit install
python -m pre_commit install --hook-type pre-push || true

echo "Done. Activate the venv with: source ${VENV_DIR}/bin/activate"
