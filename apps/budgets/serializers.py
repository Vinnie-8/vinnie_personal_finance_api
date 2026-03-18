from rest_framework import serializers
from .models import Budget
from decimal import Decimal
import datetime


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.SerializerMethodField()
    remaining = serializers.SerializerMethodField()
    percentage_used = serializers.SerializerMethodField()
    is_over_threshold = serializers.SerializerMethodField()
    period_start = serializers.SerializerMethodField()
    period_end = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)

    class Meta:
        model = Budget
        fields = [
            'id', 'name', 'category', 'category_name',
            'amount', 'period', 'start_date', 'end_date',
            'alert_threshold', 'is_active', 'rollover',
            'spent', 'remaining', 'percentage_used',
            'is_over_threshold', 'period_start', 'period_end',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_spent(self, obj):
        return obj.get_spent()

    def get_remaining(self, obj):
        return obj.amount - obj.get_spent()

    def get_percentage_used(self, obj):
        spent = obj.get_spent()
        if obj.amount == 0:
            return 0
        return round(float(spent / obj.amount * 100), 2)

    def get_is_over_threshold(self, obj):
        spent = obj.get_spent()
        return spent >= (obj.amount * obj.alert_threshold)

    def get_period_start(self, obj):
        return obj.get_period_dates()[0]

    def get_period_end(self, obj):
        return obj.get_period_dates()[1]


class BudgetProgressSerializer(serializers.Serializer):
    """Detail progress with daily burn rate and projections."""
    budget = BudgetSerializer()
    days_elapsed = serializers.IntegerField()
    days_remaining = serializers.IntegerField()
    total_days = serializers.IntegerField()
    daily_burn_rate = serializers.DecimalField(max_digits=14, decimal_places=2)
    projected_total = serializers.DecimalField(max_digits=14, decimal_places=2)
    projected_overspend = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
