from .common import *

DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
if DEBUG:
    ALLOWED_HOSTS = ['*']

else:
    ALLOWED_HOSTS = ['localhost:8000','127.0.0.1:8000']

# SQLite database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Channels + Redis (Upstash free tier)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
             "CONFIG": {
            "hosts": [('127.0.0.1',6379)],  # ที่อยู่ของ Redis server
            "capacity": 1000,  # เพิ่มขนาด queue
            "expiry": 10,      # เวลาหมดอายุของข้อความ (วินาที)
        },
    },
}