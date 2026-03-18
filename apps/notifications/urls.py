from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('read-all/', views.MarkAllReadView.as_view(), name='mark_all_read'),
    path('unread-count/', views.UnreadCountView.as_view(), name='unread_count'),
    path('preferences/', views.NotificationPreferenceView.as_view(), name='notification_prefs'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<uuid:pk>/read/', views.MarkReadView.as_view(), name='mark_read'),
]
