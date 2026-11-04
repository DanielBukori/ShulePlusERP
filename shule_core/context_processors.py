from django.conf import settings


def platform(request):
    """
    Domain, email na shule ya sasa kwa templates zote.
    View inayopitisha 'school' yake mwenyewe inashinda hii (mfano ukurasa
    wa umma wa shule nyingine kwa njia ya /site/s/<subdomain>/), kwa hiyo
    preview hazivurugiki.
    """
    return {
        'platform_domain': settings.BASE_DOMAIN,
        'platform_email': settings.SUPPORT_EMAIL,
        'school': getattr(request, 'school', None),
    }
