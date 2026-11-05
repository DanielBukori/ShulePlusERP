# Seeded by hand: nafasi 7 za slaidi za landing page, picha bado tupu.

from django.db import migrations, models

HERO_SLIDE_POSITIONS = range(1, 8)


def seed_hero_slide_slots(apps, schema_editor):
    HeroSlide = apps.get_model('marketing', 'HeroSlide')
    taken = set(HeroSlide.objects.values_list('position', flat=True))
    HeroSlide.objects.bulk_create(
        HeroSlide(position=position) for position in HERO_SLIDE_POSITIONS if position not in taken
    )


def drop_empty_hero_slide_slots(apps, schema_editor):
    # Usifute slaidi yenye picha - faili la picha lingebaki kwenye diski.
    HeroSlide = apps.get_model('marketing', 'HeroSlide')
    HeroSlide.objects.filter(image='').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0002_heroslide'),
    ]

    operations = [
        migrations.AlterField(
            model_name='heroslide',
            name='image',
            field=models.ImageField(blank=True, help_text='Picha halisi ya shule yako (darasa, uwanja, maktaba, wanafunzi). JPG/PNG/WEBP, upana wa angalau 1200px, usizidi 8MB. Ukiacha nafasi tupu, slaidi hii huendelea kuonyesha mchoro wa kipengele.', upload_to='marketing/hero_slides/'),
        ),
        migrations.AlterField(
            model_name='heroslide',
            name='position',
            field=models.PositiveSmallIntegerField(choices=[(1, '1 - Matokeo & Taaluma'), (2, '2 - Mawasiliano ya Wazazi'), (3, '3 - Nidhamu na Usalama'), (4, '4 - Ada na Malipo'), (5, '5 - Kwa Walimu'), (6, '6 - Duka la Shule'), (7, '7 - Ripoti Kamili kwa Mzazi')], help_text='Nafasi ya slaidi kwenye landing page. Slaidi 1 = "Matokeo & Taaluma", 7 = ripoti ya mzazi.', unique=True),
        ),
        migrations.RunPython(seed_hero_slide_slots, drop_empty_hero_slide_slots),
    ]
