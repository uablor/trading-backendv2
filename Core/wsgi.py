"""
WSGI config for Core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv

load_dotenv()

from django.core.wsgi import get_wsgi_application

if os.getenv('DJANGO_ENV') == 'prod':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.Settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE','Core.Settings.dev')


application = get_wsgi_application()
