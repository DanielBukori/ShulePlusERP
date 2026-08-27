from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views as views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.TenantLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='accounts:login'), name='logout'),
    path('redirect/', views.post_login_redirect_view, name='post_login_redirect'),
    path('force-password-change/', views.force_password_change_view, name='force_password_change'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('otp-verify/', views.otp_verify_view, name='otp_verify'),
    path('otp-resend/', views.otp_resend_view, name='otp_resend'),
]
