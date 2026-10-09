from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from marketing.models import HeroSlide


class HeroSlideTests(TestCase):
    def setUp(self):
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

    def make_image(self, name):
        content = BytesIO()
        Image.new('RGB', (800, 450), color='navy').save(content, format='JPEG')
        return SimpleUploadedFile(name, content.getvalue(), content_type='image/jpeg')

    def test_fixed_slides_render_even_when_only_some_have_uploaded_images(self):
        slide = HeroSlide.objects.create(position=2, image=self.make_image('parents.jpg'))

        response = self.client.get(reverse('marketing:landing_page'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Matokeo, Broadsheet, na Division')
        self.assertContains(response, 'Wazazi Wanapata Taarifa')
        self.assertContains(response, 'Taaluma, Ada, Nidhamu na Duka')
        self.assertEqual(response.content.count(b'id="hero-slide-'), 7)
        self.assertContains(
            response,
            reverse('marketing:hero_image', args=[slide.pk]),
        )
        self.assertContains(response, 'const totalHeroSlides = 7;')
        self.assertContains(response, '<svg class=" w-28 h-28 mx-auto mb-4"')
        self.assertContains(response, '<svg class="hidden w-28 h-28 mx-auto mb-4"')

    def test_hero_image_endpoint_returns_uploaded_image(self):
        slide = HeroSlide.objects.create(position=1, image=self.make_image('hero.jpg'))

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
