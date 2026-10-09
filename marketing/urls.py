from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('', views.landing_page_view, name='landing_page'),
    path('hero/<int:slide_id>/image/', views.hero_image_view, name='hero_image'),
    path('terms/', views.terms_of_service_view, name='terms_of_service'),
    path('privacy/', views.privacy_policy_view, name='privacy_policy'),
]
