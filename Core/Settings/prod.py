from .common import *
import dj_database_url

DEBUG = os.getenv("DEBUG", "False").lower == "true"

if DEBUG:
    ALLOWED_HOSTS = ['*']

else:
    ALLOWED_HOSTS = ['*']

DATABASES = {
    "default": dj_database_url.config(default=os.environ.get("DATABASE_URL"))
}

# Channels + Redis (Upstash free tier)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
             "CONFIG": {
            "hosts": [os.environ["REDIS_URL"]], # ที่อยู่ของ Redis server('127.0.0.1',6379)], 
            "capacity": 1000,  # เพิ่มขนาด queue
            "expiry": 10,      # เวลาหมดอายุของข้อความ (วินาที)
        },
    },
}

