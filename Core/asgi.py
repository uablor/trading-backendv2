import os
import django
from dotenv import load_dotenv

load_dotenv()
# Set the default settings module for the 'django' program.
if os.getenv('DJANGO_ENV') == 'prod':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'Core.Settings.prod')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.Settings.dev')

# Ensure that Django is set up as early as possible
django.setup()



from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from .routing import websocket_urlpatterns  # อย่าลืม import websocket_urlpatterns


# load_dotenv()
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Core.settings.dev')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # เพิ่มเส้นทาง WebSocket ที่เชื่อมต่อกับ consumers
        )
    ),
})
