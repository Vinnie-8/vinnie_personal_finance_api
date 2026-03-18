from rest_framework import serializers
from .models import Category


class CategoryChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'category_type', 'is_system']


class CategorySerializer(serializers.ModelSerializer):
    children = CategoryChildSerializer(many=True, read_only=True)
    transaction_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            'id', 'name', 'icon', 'color', 'category_type',
            'parent', 'is_system', 'children',
            'transaction_count', 'total_spent', 'created_at',
        ]
        read_only_fields = ['id', 'is_system', 'created_at']

    def get_transaction_count(self, obj):
        return obj.transactions.count() if hasattr(obj, 'transactions') else 0

    def get_total_spent(self, obj):
        from django.db.models import Sum
        total = obj.transactions.aggregate(s=Sum('amount'))['s']
        return total or 0


class CategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'icon', 'color', 'category_type', 'parent']

    def validate_parent(self, parent):
        user = self.context['request'].user
        if parent and parent.user != user:
            raise serializers.ValidationError('Parent category does not belong to you.')
        return parent
