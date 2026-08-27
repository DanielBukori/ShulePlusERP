from django.urls import path
from . import views

app_name = 'family_portal'

urlpatterns = [
    path('parent/dashboard/', views.parent_dashboard_view, name='parent_dashboard'),
    path('parent/child/<int:student_id>/', views.child_detail_view, name='child_detail'),
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('report/<int:student_id>/preview/', views.preview_consolidated_report_view, name='preview_consolidated_report'),
    path('report/<int:student_id>/download/', views.download_consolidated_report, name='download_consolidated_report'),
]
