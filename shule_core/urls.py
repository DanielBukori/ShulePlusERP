from django.urls import path
from . import views

app_name = 'shule_core'

urlpatterns = [
    path('register-school/', views.register_school, name='register_school'),
    path('register-school/received/', views.school_registration_received, name='registration_received'),
    path('health/', views.health_check_view, name='health_check'),
]
