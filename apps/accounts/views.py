from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from decimal import Decimal

from .models import Account, NetWorthSnapshot
from .serializers import (
    AccountSerializer, AccountCreateSerializer,
    TransferSerializer, NetWorthSerializer,
)


class AccountListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/accounts/ — all accounts with balances
    POST /api/accounts/ — create new account
    """

    def get_serializer_class(self):
        return AccountCreateSerializer if self.request.method == 'POST' else AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AccountDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/accounts/<id>/ — account detail
    PUT    /api/accounts/<id>/ — update account
    DELETE /api/accounts/<id>/ — soft delete
    """
    serializer_class = AccountSerializer

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        account.is_active = False
        account.save(update_fields=['is_active'])
        return Response({'message': 'Account deactivated.'}, status=status.HTTP_200_OK)


class AccountBalanceView(APIView):
    """GET /api/accounts/<id>/balance/ — current balance with running total"""

    def get(self, request, pk):
        account = get_object_or_404(Account, pk=pk, user=request.user)
        # Recalculate from transactions
        from apps.transactions.models import Transaction
        income = Transaction.objects.filter(
            account=account,
            transaction_type=Transaction.TYPE_INCOME,
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        expense = Transaction.objects.filter(
            account=account,
            transaction_type=Transaction.TYPE_EXPENSE,
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        transfer_in = Transaction.objects.filter(
            destination_account=account,
            transaction_type=Transaction.TYPE_TRANSFER,
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        transfer_out = Transaction.objects.filter(
            account=account,
            transaction_type=Transaction.TYPE_TRANSFER,
        ).aggregate(s=Sum('amount'))['s'] or Decimal('0')
        calculated = income - expense + transfer_in - transfer_out
        return Response({
            'account_id': str(account.id),
            'name': account.name,
            'stored_balance': account.balance,
            'calculated_balance': calculated,
            'income_total': income,
            'expense_total': expense,
        })


class NetWorthView(APIView):
    """GET /api/accounts/net-worth/ — assets minus liabilities"""

    def get(self, request):
        accounts = Account.objects.filter(user=request.user, is_active=True, include_in_total=True)
        assets = accounts.filter(account_type__in=['checking', 'savings', 'cash', 'investment'])
        liabilities = accounts.filter(account_type__in=['credit_card', 'loan'])

        total_assets = assets.aggregate(s=Sum('balance'))['s'] or Decimal('0')
        total_liabilities = liabilities.aggregate(s=Sum('balance'))['s'] or Decimal('0')
        net_worth = total_assets - total_liabilities

        return Response({
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'net_worth': net_worth,
            'accounts': AccountSerializer(accounts, many=True).data,
        })


class TransferView(APIView):
    """POST /api/accounts/transfer/ — atomic transfer between accounts"""

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from_account = get_object_or_404(Account, pk=data['from_account'], user=request.user)
        to_account = get_object_or_404(Account, pk=data['to_account'], user=request.user)
        amount = data['amount']

        with db_transaction.atomic():
            from_account.balance -= amount
            to_account.balance += amount
            from_account.save(update_fields=['balance'])
            to_account.save(update_fields=['balance'])

            # Record as transfer transactions
            from apps.transactions.models import Transaction
            tx = Transaction.objects.create(
                user=request.user,
                account=from_account,
                destination_account=to_account,
                transaction_type=Transaction.TYPE_TRANSFER,
                amount=amount,
                description=data['description'],
                date=__import__('django.utils.timezone', fromlist=['now']).now().date(),
            )

        return Response({
            'message': 'Transfer successful.',
            'transaction_id': str(tx.id),
            'from_balance': from_account.balance,
            'to_balance': to_account.balance,
        }, status=status.HTTP_201_CREATED)
