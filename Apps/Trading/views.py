

from django.forms import ValidationError
import httpx
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Order, Trade
from .serializer import OrderSerializer, WalletSerializer, TradeSerializer, TransactionSerializer
from django.db import transaction
import requests
import time
from Apps.Account.models import User, Wallet
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from datetime import datetime, timedelta
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
import json
import logging
logger = logging.getLogger(__name__)


class Trading(APIView):
    permission_classes = [AllowAny]

    def __init__(self):
        self.endpoint = "https://api.binance.com/api/v3/klines"
        self.params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 1  # Fetch the latest candlestick
        }
        self.wallet = None
        self.price_type = None

    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            order_type = request.data.get('order_type')
            symbol = request.data.get('symbol', 'BTCUSDT')
            price = float(request.data.get('price', 0))
            price_demo = request.data.get("tradeMode")
            # the_last_request =  request.data.get("last_request")
            if order_type not in ["buy", "sell"]:
                return Response({"error": "ประเภทคำสั่งไม่ถูกต้อง"}, status=status.HTTP_400_BAD_REQUEST)

            if price_demo:
                self.price_type = Order.DEMO_PRICE
            else:
                self.price_type = Order.REAL_PRICE

            # เรียกใช้ method process_trade สำหรับการเทรดทั้งแบบเดโมและจริง
            trade_result = self.process_trade(user, order_type, price, symbol, price_demo, self.price_type)

            return Response(trade_result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            return Response({"error": "เกิดข้อผิดพลาดในการดำเนินการคำสั่ง"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # if priceDemo is True:
            #     if order_type not in ["buy", "sell"]:
            #         return Response({"error": "ประเภทคำสั่งไม่ถูกต้อง"}, status=status.HTTP_400_BAD_REQUEST)

            #     if price <= 0:
            #         return Response({"error": "ราคาต้องมากกว่า 0"}, status=status.HTTP_400_BAD_REQUEST)
                
            #     self.wallet = self.get_user_wallet(user)
            #     if not self.validate_wallet_balance_demo(order_type, price):
            #         return Response({"error": "ยอดเงินไม่เพียงพอสำหรับคำสั่งนี้"}, status=status.HTTP_400_BAD_REQUEST)
            #     self.update_wallet_demo(order_type, price)
            #     self.wallet.save()
                
            #     order = Order.objects.create(
            #             user_id=user,
            #             order_type=order_type,
            #             price=price,
            #             status=Order.STATUS_PENDING,
            #             symbol=symbol,
            #             price_type = Order.DEMO_PRICE
            #         )
            #     if order_type in ["sell","SELL", "Sell"]:
                    
            #         # สะสมราคาใน cache
            #         cache_key_sell_demo = f"trade_{user.id}_price_total_sell_demo"
            #         trade_data = cache.get(cache_key_sell_demo, {"total_price": 0})
            #         trade_data["total_price"] += price
            #         cache.set(cache_key_sell_demo, trade_data)
                    
            #         last_request_cache_key_sell_demo = f"trade_{user.id}_last_request_sell_demo"
            #         cache.set(last_request_cache_key_sell_demo, {"total_price": trade_data["total_price"] , "symbol": symbol, "order_type": order_type})
                    
            #         self.get_next_candlestick_time()
                    
            #         last_candle_start_sell = self.fetch_candlestick_data_async(symbol, 2)
                    
            #         self.wait_1_scondes()
                    
            #         self.get_next_candlestick_time()
                    
            #         last_request_sell_demo = cache.get(last_request_cache_key_sell_demo)
                    
                    
            #         if last_request_sell_demo:
            #             total_price = last_request_sell_demo["total_price"]
            #             symbol = last_request_sell_demo["symbol"]
            #             order_type = last_request_sell_demo["order_type"]
            #             # ทำการ execute trade โดยใช้ข้อมูลจากคำขอล่าสุด
            #             trade_result_sell_demo = self.execute_trade(order_type, symbol, total_price)
            #             win_or_loss = self.calculate_trade_outcome_demo(order_type, symbol, last_candle_start_sell, total_price)
            #         else:
            #             trade_result_sell_demo = {"error": "ไม่มีข้อมูลคำขอล่าสุดใน cache"}
            #             win_or_loss = None
            #         # อัพเดทสถานะคำสั่ง
            #         order.status = Order.STATUS_COMPLETED
            #         order.save()
            #         # บันทึกการเทรดในฐานข้อมูล
            #         timestamp = timezone.now()
            #         Trade.objects.create(
            #             user_id=user,
            #             trade_type=order_type,
            #             price=total_price,  # ใช้ total_price แทน amountPrice
            #             timestamp=timestamp,
            #             status=Trade.STATUS_COMPLETED,
            #             symbol=symbol,
            #             price_type = Trade.DEMO_PRICE
            #         )
            #         # ส่งข้อมูลการเทรดผ่าน WebSocket
            #         trade_result_sell_demo["win_or_loss"] = win_or_loss
            #         channel_layer = get_channel_layer()
            #         cache.set(last_request_cache_key_sell, {"trade_result_sell_demo": trade_result_sell_demo})
            #         # print("trading_buy_sell", {f"user_id {user}, trade_data {trade_result_sell}"})
            #         try:
            #             async_to_sync(channel_layer.group_send)(
            #                 "trading_buy_sell",
            #                 {
            #                     'type': 'send_trade_update',
            #                     'trade_data': trade_result_sell_demo
            #                 }
            #             )
            #         except Exception as ws_error:
            #             # บันทึกข้อผิดพลาดของ WebSocket
            #             logger.error(f"WebSocket error: {ws_error}")
            #         cache.delete(cache_key_sell)
            #         cache.delete(last_request_cache_key_sell)
            #         return Response(trade_result_sell, status=status.HTTP_200_OK)
            #     if order_type in ["buy","BUY", "Buy"]:
                
            #         # สะสมราคาใน cache
            #         cache_key_buy = f"trade_{user.id}_price_total_buy_demo"
            #         trade_data = cache.get(cache_key_buy, {"total_price": 0})
            #         trade_data["total_price"] += price
            #         cache.set(cache_key_buy, trade_data)
            #         # print("wait for next candleww")
            #         last_request_cache_key_buy = f"trade_{user.id}_last_request_buy_demo"
            #         cache.set(last_request_cache_key_buy, {"total_price": trade_data["total_price"] , "symbol": symbol, "order_type": order_type})

            #         self.get_next_candlestick_time()
                    
            #         last_candle_start_buy = self.fetch_candlestick_data_async(symbol, 2)
                    
            #         self.wait_1_scondes()
                    
            #         self.get_next_candlestick_time()
                    
            #         last_request_buy = cache.get(last_request_cache_key_buy)
            #         if last_request_buy:
            #             total_price = last_request_buy["total_price"]
            #             symbol = last_request_buy["symbol"]
            #             order_type = last_request_buy["order_type"]
                        
            #             trade_result_buy_demo = self.execute_trade(order_type, symbol, total_price)
            #             win_or_loss = self.calculate_trade_outcome_demo(order_type, symbol, last_candle_start_buy, total_price)
            #         else:
            #             # กรณีที่ไม่มีข้อมูลใน cache
            #             trade_result_buy_demo = {"error": "ไม่มีข้อมูลคำขอล่าสุดใน cache"}
            #             win_or_loss = None
            #         # ทำการ execute trade
            #         # trade_result = self.execute_trade(order_type, symbol, total_price)
            #         # win_or_loss = self.calculate_trade_outcome(order_type, symbol, last_candle_start, total_price)
            #         # อัพเดทสถานะคำสั่ง
            #         order.status = Order.STATUS_COMPLETED
            #         order.save()
            #         # บันทึกการเทรดในฐานข้อมูล
            #         timestamp = timezone.now()
            #         Trade.objects.create(
            #             user_id=user,
            #             trade_type=order_type,
            #             price=total_price,  # ใช้ total_price แทน amountPrice
            #             timestamp=timestamp,
            #             status=Trade.STATUS_COMPLETED,
            #             symbol=symbol,
            #             price_type = Trade.DEMO_PRICE
            #         )
                    
            #         # ส่งข้อมูลการเทรดผ่าน WebSocket
            #         trade_result_buy_demo["win_or_loss"] = win_or_loss
            #         channel_layer = get_channel_layer()
            #         cache.set(last_request_cache_key_buy, {"trade_result_buy_demo": trade_result_buy_demo})
            #         # print("trading_buy_sell", {f"user_id {user}, trade_data {trade_result}"})
            #         try:
            #             async_to_sync(channel_layer.group_send)(
            #                 "trading_buy_sell",
            #                 {
            #                     'type': 'send_trade_update',
            #                     'trade_data': trade_result_buy_demo
            #                 }
            #             )
            #         except Exception as ws_error:
            #             # บันทึกข้อผิดพลาดของ WebSocket
            #             logger.error(f"WebSocket error: {ws_error}")
            #         cache.delete(cache_key_buy)
            #         cache.delete(last_request_cache_key_buy)
            #         return Response(trade_result_buy, status=status.HTTP_200_OK)
            

            # if priceDemo:
            #     if order_type not in ["buy", "sell"]:
            #         return Response({"error": "ประเภทคำสั่งไม่ถูกต้อง"}, status=status.HTTP_400_BAD_REQUEST)

            #     if price <= 0:
            #         return Response({"error": "ราคาต้องมากกว่า 0"}, status=status.HTTP_400_BAD_REQUEST)

            #     self.wallet = self.get_user_wallet(user)
            #     if not self.validate_wallet_balance_real(order_type, price):
            #         return Response({"error": "ยอดเงินไม่เพียงพอสำหรับคำสั่งนี้"}, status=status.HTTP_400_BAD_REQUEST)
            #     self.update_wallet_real(order_type, price)
            #     self.wallet.save()

            #     order = Order.objects.create(
            #             user_id=user,
            #             order_type=order_type,
            #             price=price,
            #             status=Order.STATUS_PENDING,
            #             symbol=symbol,
            #             price_type = Order.REAL_PRICE
            #         )
            #     if order_type in ["sell","SELL", "Sell"]:
            #         # สะสมราคาใน cache
            #         cache_key_sell = f"trade_{user.id}_price_total_sell"
            #         trade_data = cache.get(cache_key_sell, {"total_price": 0})
            #         trade_data["total_price"] += price
            #         cache.set(cache_key_sell, trade_data)
            #         # print("wait for next candleww")
            #         last_request_cache_key_sell = f"trade_{user.id}_last_request_sell"
            #         cache.set(last_request_cache_key_sell, {"total_price": trade_data["total_price"] , "symbol": symbol, "order_type": order_type})
            #         self.get_next_candlestick_time()
            #         last_candle_start_sell = self.fetch_candlestick_data_async(symbol, 2)
            #         self.wait_1_scondes()
            #         self.get_next_candlestick_time()
            #         # ดึงข้อมูลคำขอล่าสุดจาก cache
            #         last_request_sell = cache.get(last_request_cache_key_sell)
            #         if last_request_sell:
            #             total_price = last_request_sell["total_price"]
            #             symbol = last_request_sell["symbol"]
            #             order_type = last_request_sell["order_type"]
            #             # ทำการ execute trade โดยใช้ข้อมูลจากคำขอล่าสุด
            #             trade_result_sell = self.execute_trade(order_type, symbol, total_price)
            #             win_or_loss = self.calculate_trade_outcome_real(order_type, symbol, last_candle_start_sell, total_price)
            #         else:
            #             # กรณีที่ไม่มีข้อมูลใน cache
            #             trade_result = {"error": "ไม่มีข้อมูลคำขอล่าสุดใน cache"}
            #             win_or_loss = None
            #         # อัพเดทสถานะคำสั่ง
            #         order.status = Order.STATUS_COMPLETED
            #         order.save()
            #         # บันทึกการเทรดในฐานข้อมูล
            #         timestamp = timezone.now()
            #         Trade.objects.create(
            #             user_id=user,
            #             trade_type=order_type,
            #             price=total_price,  # ใช้ total_price แทน amountPrice
            #             timestamp=timestamp,
            #             status=Trade.STATUS_COMPLETED,
            #             symbol=symbol,
            #             price_type = Trade.REAL_PRICE
            #         )
            #         # ส่งข้อมูลการเทรดผ่าน WebSocket
            #         trade_result_sell["win_or_loss"] = win_or_loss
            #         channel_layer = get_channel_layer()
            #         cache.set(last_request_cache_key_sell, {"trade_result_sell": trade_result_sell})
            #         # print("trading_buy_sell", {f"user_id {user}, trade_data {trade_result_sell}"})
            #         try:
            #             async_to_sync(channel_layer.group_send)(
            #                 "trading_buy_sell",
            #                 {
            #                     'type': 'send_trade_update',
            #                     'trade_data': trade_result_sell
            #                 }
            #             )
            #         except Exception as ws_error:
            #             # บันทึกข้อผิดพลาดของ WebSocket
            #             logger.error(f"WebSocket error: {ws_error}")
            #         cache.delete(cache_key_sell)
            #         cache.delete(last_request_cache_key_sell)
            #         return Response(trade_result_sell, status=status.HTTP_200_OK)
                
            #     if order_type in ["buy","BUY", "Buy"]:
                
            #         # สะสมราคาใน cache
            #         cache_key_buy = f"trade_{user.id}_price_total_buy"
            #         trade_data = cache.get(cache_key_buy, {"total_price": 0})
            #         trade_data["total_price"] += price
            #         cache.set(cache_key_buy, trade_data)
            #         # print("wait for next candleww")
            #         last_request_cache_key_buy = f"trade_{user.id}_last_request_buy"
            #         cache.set(last_request_cache_key_buy, {"total_price": trade_data["total_price"] , "symbol": symbol, "order_type": order_type})
            #         # รอให้ข้อมูลอัพเดท (เช่น 2 นาที)
            #         # print("wait for next candle")
            #         self.get_next_candlestick_time()
            #         last_candle_start_buy = self.fetch_candlestick_data_async(symbol, 2)
            #         self.wait_1_scondes()
            #         self.get_next_candlestick_time()
            #         # ดึงข้อมูลคำขอล่าสุดจาก cache
            #         last_request_buy = cache.get(last_request_cache_key_buy)
            #         if last_request_buy:
            #             total_price = last_request_buy["total_price"]
            #             symbol = last_request_buy["symbol"]
            #             order_type = last_request_buy["order_type"]
            #             # ทำการ execute trade โดยใช้ข้อมูลจากคำขอล่าสุด
            #             trade_result_buy = self.execute_trade(order_type, symbol, total_price)
            #             win_or_loss = self.calculate_trade_outcome_real(order_type, symbol, last_candle_start_buy, total_price)
            #         else:
            #             # กรณีที่ไม่มีข้อมูลใน cache
            #             trade_result_buy = {"error": "ไม่มีข้อมูลคำขอล่าสุดใน cache"}
            #             win_or_loss = None
            #         # ทำการ execute trade
            #         # trade_result = self.execute_trade(order_type, symbol, total_price)
            #         # win_or_loss = self.calculate_trade_outcome(order_type, symbol, last_candle_start, total_price)
            #         # อัพเดทสถานะคำสั่ง
            #         order.status = Order.STATUS_COMPLETED
            #         order.save()
            #         # บันทึกการเทรดในฐานข้อมูล
            #         timestamp = timezone.now()
            #         Trade.objects.create(
            #             user_id=user,
            #             trade_type=order_type,
            #             price=total_price,  # ใช้ total_price แทน amountPrice
            #             timestamp=timestamp,
            #             status=Trade.STATUS_COMPLETED,
            #             symbol=symbol,
            #             price_type = Trade.REAL_PRICE
            #         )
            #         # ส่งข้อมูลการเทรดผ่าน WebSocket
            #         trade_result_buy["win_or_loss"] = win_or_loss
            #         channel_layer = get_channel_layer()
            #         cache.set(last_request_cache_key_buy, {"trade_result_buy": trade_result_buy})
            #         # print("trading_buy_sell", {f"user_id {user}, trade_data {trade_result}"})
            #         try:
            #             async_to_sync(channel_layer.group_send)(
            #                 "trading_buy_sell",
            #                 {
            #                     'type': 'send_trade_update',
            #                     'trade_data': trade_result_buy
            #                 }
            #             )
            #         except Exception as ws_error:
            #             # บันทึกข้อผิดพลาดของ WebSocket
            #             logger.error(f"WebSocket error: {ws_error}")
            #         cache.delete(cache_key_buy)
            #         cache.delete(last_request_cache_key_buy)
            #         return Response(trade_result_buy, status=status.HTTP_200_OK)

    def process_trade(self, user, order_type, price, symbol, price_demo, price_type):
        # the_last_request_number = int(the_last_request)
        
        if price <= 0:
            return Response({"error": "ราคาต้องมากกว่า 0"}, status=status.HTTP_400_BAD_REQUEST)

        self.wallet = self.get_user_wallet(user)
        
        if price_demo:
            if not self.validate_wallet_balance_demo(order_type, price):
                return Response({"error": "ยอดเงินไม่เพียงพอสำหรับคำสั่งนี้"}, status=status.HTTP_400_BAD_REQUEST)
            self.update_wallet_demo(price)
        else:
            if not self.validate_wallet_balance_real(order_type, price):
                return Response({"error": "ยอดเงินไม่เพียงพอสำหรับคำสั่งนี้"}, status=status.HTTP_400_BAD_REQUEST)
            self.update_wallet_real(price)

        self.wallet.save()

        order = Order.objects.create(
            user_id=user,
            order_type=order_type,
            price=price,
            status=Order.STATUS_PENDING,
            symbol=symbol,
            price_type=price_type
        )

        # ประมวลผลคำสั่งซื้อหรือขาย
        cache_key = f"trade_{user.id}_price_total_{order_type.lower()}_{price_type.lower()}"
        # print(cache_key)
        trade_data = cache.get(cache_key, {"total_price": 0})
        # print(f"Cache retrieved for {cache_key}: {trade_data}")
        trade_data["total_price"] += price
        cache.set(cache_key, trade_data)

        # กำหนดแคชสำหรับคำขอล่าสุด
        last_request_cache_key = f"trade_{user.id}_last_request_{order_type.lower()}_{price_type.lower()}"
        cache.set(last_request_cache_key, {"total_price": trade_data["total_price"], "symbol": symbol, "order_type": order_type})

        self.get_next_candlestick_time()
        
        last_candle_start = self.fetch_candlestick_data_async(symbol, 2)
        
        self.wait_1_scondes()
        
        self.get_next_candlestick_time()

        last_request = cache.get(last_request_cache_key)
        # print(f"Cache retrieved for {last_request_cache_key}: {last_request}")
        if last_request:
            total_price = last_request.get("total_price", 0)
            symbol = last_request.get("symbol")
            order_type = last_request.get("order_type")
            if total_price == 0 or not symbol or not order_type:
                return {"error": "Invalid cache data for last request"}
            # print("total_price", total_price , "symbol" , symbol , "order_type", order_type)
            trade_result = self.execute_trade(order_type, symbol, total_price)
            if price_demo:
                win_or_loss = self.calculate_trade_outcome_demo(order_type, symbol, last_candle_start, total_price)
            else:
                win_or_loss = self.calculate_trade_outcome_real(order_type, symbol, last_candle_start, total_price)
        else:
            trade_result = {"error": "ไม่มีข้อมูลคำขอล่าสุดในแคช"}
            win_or_loss = None

        # อัปเดตสถานะคำสั่ง
        order.status = Order.STATUS_COMPLETED
        order.save()

        # บันทึกการเทรดในฐานข้อมูล
        timestamp = timezone.now()
        Trade.objects.create(
            user_id=user,
            trade_type=order_type,
            price=total_price,
            timestamp=timestamp,
            status=Trade.STATUS_COMPLETED,
            symbol=symbol,
            price_type=price_type
        )

        # ส่งผลลัพธ์การเทรดผ่าน WebSocket
        trade_result["win_or_loss"] = win_or_loss
        channel_layer = get_channel_layer()
        cache.set(last_request_cache_key, {"trade_result": trade_result})
        print("trading_buy_sell", {f"user_id {user}, trade_data {trade_result}"})
        
        # ใช้ตัวล็อคหรือฟิลด์สถานะเพื่อตรวจสอบว่าได้ส่ง WebSocket ไปแล้วหรือยัง
        cache_key_lock = f"{last_request_cache_key}_lock"
        if not cache.get(cache_key_lock):
            try:
                # ส่งข้อมูลผ่าน WebSocket
                async_to_sync(channel_layer.group_send)(
                    "trading_buy_sell",
                    {
                        'type': 'send_trade_update',
                        'trade_data': trade_result  # ใช้เฉพาะผลลัพธ์ล่าสุด
                    }
                )
                # ตั้งล็อคเพื่อป้องกันการส่งซ้ำ
                cache.set(cache_key_lock, True, timeout=5)  # ล็อคไว้ 5 วินาที หรือเวลาที่เหมาะสม
                # ลบแคชเมื่อส่ง WebSocket สำเร็จ
                cache.delete(cache_key)
                cache.delete(last_request_cache_key)
            except Exception as ws_error:
                logger.error(f"WebSocket error: {ws_error}")
                # หากเกิดข้อผิดพลาด ไม่ลบแคชเพื่อเก็บข้อมูลสำหรับการ debug หรือ retry
        
        cache.delete(cache_key)
        cache.delete(last_request_cache_key)

        return trade_result
    
    
    def wait_1_scondes(self):
        time.sleep(3)

    def get_user_wallet(self, user):
        if user is None:
            raise ValidationError({"error": "ไม่พบกระเป๋าเงินของผู้ใช้งาน+2"})
        """ดึงข้อมูลกระเป๋าเงินของผู้ใช้"""
        try:
            return Wallet.objects.get(user_id=user)
        except Wallet.DoesNotExist:
            raise ValidationError({"error": "ไม่พบกระเป๋าเงินของผู้ใช้งาน"})
        
    @transaction.atomic
    def validate_wallet_balance_demo(self,order_type, price):
        """ตรวจสอบว่ายอดเงินในกระเป๋าเพียงพอหรือไม่"""
        if self.wallet.demo_balance < price:
            return False
        return True
    
    @transaction.atomic
    def validate_wallet_balance_real(self, order_type, price):
        """ตรวจสอบว่ายอดเงินในกระเป๋าเพียงพอหรือไม่"""
        if self.wallet.real_balance < price:
            return False
        return True
    
    
    def fetch_candlestick_data_async(self, symbol, start_close):
        start_close = int(start_close)
        self.params["symbol"] = symbol
        response = requests.get(self.endpoint, params=self.params)
        response.raise_for_status()
        data = response.json()
        return float(data[0][start_close])
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(self.endpoint, params={"symbol": symbol, "interval": "1m", "limit": 1})
        #     response.raise_for_status()
        #     return float(response.json()[0][start_close])

        
    def calculate_trade_outcome_real(self, order_type, symbol, last_candle_start, price):
        """คำนวณผลว่ากำไร ขาดทุน หรือเท่าทุน"""
        last_candle_close = self.fetch_candlestick_data_async(symbol,4)  # ดึงข้อมูลล่าสุด
        adjusted_price = price * 1.95  # ปรับกำไร/ขาดทุน


        if last_candle_close == last_candle_start:
            # print("before--",self.wallet.reserved)
            self.wallet.reserved -= price
            # print("after----",self.wallet.reserved)
            self.wallet.real_balance += price
            self.wallet.save()
            return "equal"

        elif order_type == "buy":
            if last_candle_close > last_candle_start:
                self.wallet.real_balance += adjusted_price
                # print("before", self.wallet.reserved)  # แสดงค่าก่อน
                self.wallet.reserved -= price
                # print("after before save", self.wallet.reserved)  # แสดงค่าหลังการลด
                self.wallet.save()
                self.wallet.refresh_from_db()  # รีเฟรชข้อมูลจากฐานข้อมูล
                # print("after save", self.wallet.reserved)  # แสดงค่าหลังจากการบันทึก
                return f"win = {adjusted_price}"
            else:
                # print("beforeพพพพพพพ222222222222222",self.wallet.reserved)
                self.wallet.reserved -= price
                # print("afteพพพพพพพพr222222",self.wallet.reserved)
                
                self.wallet.save()
                return "lose"

        elif order_type == "sell":
            if last_candle_close < last_candle_start:
                self.wallet.real_balance += adjusted_price
                # print("beforeพพพพพพพ",self.wallet.reserved)
                self.wallet.reserved -= price
                # print("afteพพพพพพพพr",self.wallet.reserved)
                self.wallet.save()
                return f"win = {adjusted_price}"
            else:
                # print("beforeพพพพพพพ222222222222222",self.wallet.reserved)
                self.wallet.reserved -= price
                # print("afteพพพพพพพพr222222",self.wallet.reserved)
                
                self.wallet.save()
                return "lose"
            
            
    def calculate_trade_outcome_demo(self, order_type, symbol, last_candle_start, price):
        """คำนวณผลว่ากำไร ขาดทุน หรือเท่าทุน"""
        last_candle_close = self.fetch_candlestick_data_async(symbol,4)  # ดึงข้อมูลล่าสุด
        adjusted_price = price * 1.95  # ปรับกำไร/ขาดทุน
        
        if last_candle_close == last_candle_start:
            self.wallet.demo_balance += price
            self.wallet.save()
            return "equal"

        elif order_type == "buy":
            if last_candle_close > last_candle_start:
                self.wallet.demo_balance += adjusted_price
                self.wallet.save()
                self.wallet.refresh_from_db()  # รีเฟรชข้อมูลจากฐานข้อมูล
                return f"win = {adjusted_price}"
            else:
                return "lose"

        elif order_type == "sell":
            if last_candle_close < last_candle_start:
                self.wallet.demo_balance += adjusted_price
                self.wallet.save()
                self.wallet.refresh_from_db()
                return f"win = {adjusted_price}"
            else:
                self.wallet.save()
                return "lose"


    def update_wallet_real(self, price):

        self.wallet.reserved += price
        self.wallet.real_balance -= price

        self.wallet.save()
        
    def update_wallet_demo(self, price):
        # print(f"wallet demo = {self.wallet.demo_balance}")
        self.wallet.demo_balance -= price
        self.wallet.save()
        # print(f"wallet demo update = {self.wallet.demo_balance}")
        
        
    def execute_trade(self, order_type, symbol, price):
        """ทำรายการโดยอัปเดตยอดในกระเป๋าเงินของผู้ใช้"""

        return {
            "order_type": order_type,
            "symbol": symbol,
            "price": price,
            "status": "success",
        }
    
    def get_next_candlestick_time(self):
        try:
            url = 'https://api.binance.com/api/v3/klines'
            params = {
                'symbol': "BTCUSDT", 
                'interval': '1m', 
                'limit': 2,  # Fetch the latest two candlesticks 
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if len(data) < 2:
                print("ข้อมูลแท่งเทียนไม่เพียงพอ", data)
                return

            # Get the second latest candlestick (we need the second one)
            latest_candlestick = data[1]  # Get the second latest candlestick
            latest_timestamp = latest_candlestick[0]

            # Calculate when the second candlestick will be complete
            next_candlestick_time = datetime.utcfromtimestamp(latest_timestamp / 1000) + timedelta(minutes=1)

            current_time = datetime.utcnow()
            time_diff = next_candlestick_time - current_time
            seconds_remaining = int(time_diff.total_seconds())

            if seconds_remaining > 0:
                minutes_remaining = seconds_remaining // 60
                seconds_only = seconds_remaining % 60
                print(f"แท่งเทียนถัดไปจะเสร็จใน {minutes_remaining} นาทีและ {seconds_only} วินาที")
                time.sleep(seconds_remaining)  # Wait for the second candlestick to complete
            else:
                print("The next candlestick time has already passed.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching candlestick data: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    

class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()  
    serializer_class = WalletSerializer  
    permission_classes = [IsAuthenticated]  

    def get_queryset(self):
        """
        ปรับแต่ง queryset เพื่อรองรับการกรองข้อมูลกระเป๋าเงินเฉพาะผู้ใช้งาน 
        หรือดึงข้อมูลกระเป๋าเงินทั้งหมด
        """
        
        user = self.request.user  # ดึงข้อมูลผู้ใช้ที่ผ่านการยืนยันตัวตน
        user_only = self.request.query_params.get('user_only', 'true').lower() == 'true'  # ตรวจสอบว่า user_only มีค่า true หรือไม่

        if user_only:
            # ดึงกระเป๋าเงินที่เกี่ยวข้องกับผู้ใช้ปัจจุบันเท่านั้น
            return Wallet.objects.filter(user_id=user)
        
        # ดึงกระเป๋าเงินทั้งหมด หากไม่ได้ระบุ user_only หรือระบุค่าเป็น false
        return Wallet.objects.all()
    
    
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()  
    serializer_class = TransactionSerializer  
    permission_classes = [IsAuthenticated]
    


