from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('me/', views.MeView.as_view(), name='me'),
    # Admin
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<uuid:pk>/', views.UserDetailAdminView.as_view(), name='user_detail'),
    path('users/<uuid:pk>/deactivate/', views.DeactivateUserView.as_view(), name='deactivate_user'),
]
