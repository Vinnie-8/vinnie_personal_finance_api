from django.urls import path
from . import views

urlpatterns = [
    path('', views.CategoryListCreateView.as_view(), name='category_list'),
    path('seed/', views.SeedCategoriesView.as_view(), name='category_seed'),
    path('<uuid:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('<uuid:pk>/stats/', views.CategoryStatsView.as_view(), name='category_stats'),
]
