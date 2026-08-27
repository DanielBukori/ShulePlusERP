from django.db import models
from shule_core.models import School, CustomUser


class Notification(models.Model):
    """Taarifa ya in-app (bell icon) - inatumika pamoja na SMS, siyo badala yake."""
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True, null=True, help_text='URL ya kwenda akibofya')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read'])]

    def __str__(self):
        return f"{self.user} - {self.message[:40]}"
