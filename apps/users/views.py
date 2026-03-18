from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import User, PasswordResetToken, EmailVerificationToken
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserUpdateSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer,
)
from apps.categories.services import seed_default_categories


class RegisterView(APIView):
    """POST /api/auth/register/ — create account + send verification email"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Seed default categories for new user
        seed_default_categories(user)

        # Create and send email verification token
        token_obj = EmailVerificationToken.objects.create(user=user)
        _send_verification_email(user, token_obj.token)

        # Return JWT tokens immediately so they can start using the app
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Account created. Please verify your email.',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ — returns JWT access + refresh tokens"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class LogoutView(APIView):
    """POST /api/auth/logout/ — blacklist the refresh token"""

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'})
        except TokenError:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    """POST /api/auth/refresh/ — handled by SimpleJWT; this is a wrapper doc view"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # SimpleJWT handles this via TokenRefreshView; kept here for URL consistency
        from rest_framework_simplejwt.views import TokenRefreshView
        return TokenRefreshView.as_view()(request._request)


class VerifyEmailView(APIView):
    """GET /api/auth/verify/<token>/ — confirm email address"""
    permission_classes = [permissions.AllowAny]

    def get(self, request, token):
        token_obj = get_object_or_404(EmailVerificationToken, token=token, is_used=False)
        user = token_obj.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        return Response({'message': 'Email verified successfully.'})


class ForgotPasswordView(APIView):
    """POST /api/auth/forgot-password/ — send reset email"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
            token_obj = PasswordResetToken.objects.create(user=user)
            _send_reset_email(user, token_obj.token)
        except User.DoesNotExist:
            pass  # Don't reveal whether email exists
        return Response({'message': 'If that email is registered, a reset link has been sent.'})


class ResetPasswordView(APIView):
    """POST /api/auth/reset-password/ — set new password with token"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_obj = get_object_or_404(PasswordResetToken, token=serializer.validated_data['token'])
        if not token_obj.is_valid():
            return Response({'detail': 'Token is expired or already used.'}, status=status.HTTP_400_BAD_REQUEST)
        user = token_obj.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])
        return Response({'message': 'Password reset successfully.'})


class ChangePasswordView(APIView):
    """PUT /api/auth/change-password/ — change password while authenticated"""

    def put(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'message': 'Password changed successfully.'})


class MeView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/DELETE /api/auth/me/ — current user profile"""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'message': 'Account deactivated.'}, status=status.HTTP_200_OK)


# ── Admin Views ─────────────────────────────────────────────────────────────

class UserListView(generics.ListAPIView):
    """GET /api/auth/users/ — admin: list all users"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    search_fields = ['email', 'full_name']
    ordering_fields = ['created_at', 'email']


class UserDetailAdminView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/auth/users/<id>/ — admin: get or update user"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()


class DeactivateUserView(APIView):
    """POST /api/auth/users/<id>/deactivate/ — admin: deactivate account"""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response({'message': f'User {user.email} deactivated.'})


# ── Helpers ──────────────────────────────────────────────────────────────────

def _send_verification_email(user, token):
    link = f"http://localhost:8000/api/auth/verify/{token}/"
    send_mail(
        subject='Verify your email — Personal Finance',
        message=f'Hi {user.first_name},\n\nVerify your email: {link}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _send_reset_email(user, token):
    link = f"http://localhost:3000/reset-password?token={token}"
    send_mail(
        subject='Reset your password — Personal Finance',
        message=f'Hi {user.first_name},\n\nReset your password: {link}\n\nThis link expires in 24 hours.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
