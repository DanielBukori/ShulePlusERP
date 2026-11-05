from io import BytesIO
from importlib import import_module
from tempfile import TemporaryDirectory

from django.apps import apps as global_apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from marketing.models import DemoRequest, HeroSlide

seed_migration = import_module('marketing.migrations.0003_heroslide_upload_slots')

OVERSIZE_BYTES = HeroSlide.MAX_UPLOAD_MB * 1024 * 1024 + 1024


def make_upload(name='hero.jpg', width=1600, height=900, color='navy'):
    content = BytesIO()
    Image.new('RGB', (width, height), color=color).save(content, format='JPEG')
    return SimpleUploadedFile(name, content.getvalue(), content_type='image/jpeg')


class HeroSlideTestBase:
    """Kila jaribio huanza kwa nafasi tupu ili matokeo yasiotegemeea mpangilio wa migration."""

    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        HeroSlide.objects.all().delete()


class HeroSlotSeedTests(HeroSlideTestBase, TestCase):
    def test_seed_creates_the_seven_empty_slots_once(self):
        seed_migration.seed_hero_slide_slots(global_apps, None)
        seed_migration.seed_hero_slide_slots(global_apps, None)

        self.assertEqual(
            list(HeroSlide.objects.values_list('position', flat=True)),
            [1, 2, 3, 4, 5, 6, 7],
        )
        self.assertEqual(HeroSlide.objects.filter(image='').count(), 7)

    def test_seed_reverse_keeps_slots_that_have_photos(self):
        HeroSlide.objects.create(position=1, image=make_upload('hero.jpg'))
        HeroSlide.objects.create(position=4)

        seed_migration.drop_empty_hero_slide_slots(global_apps, None)

        self.assertEqual(list(HeroSlide.objects.values_list('position', flat=True)), [1])


class HeroSlideLandingTests(HeroSlideTestBase, TestCase):
    def test_fixed_slides_render_even_when_only_some_have_uploaded_images(self):
        slide = HeroSlide.objects.create(position=2, image=make_upload('parents.jpg'))

        response = self.client.get(reverse('marketing:landing_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matokeo, Jedwali Kuu na Ngazi')
        self.assertContains(response, 'Wazazi Wanapata Taarifa')
        self.assertContains(response, 'Taaluma, Ada, Nidhamu na Duka')
        self.assertEqual(response.content.count(b'id="hero-slide-'), 7)
        self.assertContains(
            response,
            reverse('marketing:hero_image', args=[slide.pk]),
        )
        self.assertContains(response, 'const totalHeroSlides = 7;')
        # Slaidi yenye picha ya admin huficha mchoro wa kipengele; zingine zincuwa.
        self.assertEqual(response.content.count(b'class="lg:col-span-5 hidden lg:block"'), 6)
        self.assertEqual(response.content.count(b'class="lg:col-span-5 hidden"'), 1)

    def test_every_uploaded_photo_gets_its_own_readable_scrim(self):
        HeroSlide.objects.create(position=1, image=make_upload('matokeo.jpg'))
        HeroSlide.objects.create(position=5, image=make_upload('walimu.jpg'))

        response = self.client.get(reverse('marketing:landing_page'))

        self.assertEqual(response.content.count(b'class="lp-scrim absolute inset-0 z-0"'), 2)
        self.assertContains(response, '.lp-scrim { background:')
        self.assertContains(response, 'linear-gradient(100deg')

    def test_hero_image_endpoint_returns_uploaded_image(self):
        slide = HeroSlide.objects.create(position=1, image=make_upload('hero.jpg'))

        response = self.client.get(reverse('marketing:hero_image', args=[slide.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')
        image_content = b''.join(response.streaming_content)
        response.close()
        self.assertGreater(len(image_content), 0)

    def test_hero_image_endpoint_returns_404_when_image_is_missing(self):
        slide = HeroSlide.objects.create(position=1)

        response = self.client.get(reverse('marketing:hero_image', args=[slide.pk]))

        self.assertEqual(response.status_code, 404)

    def test_demo_form_still_submits_with_uploads_present(self):
        HeroSlide.objects.create(position=1, image=make_upload('hero.jpg'))

        response = self.client.post(
            reverse('marketing:landing_page'),
            {
                'school_name': 'Sekondari ya Jaribio',
                'contact_name': 'Mwalimu Jaribio',
                'phone': '0700000000',
                'email': 'jaribio@example.com',
                'student_count': '300-800',
                'message': 'Tunataka kuona mfumo.',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(DemoRequest.objects.count(), 1)


class HeroSlideUploadValidationTests(HeroSlideTestBase, TestCase):
    def error_messages(self, **kwargs):
        slide = HeroSlide(**kwargs)
        try:
            slide.full_clean()
        except ValidationError as error:
            return error.message_dict.get('image', [])
        return []

    def test_accepts_wide_jpeg(self):
        self.assertEqual(self.error_messages(position=1, image=make_upload('wide.jpg')), [])

    def test_accepts_png_and_webp(self):
        for name in ('darasa.png', 'uwanja.webp'):
            with self.subTest(name=name):
                self.assertEqual(self.error_messages(position=1, image=make_upload(name)), [])

    def test_rejects_file_that_is_not_an_image(self):
        upload = SimpleUploadedFile('ridhaa.gif', b'\x00\x01\x02', content_type='image/gif')

        errors = self.error_messages(position=1, image=upload)

        self.assertTrue(any('JPG, PNG, WEBP' in message for message in errors))

    def test_rejects_oversized_upload_before_reading_it(self):
        upload = SimpleUploadedFile(
            'kubwa.jpg', b'\xff\xd8\xff' + b'0' * OVERSIZE_BYTES, content_type='image/jpeg'
        )

        errors = self.error_messages(position=1, image=upload)

        self.assertTrue(any('MB' in message for message in errors))

    def test_rejects_image_too_narrow_for_the_hero(self):
        errors = self.error_messages(
            position=1, image=make_upload('ndogo.jpg', width=900, height=506)
        )

        self.assertTrue(any(str(HeroSlide.MIN_WIDTH) in message for message in errors))

    def test_slot_can_stay_empty(self):
        self.assertEqual(self.error_messages(position=3), [])


class HeroSlideAdminUploadTests(HeroSlideTestBase, TestCase):
    def setUp(self):
        super().setUp()
        self.admin_user = get_user_model().objects.create_superuser(
            'qa_admin', 'qa@example.com', 'qa-pass-123'
        )
        self.client.force_login(self.admin_user)
        self.slot = HeroSlide.objects.create(position=6)

    def test_admin_can_upload_a_photo_and_landing_page_shows_it(self):
        change_url = reverse('admin:marketing_heroslide_change', args=[self.slot.pk])

        response = self.client.post(
            change_url,
            {'position': 6, 'image': make_upload('duka.jpg', width=1800, height=1000)},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.has_image)
        self.assertContains(response, 'Imepakwa')

    def test_public_see_the_uploaded_photo_without_logging_in(self):
        change_url = reverse('admin:marketing_heroslide_change', args=[self.slot.pk])
        self.client.post(
            change_url,
            {'position': 6, 'image': make_upload('duka.jpg')},
        )
        self.client.logout()

        landing = self.client.get(reverse('marketing:landing_page'))

        self.assertEqual(landing.status_code, 200)
        self.assertContains(landing, reverse('marketing:hero_image', args=[self.slot.pk]))
        self.assertEqual(landing.content.count(b'class="lg:col-span-5 hidden"'), 1)

    def test_admin_change_form_previews_the_current_photo(self):
        self.slot.image = make_upload('duka.jpg')
        self.slot.save()

        response = self.client.get(
            reverse('admin:marketing_heroslide_change', args=[self.slot.pk])
        )

        self.assertContains(response, reverse('marketing:hero_image', args=[self.slot.pk]))
        self.assertContains(response, 'Muonekano wa slaidi hii')

    def test_admin_rejects_a_small_photo_with_a_swahili_message(self):
        change_url = reverse('admin:marketing_heroslide_change', args=[self.slot.pk])

        response = self.client.post(
            change_url,
            {'position': 6, 'image': make_upload('ndogo.jpg', width=800, height=450)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(HeroSlide.MIN_WIDTH))
        self.slot.refresh_from_db()
        self.assertFalse(self.slot.has_image)

    def test_admin_list_shows_thumbnails_for_slots_with_photos(self):
        with_photo = HeroSlide.objects.create(position=1, image=make_upload('matokeo.jpg'))

        response = self.client.get(reverse('admin:marketing_heroslide_changelist'))

        self.assertContains(response, reverse('marketing:hero_image', args=[with_photo.pk]))
        self.assertContains(response, 'Imepakwa')
        self.assertEqual(response.content.count(b'object-fit:cover'), 1)

    def test_admin_list_names_each_slide_not_just_its_number(self):
        HeroSlide.objects.all().delete()
        seed_migration.seed_hero_slide_slots(global_apps, None)

        response = self.client.get(reverse('admin:marketing_heroslide_changelist'))

        for label in ('Matokeo', 'Mawasiliano ya Wazazi', 'Duka la Shule', 'Ripoti Kamili kwa Mzazi'):
            with self.subTest(label=label):
                self.assertContains(response, label)
        self.assertEqual(HeroSlide.objects.filter(image='').count(), 7)
