from rest_framework import serializers
from .models import Account, NetWorthSnapshot
from decimal import Decimal


class AccountSerializer(serializers.ModelSerializer):
    is_liability = serializers.ReadOnlyField()
    transaction_count = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            'id', 'name', 'account_type', 'balance', 'currency',
            'institution_name', 'account_number_last4',
            'color', 'icon', 'is_active', 'include_in_total',
            'is_liability', 'transaction_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_transaction_count(self, obj):
        return obj.transactions.count()


class AccountCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            'name', 'account_type', 'balance', 'currency',
            'institution_name', 'account_number_last4',
            'color', 'icon', 'include_in_total',
        ]


class TransferSerializer(serializers.Serializer):
    from_account = serializers.UUIDField()
    to_account = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))
    description = serializers.CharField(max_length=255, default='Transfer')

    def validate(self, attrs):
        if attrs['from_account'] == attrs['to_account']:
            raise serializers.ValidationError('Cannot transfer to the same account.')
        return attrs


class NetWorthSerializer(serializers.Serializer):
    total_assets = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_liabilities = serializers.DecimalField(max_digits=14, decimal_places=2)
    net_worth = serializers.DecimalField(max_digits=14, decimal_places=2)
    accounts = AccountSerializer(many=True)


class NetWorthSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetWorthSnapshot
        fields = ['snapshot_date', 'total_assets', 'total_liabilities', 'net_worth']
