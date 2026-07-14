from .base import *  # noqa
import os

DEBUG = False
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

CORS_ALLOWED_ORIGINS = [
    "https://vagus-ai-s9s4.vercel.app",
    "https://vagus-ai-s9s4-git-main-navindra001s-projects.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True