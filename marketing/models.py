from django.db import models


class HeroSlide(models.Model):
    """Picha ya hiari kwa slide yenye maandishi yaliyowekwa kwenye landing page."""
    POSITIONS = (
        (1, '1 - Matokeo & Taaluma'),
        (2, '2 - Mawasiliano ya Wazazi'),
        (3, '3 - Nidhamu na Usalama'),
        (4, '4 - Ada na Malipo'),
        (5, '5 - Kwa Walimu'),
        (6, '6 - Duka la Shule'),
        (7, '7 - Ripoti Kamili kwa Mzazi'),
    )

    position = models.PositiveSmallIntegerField(choices=POSITIONS, unique=True)
    image = models.ImageField(upload_to='marketing/hero_slides/', blank=True)

    class Meta:
        ordering = ('position',)
        verbose_name = 'Hero slide'
        verbose_name_plural = 'Hero slides'

    def __str__(self):
        return self.get_position_display()


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
