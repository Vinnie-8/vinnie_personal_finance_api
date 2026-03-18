from django.contrib import admin
from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'category_type', 'parent', 'is_system']
    list_filter = ['category_type', 'is_system']
    search_fields = ['name', 'user__email']
    readonly_fields = ['id', 'created_at']
