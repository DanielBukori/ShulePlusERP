from django.urls import path
from . import views

app_name = 'teacher_portal'

urlpatterns = [
    path('dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('marks/enter/', views.enter_marks_view, name='enter_marks'),
    path('marks/stats/', views.subject_stats_view, name='subject_stats'),
    path('home-package/upload/', views.upload_home_package_view, name='upload_home_package'),
    path('home-package/<int:package_id>/download/', views.download_home_package_view, name='download_home_package'),
]
