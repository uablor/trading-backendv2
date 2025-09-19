from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/klines/', consumers.KlineConsumer.as_asgi()),
    re_path(r'ws/candlestick/', consumers.CandlestickConsumer.as_asgi()),
    re_path(r'ws/wallet/', consumers.WalletConsumer.as_asgi()),
    re_path(r'ws/trading/', consumers.TradingConsumer.as_asgi()),
]