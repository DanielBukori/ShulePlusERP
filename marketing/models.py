from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from PIL import Image


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
    ALLOWED_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
    MAX_UPLOAD_MB = 8
    MIN_WIDTH = 1200

    position = models.PositiveSmallIntegerField(
        verbose_name='Slaidi namba ngapi',
        choices=POSITIONS,
        unique=True,
        help_text='Nafasi ya slaidi kwenye ukurasa wa mwanzo. Slaidi 1 = "Matokeo & Taaluma", 7 = ripoti ya mzazi.',
    )
    image = models.ImageField(
        verbose_name='Picha ya shule',
        upload_to='marketing/hero_slides/',
        blank=True,
        help_text=(
            'Picha halisi ya shule yako (darasa, uwanja, maktaba, wanafunzi). '
            'JPG/PNG/WEBP, upana wa angalau 1200px, usizidi 8MB. '
            'Ukiacha nafasi tupu, slaidi hii huendelea kuonyesha mchoro wa kipengele.'
        ),
    )

    class Meta:
        ordering = ('position',)
        verbose_name = 'Slaidi ya ukurasa wa mwanzo'
        verbose_name_plural = 'Slaidi za ukurasa wa mwanzo'

    def __str__(self):
        return self.get_position_display()

    @property
    def has_image(self):
        return bool(self.image)

    def clean(self):
        super().clean()
        self.validate_image_file()

    def validate_image_file(self):
        upload = self.image
        if not upload:
            return

        errors = []
        if Path(upload.name).suffix.lower() not in self.ALLOWED_EXTENSIONS:
            errors.append('Ruhusu faili za aina hizi pekee: JPG, PNG, WEBP.')

        size_mb = (upload.size or 0) / 1024 / 1024
        if size_mb > self.MAX_UPLOAD_MB:
            errors.append(f'Picha ni {size_mb:.1f}MB. Pakia picha ya {self.MAX_UPLOAD_MB}MB au chini.')

        if errors:
            raise ValidationError({'image': errors})

        try:
            upload.seek(0)
            with Image.open(upload) as opened:
                width, height = opened.size
        except OSError:
            raise ValidationError({'image': 'Faili hili halawezi kusomwa kama picha. Jaribu tena au chagua faili lingine.'})
        finally:
            upload.seek(0)

        if width < self.MIN_WIDTH:
            raise ValidationError({
                'image': (
                    f'Picha hii ina upana wa {width}px tu. Inahitaji angalau {self.MIN_WIDTH}px '
                    f'ili ijalie vizuri kwenye slaidi kubwa. Pakia picha kutoka kamerani, siyo picha ya skrini.'
                )
            })


class DemoRequest(models.Model):
    """Ombi la shule linalotaka onyesho la ShulePlusERP."""
    school_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    student_count = models.CharField(max_length=50, blank=True, null=True, help_text='Mfano: 300 hadi 800')
    message = models.TextField(blank=True, null=True)
    is_contacted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ombi la Onyesho'
        verbose_name_plural = 'Maombi ya Maonyesho'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.school_name} - {self.contact_name}"
