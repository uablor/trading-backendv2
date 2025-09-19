import json
import asyncio
import time
from channels.generic.websocket import AsyncWebsocketConsumer
from binance.client import Client
from binance.streams import BinanceSocketManager
from channels.layers import get_channel_layer
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime, timedelta
import requests
from channels.db import database_sync_to_async
from django.apps import apps
from django.core.cache import cache
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import AnonymousUser

from Apps.Account.models import User

class KlineConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'klines'
        self.room_group_name = f'ws_{self.room_name}'
        
        # Join WebSocket group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept WebSocket connection
        await self.accept()
        
        # Initialize Binance API client
        self.client = Client(api_key='', api_secret='')
        
        # Initialize BinanceSocketManager
        self.bsm = BinanceSocketManager(self.client)
        
        # Start Kline Stream (BTC/USDT 1m)
        self.socket = self.bsm.kline_socket('BTCUSDT', interval='1m')
        
        # Run WebSocket stream in background
        asyncio.create_task(self.run_socket())

    async def run_socket(self):
        try:
            async with self.socket as socket_manager:
                while True:
                    message = await socket_manager.recv()
                    if message:
                        await self.handle_kline_data(message)
        except Exception as e:
            print(f"Error in run_socket: {e}")
            await self.close()

    async def disconnect(self, close_code):
        # Leave WebSocket group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Stop Kline Stream
        if hasattr(self, 'socket'):
        # Close the socket if necessary (this may depend on the library version)
            try:
                await self.socket.close()  # If the socket has this method
            except AttributeError:
            # If the socket does not have the close method, just pass
                pass

    async def handle_kline_data(self, data):
        try:
            kline = data.get('k', {})  # Binance ส่ง kline data ใน 'k' key
            kline_data = {
                'time': kline.get('t', 0) // 1000,  # แปลง timestamp เป็นวินาที
                'open': float(kline.get('o', 0)),
                'high': float(kline.get('h', 0)),
                'low': float(kline.get('l', 0)),
                'close': float(kline.get('c', 0)),
                'volume': float(kline.get('v', 0))  # เพิ่ม volume
            }
            
            await self.send_kline_data_to_group(kline_data)
        except Exception as e:
            print(f"Error processing kline data: {e}")

    async def send_kline_data(self, event):
        # This method is called when group_send is called
        try:
            await self.send(text_data=json.dumps({
                'klines': event['data']
            }))
        except Exception as e:
            print(f"Error sending kline data: {e}")

    async def send_kline_data_to_group(self, data):
        try:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_kline_data',
                    'data': data
                }
            )
        except Exception as e:
            print(f"Error sending to group: {e}")
    
            
class CandlestickConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_name = "candlestick_room"
        self.room_group_name = f"candlestick_{self.room_name}"

        # เข้าร่วมกลุ่ม
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # เริ่มลูปเพื่อส่งเวลาแท่งเทียนถัดไปทุกๆ วินาที
        self.send_next_candlestick_time_task = asyncio.create_task(self.send_next_candlestick_time())

    async def disconnect(self, close_code):
        # ยกเลิกงานเมื่อ WebSocket ถูกตัดการเชื่อมต่อ
        self.send_next_candlestick_time_task.cancel()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def send_next_candlestick_time(self):
        try:
          
            
            
            while True:
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

                    # ส่งข้อมูลเวลาที่เหลือของแท่งเทียนถัดไปและสถานะปุ่ม
                if seconds_left > 0:
                    await self.send(text_data=json.dumps({
                        'next_candlestick_time': f"{seconds_left}s",
                        'is_button_enter': is_button_enter
                    }))

                # รอ 0.2 วินาทีก่อนดึงข้อมูลใหม่
                await asyncio.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"เกิดข้อผิดพลาดในการดึงข้อมูลแท่งเทียน: {e}")
        except Exception as e:
            print(f"เกิดข้อผิดพลาด: {e}")


    async def receive(self, text_data):
        # เมธอดนี้ยังสามารถใช้จัดการข้อความอื่นๆ ที่ส่งมาจาก frontend
        data = json.loads(text_data)

        if data.get('request_next_candlestick_time'):
            # ส่งเวลาแท่งเทียนถัดไปตามคำขอ
            await self.send_next_candlestick_time()


class WalletConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        # ตรวจสอบว่า headers มี authorization หรือไม่
        headers = dict(self.scope.get('headers', []))  # Convert headers list to dictionary
        token = headers.get('authorization', None)
        print(f"Token: {token}")
        # print(f"Headers: {headers}")
        if token:
            # ลบคำว่า 'Bearer ' ออกถ้ามี
            token = token[7:] if token.startswith('Bearer ') else token

            try:
                # ถอดรหัส token และยืนยันตัวตนของผู้ใช้
                access_token = AccessToken(token)
                user = await database_sync_to_async(access_token.payload.get)('user_id')
                self.scope['user'] = await database_sync_to_async(User.objects.get)(id=user)
            except Exception as e:
                print(f"เกิดข้อผิดพลาดในการยืนยันตัวตนผู้ใช้: {e}")
                self.scope['user'] = AnonymousUser()

        else:
            self.scope['user'] = AnonymousUser()

        if isinstance(self.scope['user'], AnonymousUser):
            await self.close()  # ปฏิเสธการเชื่อมต่อหากเป็นผู้ใช้ที่ไม่รู้จัก

        self.room_group_name = "wallet_update"
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # ออกจากกลุ่ม WebSocket
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # รับข้อมูลจาก WebSocket (ถ้ามี)
        text_data_json = json.loads(text_data)
        action = text_data_json.get("action", None)

        # ถ้าต้องการให้เช็คหรือรับข้อมูลจาก WebSocket
        if action == "fetch_wallet":
            wallet_data = await self.get_wallet_data()
            await self.send(text_data=json.dumps({
                "wallet": wallet_data
            }))

    @database_sync_to_async
    def get_wallet_data(self):
        user = self.scope.get("user")
        print(f"User: {user}")
        self.Wallet = apps.get_model('Account', 'Wallet')

        # ดึงข้อมูลจากฐานข้อมูล
        wallet = self.Wallet.objects.filter(user_id=user.id).first()
        
        print(f"Wallet data: {wallet}")  # พิมพ์ข้อมูล
        return {
            "real_balance": wallet.real_balance,
            "demo_balance": wallet.demo_balance
        }

    async def send_wallet_update(self, event):
        # print("sending to ...")
        # ส่งการอัปเดตข้อมูลไปยัง WebSocket
        # print("Event data:", event['wallet'])
        await self.send(text_data=json.dumps({
            "wallet": event['wallet']
        }))
        # print("send to done...")
        

class TradingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = "buy_sell"
        self.room_group_name = f'trading_{self.room_name}'
        print(f"Connecting to room: {self.room_group_name}")

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        print(f"Disconnecting from room: {self.room_group_name}")
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        print(f"Received message: {text_data}")
        data = json.loads(text_data)
        order_type = data.get('order_type')
        price = data.get('price')
        symbol = data.get('symbol')

        # Process order logic (you can call the trading logic here)
        # For example, simulate trade execution:
        response = {
        'status': 'success',
        'order_type': order_type,
        'price': price,
        'symbol': symbol,
        "win_or_loss":"equal"
        }

    # Send response to WebSocket
        await self.send(text_data=json.dumps(response))  # Corrected json.dumps() syntax


    # Send message to WebSocket
    async def send_trade_update(self, event):
        trade_data = event['trade_data']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(trade_data))
        
