"""
Weka faili hii: audit/utils.py

MATUMIZI (kwenye view yoyote, baada ya kitendo kufanikiwa):
    from audit.utils import log_action
    log_action(request.user, school, 'PAYMENT_RECORDED',
               f"Amerekodi malipo ya TZS {payment.amount} kwa {payment.student}")
"""
from .models import AuditLog


def log_action(actor, school, action, description):
    """
    actor: request.user (CustomUser) aliyefanya kitendo
    school: School husika
    action: mojawapo ya AuditLog.ACTION_CHOICES (mfano 'PAYMENT_RECORDED')
    description: maelezo mafupi ya kibinadamu ya kilichotokea
    """
    try:
        AuditLog.objects.create(school=school, actor=actor, action=action, description=description)
    except Exception as e:
        # Audit log isije ikavunja kitendo halisi (mfano kuhifadhi malipo)
        # hata kama log yenyewe imeshindwa kuandikwa.
        print(f"[AUDIT LOG ERROR] {e}")
