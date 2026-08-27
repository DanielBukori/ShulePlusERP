from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list_view, name='notifications_list'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('<int:notification_id>/go/', views.mark_read_and_go_view, name='mark_read_and_go'),
]
