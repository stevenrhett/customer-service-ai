# Clean Project
# Removes generated files and caches

echo "Cleaning backend..."
cd backend
rm -rf __pycache__ */__pycache__ */*/__pycache__
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf .coverage

echo "Cleaning frontend..."
cd ../frontend
rm -rf .next
rm -rf node_modules/.cache

echo "Clean complete! (node_modules and chroma_db preserved)"

