#!/bin/bash

# W4L (Wispr for Linux) - Development Environment Setup
# This script sets up a virtual environment using pyenv Python

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the project root
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the W4L project root directory"
    exit 1
fi

print_status "Setting up W4L development environment..."

# Check if pyenv is available
if ! command -v pyenv &> /dev/null; then
    print_error "pyenv is not installed or not in PATH"
    print_status "Please install pyenv first: https://github.com/pyenv/pyenv"
    exit 1
fi

# Get current Python version
CURRENT_PYTHON=$(python --version 2>&1 | cut -d' ' -f2)
print_status "Current Python version: $CURRENT_PYTHON"

# Check if we're using pyenv Python
if ! pyenv version-name &> /dev/null; then
    print_warning "Not using pyenv Python. Current Python: $(which python)"
else
    PYENV_VERSION=$(pyenv version-name)
    print_status "Using pyenv Python: $PYENV_VERSION"
fi

# Virtual environment name
VENV_NAME="w4l_env"
VENV_PATH="./$VENV_NAME"

# Remove existing virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    print_status "Removing existing virtual environment..."
    rm -rf "$VENV_PATH"
fi

# Create virtual environment
print_status "Creating virtual environment: $VENV_NAME"
python -m venv "$VENV_NAME"

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
print_status "Installing production dependencies..."
if ! pip install -r requirements.txt; then
    print_warning "Some production dependencies failed to install"
    print_status "This is normal for some platform-specific packages"
    print_status "Continuing with available packages..."
fi

# Install development dependencies
print_status "Installing development dependencies..."
if ! pip install -r requirements-dev.txt; then
    print_warning "Some development dependencies failed to install"
    print_status "Continuing with available packages..."
fi

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ] && [ -f "env.example" ]; then
    print_status "Creating .env file from env.example..."
    cp env.example .env
    print_warning "Please review and customize .env file for your setup"
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p ~/.config/w4l/logs
mkdir -p ~/.config/w4l/models

# Set up pre-commit hooks
print_status "Setting up pre-commit hooks..."
pre-commit install

print_success "W4L development environment setup complete!"
echo ""
print_status "To activate the environment, run:"
echo "  source $VENV_PATH/bin/activate"
echo ""
print_status "To run the application:"
echo "  python -m src.main"
echo ""
print_status "To run tests:"
echo "  pytest"
echo ""
print_status "To format code:"
echo "  black src/"
echo ""
print_status "To lint code:"
echo "  flake8 src/" 