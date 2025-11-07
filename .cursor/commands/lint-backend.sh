# Run Linter
# Runs linting checks on backend Python code

cd backend && python -m flake8 app/ --max-line-length=120 --exclude=__pycache__,*.pyc || echo "Install flake8: pip install flake8"

