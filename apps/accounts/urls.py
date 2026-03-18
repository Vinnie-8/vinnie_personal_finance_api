from django.urls import path
from . import views

urlpatterns = [
    path('', views.AccountListCreateView.as_view(), name='account_list'),
    path('net-worth/', views.NetWorthView.as_view(), name='net_worth'),
    path('transfer/', views.TransferView.as_view(), name='transfer'),
    path('<uuid:pk>/', views.AccountDetailView.as_view(), name='account_detail'),
    path('<uuid:pk>/balance/', views.AccountBalanceView.as_view(), name='account_balance'),
]
