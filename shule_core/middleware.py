"""
TenantMiddleware - toleo lililorekebishwa.

Weka kwenye settings.py:
    BASE_DOMAIN = 'shulepluserp.co.tz'   # badilisha na domain yako halisi

MANTIKI:
    - host == BASE_DOMAIN (apex) au 'www.'+BASE_DOMAIN -> request.school=None
      (marketing landing page inaonekana - HAKUNA subdomain)
    - host == '<subdomain>.'+BASE_DOMAIN -> request.school = shule husika
    - host == '<subdomain>.localhost' (LOCAL DEV) -> vivyo hivyo
    - subdomain isiyopatikana -> ukurasa mzuri wa 'school_not_found', siyo Http404 mbaya
"""
from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from .models import School


class TenantMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.school = None

        if request.path.startswith('/admin/'):
            return None

        host = request.get_host().split(':')[0]  # ondoa port (mfano :8000)
        base_domain = getattr(settings, 'BASE_DOMAIN', 'shulepluserp.co.tz')

        subdomain = None

        # 1. LOCAL DEV: mfano sehisco.localhost (browsers za kisasa zina-resolve
        #    *.localhost kwenda 127.0.0.1 kiotomatiki, hauhitaji /etc/hosts)
        if host.endswith('.localhost'):
            subdomain = host[: -len('.localhost')]

        # 2. PRODUCTION: mfano sehisco.shulepluserp.co.tz
        elif host.endswith('.' + base_domain):
            subdomain = host[: -len('.' + base_domain)]

        # 3. host == base_domain wenyewe (apex) au 'www.'+base_domain au
        #    'localhost' tupu -> subdomain inabaki None kabisa (SIYO error)

        if not subdomain or subdomain == 'www':
            return None  # marketing/apex page - request.school inabaki None

        try:
            request.school = School.objects.get(subdomain=subdomain, is_approved=True)
        except School.DoesNotExist:
            return render(request, 'branding/school_not_found.html', status=404)

        user = getattr(request, 'user', None)
        if (
            user
            and user.is_authenticated
            and user.school_id
            and user.school_id != request.school.pk
        ):
            return HttpResponseForbidden("Akaunti hii si ya shule hii.")

        return None
