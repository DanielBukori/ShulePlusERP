"""
Weka faili hii: notifications/context_processors.py

Kisha ongeza kwenye settings.py -> TEMPLATES -> OPTIONS -> context_processors:
    'notifications.context_processors.notifications_context',

Hii inaingiza unread_notifications_count na recent_notifications kwenye
templates ZOTE kiotomatiki - hutahitaji kuziongeza kwenye kila view.
"""
from .models import Notification


def notifications_context(request):
    if not request.user.is_authenticated:
        return {}
    qs = Notification.objects.filter(user=request.user)
    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': qs[:8],
    }
