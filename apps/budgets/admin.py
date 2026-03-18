from django.contrib import admin
from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category', 'amount', 'period', 'is_active', 'rollover']
    list_filter = ['period', 'is_active', 'rollover']
    search_fields = ['name', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
