"""
Weka faili hii: notifications/utils.py

MATUMIZI (badala ya kuita send_sms_to_user peke yake popote kwenye
discipline/store/accountant/academic):

    from notifications.utils import notify
    notify(user, school, "Ujumbe wako...", link="/family/parent/dashboard/")

Hii inaunda Notification (bell) NA kujaribu SMS kwa pamoja - mtu ataona
ujumbe humo humo mfumoni HATA kama hajaweka BEEM_API_KEY bado.
"""
from .models import Notification
from shule_core.sms_service import send_sms_to_user


def notify(user, school, message, link=''):
    if not user:
        return
    try:
        Notification.objects.create(school=school, user=user, message=message, link=link)
    except Exception as e:
        print(f"[NOTIFICATION ERROR] {e}")

    send_sms_to_user(school, user, message)
