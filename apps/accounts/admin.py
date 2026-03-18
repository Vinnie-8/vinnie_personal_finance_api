from django.contrib import admin
from .models import Account, NetWorthSnapshot


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'account_type', 'balance', 'currency', 'is_active']
    list_filter = ['account_type', 'currency', 'is_active']
    search_fields = ['name', 'user__email', 'institution_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(NetWorthSnapshot)
class NetWorthSnapshotAdmin(admin.ModelAdmin):
    list_display = ['user', 'snapshot_date', 'net_worth', 'total_assets', 'total_liabilities']
    list_filter = ['snapshot_date']
