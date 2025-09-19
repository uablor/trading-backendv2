# Chart/views.py
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.views import status
import time
from django.core.cache import cache


class KlineDataView(APIView):
    def get(self, request):
        # Fetch data from Binance API
        endpoint = "https://api.binance.com/api/v3/klines"
        params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 1000
        }
        response = requests.get(endpoint, params=params)
        data = response.json()

        # Process the data for chart display
        processed_data = [
            {
                "time": int(d[0] / 1000),
                "open": float(d[1]),
                "high": float(d[2]),
                "low": float(d[3]),
                "close": float(d[4]),
                "volume": float(d[5]),
            }
            for d in data
        ]

        # Send data to WebSocket group
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'ws_klines',  # Group name must match the consumer
            {
                'type': 'send_kline_data',  # Custom type to trigger a specific function in consumer
                'data': processed_data
            }
        )

        return Response(processed_data)


class TradeView(APIView):
    
    def __init__(self):
        self.endpoint = "https://api.binance.com/api/v3/klines"
        self.params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 1  # Fetch the latest candlestick
        }
        
    def post(self, request):
        action = request.data.get('action')  # "buy" or "sell"
        symbol = request.data.get('symbol', 'BTCUSDT')  # Default symbol
        quantity = request.data.get('quantity', 0)
        quantity = float(quantity)

        if action not in ["buy", "sell"]:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

        if quantity <= 0:
            return Response({"error": "Quantity must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

        response = requests.get(self.endpoint, params=self.params)
        data = response.json()

        # Get the closing price of the last candlestick
        last_candle_start = float(data[0][2])  # open price is at index 4
        # Simulate waiting for the next candle (in real application, this would be replaced by a time check)
        current_time = int(time.time())
        seconds_in_current_minute = current_time % 60
        time_to_wait = 60 - seconds_in_current_minute  # Time remaining until the next candle
        time.sleep(time_to_wait)  # Wait until the next candle close

        # Perform the trade
        result = self.execute_trade(action, symbol, quantity)

        # Calculate profit/loss
        win_or_loss = self.check_win_or_loss(action, symbol, last_candle_start, quantity)

        result['win_or_loss'] = win_or_loss
        return Response(result, status=status.HTTP_200_OK)

    def execute_trade(self, action, symbol, quantity):
        Is_quantity = quantity + (quantity * 0.95)
        # Simulate trade execution
        price = self.get_market_price(symbol)  # Get market price from API or mock data
        return {
            "action": action,
            "symbol": symbol,
            "quantity": Is_quantity,
            "price": price,
            "status": "success"
        }

    def get_market_price(self, symbol):
        # Simulate fetching market price
        return 50000.00  # Mocked market price (replace with real API call)

    def check_win_or_loss(self, action, symbol, last_candle_start, quantity):
        # Fetch the most recent candlestick data from a market API (e.g., Binance)

        response = requests.get(self.endpoint, params=self.params)
        data = response.json()

        # Get the closing price of the last candlestick
        last_candle_close = float(data[0][4])  # Close price is at index 4

        # Determine profit or loss
        if last_candle_close == last_candle_start:
            return "equal"
        if action == 'buy':
            if last_candle_close > last_candle_start:
                return "win"
            else:
                return "lose"
        elif action == 'sell':
            if last_candle_close < last_candle_start:
                return "win"
            else:
                return "lose"


class TimeUntilNextCandlestickView(APIView):
    def get(self, request):
        current_time = int(time.time())  # เวลาปัจจุบันในหน่วยวินาทีจาก Unix epoch
        seconds_in_current_minute = current_time % 60
        seconds_left = 60 - seconds_in_current_minute  # เวลาที่เหลือจนถึงนาทีถัดไป
                # Get the current state of is_button_enter from cache, default to False
        is_button_enter = cache.get('is_button_enter', False)
        last_toggled = cache.get('last_toggled', 0)
        # print(f"ก่อนการสลับสถานะ: is_button_enter={is_button_enter}")
        
        # สลับสถานะเมื่อ seconds_left == 60 และไม่ได้สลับเมื่อเร็วเกินไป
        if seconds_left == 60 and current_time != last_toggled:
            is_button_enter = not is_button_enter
            cache.set('is_button_enter', is_button_enter)
            cache.set('last_toggled', current_time)
            # print(f"หลังการสลับสถานะ: is_button_enter={is_button_enter}")
            
            
        return Response({"seconds_left": seconds_left ,"is_button_enter" : is_button_enter})

class get_next_candlestick_time(APIView):
    def get(self, request):
        try:
            url = f'https://api.binance.com/api/v3/klines'
            params = {
                'symbol': "BTCUSDT", 
                'interval': '1m', 
                'limit': 1, 
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            if not data:
                return Response({"error": "No data found for this symbol"}, status=404)

            latest_candlestick = data[0]
            latest_timestamp = latest_candlestick[0]  # timestamp ของแท่งเทียนล่าสุด

            # คำนวณเวลาแท่งเทียนถัดไป
            next_candlestick_time = datetime.utcfromtimestamp(latest_timestamp / 1000) + timedelta(minutes=1)

            # เวลาในปัจจุบัน
            current_time = datetime.utcnow()

            # คำนวณเวลาที่เหลือ (ต่างกันระหว่างเวลาปัจจุบันกับเวลาแท่งเทียนถัดไป)
            time_diff = next_candlestick_time - current_time
            seconds_remaining = int(time_diff.total_seconds())
            minutes_remaining = seconds_remaining // 60
            seconds_only = seconds_remaining % 60

            # ส่งข้อมูลกลับไป
            return Response({
                # 'next_candlestick_time': next_candlestick_time.isoformat(),
                # 'minutes_remaining': minutes_remaining,
                # 'seconds_remaining': seconds_remaining,
                'seconds_only': seconds_only
            })

        except requests.exceptions.RequestException as e:
            # กรณีเกิดข้อผิดพลาดในการเชื่อมต่อกับ API
            return Response({"error": str(e)}, status=500)