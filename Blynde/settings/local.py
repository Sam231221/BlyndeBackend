from Blynde.base import *
from decouple import config

DEBUG = True

SITE_ID = 1


ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
DJANGO_BASE_URL = config("DJANGO_BASE_URL")
FRONTEND_BASE_URL = config("FRONTEND_BASE_URL")

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://localhost:5173",
]
CSRF_TRUSTED_ORIGINS = [
    "https://blynde.up.railway.app",
    "https://blynde.netlify.app",
    "http://localhost:5173",
]


# CACHES = {
#     "default": {
#         "BACKEND": "django_redis.cache.RedisCache",
#         "LOCATION": env.str("REDIS_URL"),
#         "OPTIONS": {
#             "CLIENT_CLASS": "django_redis.client.DefaultClient",
#         },
#     }
# }
