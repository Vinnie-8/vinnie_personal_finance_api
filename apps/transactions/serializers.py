from rest_framework import serializers
from .models import Transaction
from apps.accounts.serializers import AccountSerializer
from apps.categories.serializers import CategoryChildSerializer
import csv
import io


class TransactionSerializer(serializers.ModelSerializer):
    account_detail = AccountSerializer(source='account', read_only=True)
    category_detail = CategoryChildSerializer(source='category', read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_detail',
            'destination_account',
            'category', 'category_detail',
            'transaction_type', 'amount', 'currency',
            'description', 'notes', 'date',
            'attachment', 'is_recurring', 'recurrence_rule', 'next_occurrence',
            'tags', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_account(self, account):
        user = self.context['request'].user
        if account.user != user:
            raise serializers.ValidationError('Account does not belong to you.')
        return account

    def validate(self, attrs):
        if attrs.get('transaction_type') == Transaction.TYPE_TRANSFER:
            if not attrs.get('destination_account'):
                raise serializers.ValidationError({'destination_account': 'Required for transfers.'})
        return attrs


class TransactionCreateSerializer(TransactionSerializer):
    class Meta(TransactionSerializer.Meta):
        fields = [
            'account', 'destination_account', 'category',
            'transaction_type', 'amount', 'currency',
            'description', 'notes', 'date',
            'attachment', 'is_recurring', 'recurrence_rule',
            'tags',
        ]


class BulkImportSerializer(serializers.Serializer):
    """Accepts a CSV file with columns: date,type,amount,description,category,account"""
    file = serializers.FileField()
    account = serializers.UUIDField()

    def validate_file(self, file):
        if not file.name.endswith('.csv'):
            raise serializers.ValidationError('Only CSV files are supported.')
        return file


class CategoryTotalSerializer(serializers.Serializer):
    category_id = serializers.UUIDField(allow_null=True)
    category_name = serializers.CharField()
    total = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class PeriodTotalSerializer(serializers.Serializer):
    period = serializers.CharField()
    income = serializers.DecimalField(max_digits=14, decimal_places=2)
    expense = serializers.DecimalField(max_digits=14, decimal_places=2)
    net = serializers.DecimalField(max_digits=14, decimal_places=2)
