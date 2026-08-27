from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('dashboard/', views.store_dashboard_view, name='store_dashboard'),
    path('requirements/add/', views.add_requirement_view, name='add_requirement'),
    path('contributions/record/', views.record_contribution_view, name='record_contribution'),
    path('stock/adjust/', views.stock_adjustment_view, name='stock_adjustment'),
]
