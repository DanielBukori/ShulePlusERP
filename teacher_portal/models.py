from django.db import models
from shule_core.models import School, Subject, SchoolClass, CustomUser
from shule_core.upload_paths import home_package_upload_path


class HomePackage(models.Model):
    """
    Kazi/mazoezi anayopakia mwalimu kwa ajili ya wanafunzi likizo,
    kwa somo na darasa lake mwenyewe.
    """
    TERM_CHOICES = [('TERM_1', 'Muhula wa Kwanza'), ('TERM_2', 'Muhula wa Pili')]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='home_packages', db_index=True)
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='home_packages')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='home_packages')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='home_packages')
    term = models.CharField(max_length=20, choices=TERM_CHOICES)
    academic_year = models.IntegerField(default=2026)
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to=home_package_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [models.Index(fields=['school', 'subject', 'school_class', 'term', 'academic_year'])]

    def __str__(self):
        return f"{self.title} - {self.subject.name} {self.school_class}"
