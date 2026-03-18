from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils.dateparse import parse_date
from django.utils import timezone
import csv
import io
from decimal import Decimal

from .models import Transaction
from .serializers import (
    TransactionSerializer, TransactionCreateSerializer,
    BulkImportSerializer,
)
from .filters import TransactionFilter


class TransactionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/transactions/ — paginated list with filters
    POST /api/transactions/ — record new transaction
    """
    filterset_class = TransactionFilter
    search_fields = ['description', 'notes', 'tags']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_serializer_class(self):
        return TransactionCreateSerializer if self.request.method == 'POST' else TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            'account', 'category', 'destination_account'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/transactions/<id>/
    PUT    /api/transactions/<id>/
    DELETE /api/transactions/<id>/ — reverses balance
    """
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        old_amount = instance.amount
        old_type = instance.transaction_type

        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Reverse old balance change, apply new
        instance._apply_balance_change(-old_amount)
        updated = serializer.save()
        updated._apply_balance_change(updated.amount)

        return Response(TransactionSerializer(updated, context={'request': request}).data)


class BulkImportView(APIView):
    """POST /api/transactions/bulk/ — import transactions from CSV"""
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = BulkImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from apps.accounts.models import Account
        account = get_object_or_404(Account, pk=serializer.validated_data['account'], user=request.user)

        csv_file = serializer.validated_data['file']
        decoded = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))

        created, errors = [], []
        for i, row in enumerate(reader, start=2):
            try:
                tx = Transaction.objects.create(
                    user=request.user,
                    account=account,
                    date=parse_date(row['date'].strip()),
                    transaction_type=row.get('type', 'expense').strip().lower(),
                    amount=Decimal(row['amount'].strip().replace(',', '')),
                    description=row.get('description', '').strip(),
                    currency=row.get('currency', account.currency).strip(),
                )
                created.append(str(tx.id))
            except Exception as e:
                errors.append({'row': i, 'error': str(e)})

        return Response({
            'created': len(created),
            'errors': errors,
            'transaction_ids': created,
        }, status=status.HTTP_207_MULTI_STATUS)


class CategoryBreakdownView(APIView):
    """GET /api/transactions/by-category/?start=&end=&type=expense"""

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user)
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        tx_type = request.query_params.get('type', Transaction.TYPE_EXPENSE)

        if start:
            qs = qs.filter(date__gte=parse_date(start))
        if end:
            qs = qs.filter(date__lte=parse_date(end))
        qs = qs.filter(transaction_type=tx_type)

        total = qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        breakdown = (
            qs.values('category__id', 'category__name')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )
        results = []
        for item in breakdown:
            results.append({
                'category_id': item['category__id'],
                'category_name': item['category__name'] or 'Uncategorised',
                'total': item['total'],
                'count': item['count'],
                'percentage': float(item['total'] / total * 100) if total else 0,
            })
        return Response({'total': total, 'breakdown': results})


class PeriodBreakdownView(APIView):
    """GET /api/transactions/by-period/?period=monthly&start=&end="""

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user)
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        period = request.query_params.get('period', 'monthly')

        if start:
            qs = qs.filter(date__gte=parse_date(start))
        if end:
            qs = qs.filter(date__lte=parse_date(end))

        trunc_map = {'daily': 'day', 'weekly': 'week', 'monthly': 'month', 'yearly': 'year'}
        trunc = trunc_map.get(period, 'month')

        income = (
            qs.filter(transaction_type=Transaction.TYPE_INCOME)
            .extra(select={'period': f"DATE_TRUNC('{trunc}', date)"})
            .values('period').annotate(total=Sum('amount')).order_by('period')
        )
        expense = (
            qs.filter(transaction_type=Transaction.TYPE_EXPENSE)
            .extra(select={'period': f"DATE_TRUNC('{trunc}', date)"})
            .values('period').annotate(total=Sum('amount')).order_by('period')
        )
        # Merge into periods
        periods = {}
        for item in income:
            p = str(item['period'])
            periods.setdefault(p, {'period': p, 'income': Decimal('0'), 'expense': Decimal('0')})
            periods[p]['income'] = item['total']
        for item in expense:
            p = str(item['period'])
            periods.setdefault(p, {'period': p, 'income': Decimal('0'), 'expense': Decimal('0')})
            periods[p]['expense'] = item['total']
        for p in periods.values():
            p['net'] = p['income'] - p['expense']
        return Response(sorted(periods.values(), key=lambda x: x['period']))


class UpcomingRecurringView(APIView):
    """GET /api/transactions/upcoming/?days=30"""

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        future = today + __import__('datetime').timedelta(days=days)
        txs = Transaction.objects.filter(
            user=request.user,
            is_recurring=True,
            next_occurrence__lte=future,
            next_occurrence__gte=today,
        ).order_by('next_occurrence')
        return Response(TransactionSerializer(txs, many=True, context={'request': request}).data)
