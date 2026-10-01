import sys, asyncio
sys.path.append('backend')
from app.core.config import get_settings
from pymongo import MongoClient

async def main():
    settings = get_settings()
    # Environment check
    env_ok = 'PASS' if (settings.mongodb_uri and settings.database_name) else 'FAIL'
    print(f'ENVIRONMENT configuration: {env_ok}')
    if not settings.mongodb_uri:
        print('MONGODB connection: FAIL')
        return
    uri = settings.mongodb_uri.get_secret_value()
    client = MongoClient(uri, serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms)
    try:
        client.admin.command('ping')
        print('MongoDB connection: PASS')
        print('MongoDB ping: PASS')
        db = client[settings.database_name]
        # list collections (read-only)
        cols = db.list_collection_names()
        print(f'Collections access: PASS ({len(cols)} collections)')
        # attempt a simple read from first collection if exists
        if cols:
            coll = db[cols[0]]
            try:
                doc = coll.find_one()
                print('Read access: PASS')
            except Exception as e:
                print(f'Read access: FAIL ({type(e).__name__})')
        else:
            print('Read access: NO_DATA')
    except Exception as e:
        print(f'MongoDB connection: FAIL ({type(e).__name__}: {e})')
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(main())

