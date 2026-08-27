from django.db import models
from django.conf import settings
from shule_core.models import School, SchoolClass, Student


class Attendance(models.Model):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    EXCUSED = "EXCUSED"

    STATUS_CHOICES = [
        (PRESENT, "Yupo"),
        (ABSENT, "Hayupo"),
        (LATE, "Amechelewa"),
        (EXCUSED, "Ruhusa"),
    ]

    school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="attendance_records"
    )
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name="attendance_records"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="attendance_records"
    )
    date = models.DateField()
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PRESENT
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date", "student__first_name"]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"
