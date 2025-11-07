# Verify Data Ingestion
# Verifies that ChromaDB collections exist and contain data

cd backend && python -c "
import chromadb
from app.config import get_settings

settings = get_settings()
client = chromadb.PersistentClient(path=settings.chroma_persist_directory)

collections = ['billing', 'technical', 'policy']
print('=== Verifying Data Ingestion ===\n')

for coll_name in collections:
    try:
        collection = client.get_collection(coll_name)
        count = collection.count()
        print(f'✓ {coll_name}: {count} chunks')
    except Exception as e:
        print(f'✗ {coll_name}: Not found - {e}')

print('\n=== Verification Complete ===')
"

