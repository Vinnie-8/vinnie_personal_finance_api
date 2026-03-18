from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from decimal import Decimal
import datetime

from .models import Budget
from .serializers import BudgetSerializer, BudgetProgressSerializer


class BudgetListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/budgets/ — all budgets with live spent/remaining
    POST /api/budgets/ — create budget rule
    """
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user, is_active=True).select_related('category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/budgets/<id>/"""
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        budget = self.get_object()
        budget.is_active = False
        budget.save(update_fields=['is_active'])
        return Response({'message': 'Budget removed.'}, status=status.HTTP_200_OK)


class BudgetProgressView(APIView):
    """GET /api/budgets/<id>/progress/ — % spent, burn rate, projection"""

    def get(self, request, pk):
        budget = get_object_or_404(Budget, pk=pk, user=request.user)
        today = timezone.now().date()
        start, end = budget.get_period_dates()
        total_days = (end - start).days + 1
        days_elapsed = max((today - start).days + 1, 1)
        days_remaining = max((end - today).days, 0)

        spent = budget.get_spent()
        daily_burn = spent / days_elapsed
        projected = daily_burn * total_days
        overspend = projected - budget.amount if projected > budget.amount else None

        return Response({
            'budget': BudgetSerializer(budget).data,
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'total_days': total_days,
            'daily_burn_rate': round(daily_burn, 2),
            'projected_total': round(projected, 2),
            'projected_overspend': round(overspend, 2) if overspend else None,
        })


class BudgetOverviewView(APIView):
    """GET /api/budgets/overview/ — aggregated all budgets"""

    def get(self, request):
        budgets = Budget.objects.filter(user=request.user, is_active=True)
        data = BudgetSerializer(budgets, many=True).data
        total_budgeted = sum(Decimal(str(b['amount'])) for b in data)
        total_spent = sum(Decimal(str(b['spent'])) for b in data)
        return Response({
            'total_budgeted': total_budgeted,
            'total_spent': total_spent,
            'total_remaining': total_budgeted - total_spent,
            'budgets': data,
        })


class BudgetAlertsView(APIView):
    """GET /api/budgets/alerts/ — budgets exceeding threshold"""

    def get(self, request):
        budgets = Budget.objects.filter(user=request.user, is_active=True)
        alerts = []
        for budget in budgets:
            spent = budget.get_spent()
            if spent >= budget.amount * budget.alert_threshold:
                pct = float(spent / budget.amount * 100) if budget.amount else 0
                alerts.append({
                    **BudgetSerializer(budget).data,
                    'alert_level': 'exceeded' if spent >= budget.amount else 'warning',
                })
        return Response({'count': len(alerts), 'alerts': alerts})
