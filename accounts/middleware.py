"""
Weka faili hii: accounts/middleware.py

Kisha ongeza kwenye settings.py -> MIDDLEWARE, BAADA ya
AuthenticationMiddleware NA TenantMiddleware:

    MIDDLEWARE = [
        ...
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'shule_core.middleware.TenantMiddleware',
        'accounts.middleware.ForcePasswordChangeMiddleware',   # <-- HAPA
        ...
    ]

Hii inazuia mtumiaji mwenye must_change_password=True kufikia UKURASA
WOWOTE mwingine (hata kwa kuandika URL moja kwa moja) mpaka abadilishe
password yake kwanza.
"""
from django.shortcuts import redirect
from django.urls import reverse

# Njia zinazoruhusiwa hata kabla ya kubadilisha password
ALLOWED_PATHS_PREFIXES = ('/admin/', '/static/', '/media/')
ALLOWED_URL_NAMES = ('accounts:force_password_change', 'accounts:logout')


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)

        if user and user.is_authenticated and getattr(user, 'must_change_password', False):
            allowed_paths = [reverse(name) for name in ALLOWED_URL_NAMES]
            if request.path not in allowed_paths and not request.path.startswith(ALLOWED_PATHS_PREFIXES):
                return redirect('accounts:force_password_change')

        return self.get_response(request)
