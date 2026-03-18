from django.urls import path
from . import views

urlpatterns = [
    path('income-expense/', views.IncomeVsExpenseView.as_view(), name='income_expense'),
    path('spending/', views.SpendingBreakdownView.as_view(), name='spending_breakdown'),
    path('cash-flow/', views.CashFlowView.as_view(), name='cash_flow'),
    path('net-worth/', views.NetWorthHistoryView.as_view(), name='net_worth_history'),
    path('top-merchants/', views.TopMerchantsView.as_view(), name='top_merchants'),
    path('savings-rate/', views.SavingsRateView.as_view(), name='savings_rate'),
    path('budget-actual/', views.BudgetVsActualView.as_view(), name='budget_actual'),
    path('export/csv/', views.ExportCSVView.as_view(), name='export_csv'),
    path('export/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),
    path('export/<str:task_id>/', views.ExportStatusView.as_view(), name='export_status'),
]
