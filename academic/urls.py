from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # Dashboard kuu ya Academic Master
    path('dashboard/', views.academic_dashboard_view, name='academic_dashboard'),
    path('setup/', views.school_setup_view, name='school_setup'),

    # Matokeo ya darasa moja (broadsheet: subjects, total, average, division, position)
    path('results/class/<int:class_id>/', views.academic_class_results_view, name='class_results'),
    path('results/class/<int:class_id>/download/pdf/', views.download_broadsheet_pdf, name='download_broadsheet_pdf'),
    path('results/class/<int:class_id>/download/excel/', views.download_broadsheet_excel, name='download_broadsheet_excel'),

    # Uchambuzi wa somo kivyake (subject-wise analysis)
    path('analysis/subject/', views.academic_subject_analysis_view, name='subject_analysis'),

    # Takwimu za Jumla - pie + bar chart (grade distribution kwa somo)
    path('analysis/statistics/', views.academic_statistics_view, name='statistics'),

    # Ripoti ya Alama Zinazokosekana - kufuatilia walimu wamalize kujaza
    path('analysis/missing-marks/', views.missing_marks_report_view, name='missing_marks_report'),

    # Ripoti ya F za Kiotomatiki (baada ya Publish) - kufuatilia waliokosa mtihani
    path('analysis/auto-absent/', views.auto_absent_report_view, name='auto_absent_report'),

    # Kuchapisha matokeo kwa wazazi/wanafunzi
    path('publish/', views.academic_publish_results_view, name='publish_results'),

    # Usajili wa mwanafunzi (+ akaunti za mzazi na mwanafunzi)
    path('students/register/', views.register_student_view, name='register_student'),
    path('search/', views.global_search_view, name='global_search'),
    # ILIKUWA 'students/register/' (sawa na register_student!) - Django
    # ilikuwa ikitumia daima pattern ya KWANZA iliyofanana (register_student_view),
    # kwa hiyo bulk import haikuwahi kufikiwa. Sasa ina njia yake mwenyewe.
    path('students/bulk-register/', views.bulk_register_students_view, name='bulk_register_students'),
    path('students/import-template/', views.download_import_template_view, name='download_import_template'),
    path('students/promote/', views.promote_students_view, name='promote_students'),
]
