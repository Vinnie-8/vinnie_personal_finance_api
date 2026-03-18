from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.utils.dateparse import parse_date
from django.utils import timezone
from decimal import Decimal
import datetime

from apps.transactions.models import Transaction
from apps.accounts.models import Account, NetWorthSnapshot


class IncomeVsExpenseView(APIView):
    """GET /api/reports/income-expense/?months=6"""

    def get(self, request):
        months = int(request.query_params.get('months', 6))
        today = timezone.now().date()
        results = []
        for i in range(months - 1, -1, -1):
            # Go back i months from current month
            first_of_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1) if i > 0 else today.replace(day=1)
            # Simplified: use first day of month offset
            month = (today.month - i - 1) % 12 + 1
            year = today.year - ((today.month - i - 1) // 12)
            start = datetime.date(year, month, 1)
            # Last day of month
            if month == 12:
                end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lte=end)
            income = qs.filter(transaction_type=Transaction.TYPE_INCOME).aggregate(s=Sum('amount'))['s'] or Decimal('0')
            expense = qs.filter(transaction_type=Transaction.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s'] or Decimal('0')
            results.append({
                'month': start.strftime('%Y-%m'),
                'income': income,
                'expense': expense,
                'net': income - expense,
            })
        return Response(results)


class SpendingBreakdownView(APIView):
    """GET /api/reports/spending/?start=&end="""

    def get(self, request):
        qs = Transaction.objects.filter(user=request.user, transaction_type=Transaction.TYPE_EXPENSE)
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(date__gte=parse_date(start))
        if end:
            qs = qs.filter(date__lte=parse_date(end))

        total = qs.aggregate(s=Sum('amount'))['s'] or Decimal('0')
        breakdown = (
            qs.values('category__id', 'category__name', 'category__color', 'category__icon')
            .annotate(amount=Sum('amount'), count=Count('id'))
            .order_by('-amount')
        )
        return Response({
            'total': total,
            'categories': [
                {
                    'category_id': str(r['category__id']) if r['category__id'] else None,
                    'name': r['category__name'] or 'Uncategorised',
                    'color': r['category__color'] or '#6c757d',
                    'icon': r['category__icon'] or 'tag',
                    'amount': r['amount'],
                    'count': r['count'],
                    'percentage': round(float(r['amount'] / total * 100), 2) if total else 0,
                }
                for r in breakdown
            ]
        })


class CashFlowView(APIView):
    """GET /api/reports/cash-flow/?start=&end="""

    def get(self, request):
        today = timezone.now().date()
        start = parse_date(request.query_params.get('start', str(today.replace(day=1))))
        end = parse_date(request.query_params.get('end', str(today)))
        qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lte=end)

        income_by_day = {
            r['date']: r['total']
            for r in qs.filter(transaction_type=Transaction.TYPE_INCOME)
            .values('date').annotate(total=Sum('amount'))
        }
        expense_by_day = {
            r['date']: r['total']
            for r in qs.filter(transaction_type=Transaction.TYPE_EXPENSE)
            .values('date').annotate(total=Sum('amount'))
        }
        current = start
        results = []
        while current <= end:
            income = income_by_day.get(current, Decimal('0'))
            expense = expense_by_day.get(current, Decimal('0'))
            results.append({
                'date': str(current),
                'income': income,
                'expense': expense,
                'net': income - expense,
            })
            current += datetime.timedelta(days=1)
        return Response(results)


class NetWorthHistoryView(APIView):
    """GET /api/reports/net-worth/?months=12"""

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        today = timezone.now().date()
        since = today - datetime.timedelta(days=months * 30)
        snapshots = NetWorthSnapshot.objects.filter(
            user=request.user,
            snapshot_date__gte=since,
        ).order_by('snapshot_date')
        return Response([
            {
                'date': str(s.snapshot_date),
                'net_worth': s.net_worth,
                'total_assets': s.total_assets,
                'total_liabilities': s.total_liabilities,
            }
            for s in snapshots
        ])


class TopMerchantsView(APIView):
    """GET /api/reports/top-merchants/?limit=10&start=&end="""

    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        qs = Transaction.objects.filter(user=request.user, transaction_type=Transaction.TYPE_EXPENSE)
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        if start:
            qs = qs.filter(date__gte=parse_date(start))
        if end:
            qs = qs.filter(date__lte=parse_date(end))
        merchants = (
            qs.values('description')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:limit]
        )
        return Response(list(merchants))


class SavingsRateView(APIView):
    """GET /api/reports/savings-rate/?start=&end="""

    def get(self, request):
        today = timezone.now().date()
        start = parse_date(request.query_params.get('start', str(today.replace(day=1))))
        end = parse_date(request.query_params.get('end', str(today)))
        qs = Transaction.objects.filter(user=request.user, date__gte=start, date__lte=end)

        income = qs.filter(transaction_type=Transaction.TYPE_INCOME).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        expense = qs.filter(transaction_type=Transaction.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        savings = income - expense
        rate = float(savings / income * 100) if income else 0
        return Response({
            'start': str(start),
            'end': str(end),
            'income': income,
            'expense': expense,
            'savings': savings,
            'savings_rate_percentage': round(rate, 2),
        })


class BudgetVsActualView(APIView):
    """GET /api/reports/budget-actual/"""

    def get(self, request):
        from apps.budgets.models import Budget
        from apps.budgets.serializers import BudgetSerializer
        budgets = Budget.objects.filter(user=request.user, is_active=True).select_related('category')
        results = []
        for b in budgets:
            spent = b.get_spent()
            results.append({
                'budget_id': str(b.id),
                'name': b.name,
                'category': b.category.name if b.category else 'Overall',
                'budgeted': b.amount,
                'actual': spent,
                'variance': b.amount - spent,
                'percentage': round(float(spent / b.amount * 100), 2) if b.amount else 0,
            })
        return Response(results)


class ExportCSVView(APIView):
    """POST /api/reports/export/csv/ — queue CSV export"""

    def post(self, request):
        from .tasks import export_csv_task
        task = export_csv_task.delay(str(request.user.id), request.data)
        return Response({
            'task_id': task.id,
            'status': 'queued',
            'message': 'CSV export queued. Poll /api/reports/export/{task_id}/ for status.',
        })


class ExportPDFView(APIView):
    """POST /api/reports/export/pdf/ — queue PDF report"""

    def post(self, request):
        from .tasks import export_pdf_task
        task = export_pdf_task.delay(str(request.user.id), request.data)
        return Response({
            'task_id': task.id,
            'status': 'queued',
            'message': 'PDF export queued. Poll /api/reports/export/{task_id}/ for status.',
        })


class ExportStatusView(APIView):
    """GET /api/reports/export/<task_id>/"""

    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        response = {'task_id': task_id, 'status': result.status}
        if result.ready():
            response['result'] = result.get()
        return Response(response)
