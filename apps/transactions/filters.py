import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='date', lookup_expr='lte')
    min_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    description = django_filters.CharFilter(field_name='description', lookup_expr='icontains')

    class Meta:
        model = Transaction
        fields = [
            'account', 'category', 'transaction_type',
            'is_recurring', 'currency',
            'start_date', 'end_date',
            'min_amount', 'max_amount', 'description',
        ]
