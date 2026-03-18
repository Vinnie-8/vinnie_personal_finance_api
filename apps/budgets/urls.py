from django.urls import path
from . import views

urlpatterns = [
    path('', views.BudgetListCreateView.as_view(), name='budget_list'),
    path('overview/', views.BudgetOverviewView.as_view(), name='budget_overview'),
    path('alerts/', views.BudgetAlertsView.as_view(), name='budget_alerts'),
    path('<uuid:pk>/', views.BudgetDetailView.as_view(), name='budget_detail'),
    path('<uuid:pk>/progress/', views.BudgetProgressView.as_view(), name='budget_progress'),
]
