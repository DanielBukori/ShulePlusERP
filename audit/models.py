from django.db import models
from shule_core.models import School, CustomUser


class AuditLog(models.Model):
    """
    Kumbukumbu ya kudumu ya vitendo muhimu vya mfumo - nani (actor),
    alifanya nini (action + description), lini (created_at), shule gani.

    Hii SIYO inayotokana na signals za Django kwa sababu signals hazina
    ufahamu wa 'nani ameingia' (request.user) kwa uhakika - badala yake,
    log_action() inaitwa moja kwa moja ndani ya views baada ya kitendo
    kufanikiwa, hivyo actor ni sahihi kila wakati.
    """
    ACTION_CHOICES = [
        ('MARKS_ENTERED', 'Alama Zimejazwa/Kubadilishwa'),
        ('RESULTS_PUBLISHED', 'Matokeo Yamechapishwa'),
        ('PAYMENT_RECORDED', 'Malipo Yamerekodiwa'),
        ('FEE_STRUCTURE_SET', 'Ada Imewekwa'),
        ('ASSESSMENTS_GENERATED', 'Tathmini za Ada Zimetengenezwa'),
        ('OTHER_CHARGE_ADDED', 'Mchango Umeongezwa'),
        ('DISCIPLINE_RECORDED', 'Kosa la Nidhamu Limerekodiwa'),
        ('STUDENT_REGISTERED', 'Mwanafunzi Amesajiliwa'),
        ('TEACHER_REGISTERED', 'Mwalimu Amesajiliwa'),
        ('STOCK_ADJUSTED', 'Stock Imerekebishwa'),
        ('CONTRIBUTION_RECORDED', 'Mchango wa Mwanafunzi Umerekodiwa'),
        ('BRANDING_POST_CREATED', 'Chapisho la Tovuti Limeongezwa'),
        ('OTHER', 'Kingine'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='audit_logs', db_index=True)
    actor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='audit_actions')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_index=True)
    description = models.TextField(help_text='Maelezo ya kibinadamu ya kitendo kilichofanyika')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['school', 'created_at'])]

    def __str__(self):
        who = self.actor.get_full_name() if self.actor else 'Mfumo'
        return f"{who} - {self.get_action_display()} ({self.created_at:%d/%m/%Y %H:%M})"
