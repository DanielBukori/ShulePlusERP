from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('dashboard/', views.store_dashboard_view, name='store_dashboard'),
    path('report/full/', views.full_report_view, name='full_report'),
    path('requirements/add/', views.add_requirement_view, name='add_requirement'),
    path('requirements/<int:requirement_id>/publish/', views.publish_requirement_view, name='publish_requirement'),
    path('contributions/record/', views.record_contribution_view, name='record_contribution'),
    path('contributions/record-bulk/', views.record_contribution_spreadsheet_view, name='record_contribution_spreadsheet'),
    path('stock/adjust/', views.stock_adjustment_view, name='stock_adjustment'),
]
