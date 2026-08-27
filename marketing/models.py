from django.db import models


class DemoRequest(models.Model):
    """Ombi la shule linalotaka demo/kununua ShulePlusERP."""
    school_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    student_count = models.CharField(max_length=50, blank=True, null=True, help_text='Mfano: 300-800')
    message = models.TextField(blank=True, null=True)
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.school_name} - {self.contact_name}"
