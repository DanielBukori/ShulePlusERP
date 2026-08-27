from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.my_classes_view, name="my_classes"),
    path("mark/<int:class_id>/", views.mark_attendance_view, name="mark_attendance"),
    path("conduct/<int:class_id>/", views.conduct_list_view, name="conduct_list"),
    path("conduct/student/<int:student_id>/", views.edit_conduct_view, name="edit_conduct"),
]
