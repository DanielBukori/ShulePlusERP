"""
DISCIPLINE MODELS - inaenda kwenye 'discipline/models.py'
Inatumia School.discipline_starting_score na School.discipline_alert_score
(ongeza hizo kwenye shule_core/models.py -> School, kama ilivyoelekezwa).
"""
from django.db import models
from shule_core.models import School, Student, CustomUser
from shule_core.upload_paths import discipline_upload_path


class OffenseType(models.Model):
    """
    Orodha ya makosa yanayowezekana na alama zinazopunguzwa kwa kila moja.
    Mfano: 'Kuchelewa' -2, 'Kutoroka Shule' -15, 'Ugomvi' -10.
    Kila shule ina orodha yake (inaweza kutofautiana shule hadi shule).
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='offense_types', db_index=True)
    name = models.CharField(max_length=100)
    points_deducted = models.PositiveIntegerField(help_text='Alama zitakazopunguzwa (namba chanya)')
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('school', 'name')
        ordering = ['-points_deducted']

    def __str__(self):
        return f"{self.name} (-{self.points_deducted})"


class DisciplineIncident(models.Model):
    """
    Kosa moja alilofanya mwanafunzi. Alama zake zinapunguzwa moja kwa moja
    kwenye 'current score' ya mwanafunzi kwa mwaka husika wa masomo.
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='discipline_incidents', db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='discipline_incidents', db_index=True)
    offense_type = models.ForeignKey(OffenseType, on_delete=models.PROTECT, related_name='incidents')
    academic_year = models.IntegerField(default=2026, db_index=True)
    date_occurred = models.DateField()
    notes = models.TextField(blank=True, null=True)
    evidence_file = models.FileField(upload_to=discipline_upload_path, blank=True, null=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_occurred']
        indexes = [models.Index(fields=['school', 'student', 'academic_year'])]

    def __str__(self):
        return f"{self.student} - {self.offense_type.name} ({self.date_occurred})"


class DisciplineAlert(models.Model):
    """
    Inaundwa MARA MOJA TU kwa kila (student, academic_year) pale alama za
    mwanafunzi zinapopita chini ya School.discipline_alert_score.
    Discipline Officer/Headmaster wanaweza ku-'resolve' baada ya kuchukua
    hatua (mfano bodi imekaa, mzazi ameitwa).
    """
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='discipline_alerts', db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='discipline_alerts', db_index=True)
    academic_year = models.IntegerField(default=2026, db_index=True)
    score_at_alert = models.IntegerField()
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('student', 'academic_year')

    def __str__(self):
        status = 'Imeshughulikiwa' if self.is_resolved else 'Bado Wazi'
        return f"Alert: {self.student} - {self.score_at_alert} pts ({status})"


def get_student_discipline_score(student, academic_year):
    """
    Helper: alama za sasa za mwanafunzi kwa mwaka husika.
    score = starting_score - jumla ya points_deducted za makosa yote ya mwaka huo.
    """
    starting = student.school.discipline_starting_score
    total_deducted = DisciplineIncident.objects.filter(
        student=student, academic_year=academic_year
    ).aggregate(total=models.Sum('offense_type__points_deducted'))['total'] or 0
    return starting - total_deducted
