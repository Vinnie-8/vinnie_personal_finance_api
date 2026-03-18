from django.urls import path
from . import views

urlpatterns = [
    path('', views.TransactionListCreateView.as_view(), name='transaction_list'),
    path('bulk/', views.BulkImportView.as_view(), name='bulk_import'),
    path('by-category/', views.CategoryBreakdownView.as_view(), name='by_category'),
    path('by-period/', views.PeriodBreakdownView.as_view(), name='by_period'),
    path('upcoming/', views.UpcomingRecurringView.as_view(), name='upcoming_recurring'),
    path('<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
]
