from rest_framework import serializers
from .models import Order, Trade, Transaction
from Apps.Account.models import Wallet


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'user_id', 'order_type', 'price', 'created_at', 'status']

class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = ['id', 'trade_type', 'price', 'created_at', 'status', 'timestamp', 'user']


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'user', 'amount', 'transaction_date', 'status']
        
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'currency', 'demo_balance','real_balance','last_updated', 'reserved']

    def update(self, instance, validated_data):
        validated_data.pop("wallet_id", None)
        return super().update(instance, validated_data)

