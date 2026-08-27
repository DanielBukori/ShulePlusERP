from django.urls import path
from . import views

app_name = 'discipline'

urlpatterns = [
    path('dashboard/', views.discipline_dashboard_view, name='discipline_dashboard'),
    path('offenses/add/', views.add_offense_type_view, name='add_offense_type'),
    path('incidents/record/', views.record_incident_view, name='record_incident'),
    path('incidents/<int:incident_id>/evidence/', views.view_evidence_view, name='view_evidence'),
]
