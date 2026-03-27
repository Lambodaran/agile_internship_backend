from django.urls import path
from .views import RegisterView, LoginView,LogoutView
from .views import (
    RequestPasswordResetView,
    VerifyResetCodeView,
    ResetPasswordView,
)
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    path('request-password-reset/', RequestPasswordResetView.as_view(), name='request-password-reset'),
    path('verify-reset-code/', VerifyResetCodeView.as_view(), name='verify-reset-code'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
