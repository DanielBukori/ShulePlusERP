"""
ROOT urls.py - weka faili hii kwenye 'jina_la_project_yako/urls.py'
(ile folder yenye settings.py, siyo app yoyote).

MUUNDO WA PREFIX (hakuna mgongano - kila app ina nafasi yake):
    ''                -> marketing (landing page ya kampuni - LAZIMA iwe ya mwisho kwenye orodha)
    'register-school/' -> shule_core (usajili wa shule mpya)
    'accounts/'        -> accounts (login, logout, role-redirect)
    'academic/'        -> academic (matokeo, broadsheet, publish)
    'staff/'           -> staff (usajili wa walimu)
    'teacher/'         -> teacher_portal (marks, stats, home package)
    'store/'           -> store (michango + stock)
    'discipline/'      -> discipline (makosa + alerts)
    'accountant/'      -> accountant (ada + madeni + malipo)
    'family/'          -> family_portal (Parent + Student dashboard)
    'audit/'           -> audit (audit log)
    'site/'            -> branding (tovuti ya umma ya kila shule - LOCAL DEV fallback tu;
                           production itakuwa root '' kwenye subdomain, siyo apex domain)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('shule_core.urls')),
    path('accounts/', include('accounts.urls')),
    path('academic/', include('academic.urls')),
    path('staff/', include('staff.urls')),
    path('teacher/', include('teacher_portal.urls')),
    path('store/', include('store.urls')),
    path('discipline/', include('discipline.urls')),
    path('accountant/', include('accountant.urls')),
    path('family/', include('family_portal.urls')),
    path('audit/', include('audit.urls')),
    path('site/', include('branding.urls')),
    path('notifications/', include('notifications.urls')),   
    path('attendance/', include('attendance.urls')),
    # MARKETING LAZIMA IWE YA MWISHO - ina path('') ambayo inaweza
    # "kumeza" njia nyingine ikiwa imewekwa juu.
    path('', include('marketing.urls')),
]

# Picha/faili za MEDIA zionekane wakati wa maendeleo (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

