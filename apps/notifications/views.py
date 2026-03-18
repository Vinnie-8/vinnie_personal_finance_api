from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ — all notifications, unread first"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get('unread_only')
        if unread_only == 'true':
            qs = qs.filter(is_read=False)
        return qs.order_by('is_read', '-created_at')


class NotificationDetailView(generics.RetrieveDestroyAPIView):
    """GET/DELETE /api/notifications/<id>/"""
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkReadView(APIView):
    """PATCH /api/notifications/<id>/read/"""

    def patch(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.mark_read()
        return Response(NotificationSerializer(notif).data)


class MarkAllReadView(APIView):
    """PATCH /api/notifications/read-all/"""

    def patch(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )
        return Response({'message': f'{count} notifications marked as read.'})


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""

    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/notifications/preferences/"""
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        prefs, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return prefs
