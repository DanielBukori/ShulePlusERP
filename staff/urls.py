from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('teachers/', views.teacher_list_view, name='teacher_list'),
    path('teachers/register/', views.register_teacher_view, name='register_teacher'),
    path('teachers/<int:staff_id>/assignments/', views.manage_assignments_view, name='manage_assignments'),
    path('assign-class-teacher/', views.assign_class_teacher_view, name='assign_class_teacher'),
]
