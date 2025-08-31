# Redis Setup for Windows - Phase 4 Enhancement

## Quick Redis Setup Options

### Option 1: Redis for Windows (Recommended)
1. **Download**: https://github.com/microsoftarchive/redis/releases
2. **Install**: Run the MSI installer
3. **Start**: Redis will start automatically as a Windows service
4. **Verify**: Open Command Prompt and run `redis-cli ping` (should return PONG)

### Option 2: WSL2 + Redis (If you have WSL2)
```bash
# In WSL2 terminal
sudo apt update
sudo apt install redis-server
sudo service redis-server start
redis-cli ping
```

### Option 3: Portable Redis (No Installation)
1. **Download**: https://github.com/microsoftarchive/redis/releases (ZIP version)
2. **Extract** to a folder like `C:\redis`
3. **Run**: Double-click `redis-server.exe`
4. **Test**: Run `redis-cli.exe` and type `ping`

## Verify Redis is Working

Once Redis is running, test the connection:

```bash
# In project directory
python -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis is running and accessible!')
    r.set('test', 'Phase 4 Redis Setup')
    value = r.get('test').decode()
    print(f'✅ Redis read/write test: {value}')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    print('   Make sure Redis server is running on port 6379')
"
```

## Current Status Without Redis
The system is designed with graceful fallbacks:
- **Cache Manager**: Uses in-memory cache instead of Redis
- **Performance**: Still excellent for single-session use
- **Functionality**: All features work normally
- **Production**: Redis recommended for multi-user/persistent caching

To check current cache status:
```bash
python -c "
from services.cache_manager import get_cache_manager
cache = get_cache_manager()
health = cache.health_check()
print('Current Cache Type:', health.get('cache_type', 'unknown'))
print('Redis Available:', health.get('redis_available', False))
print('Memory Cache Enabled:', health.get('memory_cache_enabled', False))
"
```