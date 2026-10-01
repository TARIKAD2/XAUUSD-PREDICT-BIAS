import sys, asyncio
sys.path.append('backend')
from app.core.config import get_settings
from app.db.client import MongoClientManager

async def main():
    settings = get_settings()
    config_loaded = 'YES' if settings else 'NO'
    manager = MongoClientManager(settings)
    connected = await manager.connect()
    connection_status = 'PASS' if connected else 'FAIL'
    ping_status = 'FAIL'
    if connected:
        try:
            await manager._client.admin.command('ping')
            ping_status = 'PASS'
        except Exception as e:
            ping_status = f'FAIL: {type(e).__name__}: {str(e)}'
    await manager.disconnect()
    print(f"MongoDB configuration loaded: {config_loaded}")
    print(f"MongoDB Atlas connection: {connection_status}")
    print(f"Ping result: {ping_status}")

if __name__ == '__main__':
    asyncio.run(main())

