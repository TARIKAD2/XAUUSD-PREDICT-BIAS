import sys
sys.path.append('backend')
from app.core.config import get_settings
from pymongo import MongoClient

def main():
    settings = get_settings()
    if not settings.mongodb_uri:
        print('MongoDB configuration loaded: NO')
        print('MongoDB Atlas connection: FAIL')
        print('Ping result: FAIL (no URI)')
        return
    uri = settings.mongodb_uri.get_secret_value()
    print('MongoDB configuration loaded: YES')
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms)
        client.admin.command('ping')
        print('MongoDB Atlas connection: PASS')
        print('Ping result: PASS')
    except Exception as e:
        print('MongoDB Atlas connection: FAIL')
        print(f'Ping result: FAIL ({type(e).__name__}: {e})')

if __name__ == '__main__':
    main()

