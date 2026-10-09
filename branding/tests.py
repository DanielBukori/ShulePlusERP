from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from branding.models import BrandingPost
from shule_core.models import School, CustomUser


class SchoolAssetViewTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            subdomain='testschool',
            email='school@example.com',
            phone='255700000001',
        )
        self.host = 'testschool.localhost'
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

    def asset_url(self, kind, object_id):
        return reverse(
            'branding:school_asset',
            kwargs={
                'subdomain': self.school.subdomain,
                'kind': kind,
                'object_id': object_id,
            },
        )

    def test_school_logo_is_served_through_tenant_scoped_view(self):
        self.school.logo = SimpleUploadedFile('logo.png', b'public logo bytes', content_type='image/png')
        self.school.save()

        response = self.client.get(
            self.asset_url('school-logo', self.school.pk),
            HTTP_HOST=self.host,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(b''.join(response.streaming_content), b'public logo bytes')

    def test_unpublished_branding_image_requires_same_school_manager(self):
        post = BrandingPost.objects.create(
            school=self.school,
            category='GENERAL',
            title='Draft',
            body='Not published',
            image=SimpleUploadedFile('draft.png', b'draft image bytes', content_type='image/png'),
            is_published=False,
        )
        url = self.asset_url('post-image', post.pk)

        self.assertEqual(self.client.get(url, HTTP_HOST=self.host).status_code, 404)

        manager = CustomUser.objects.create_user(
            username='school-manager',
            email='manager@example.com',
            password='test-password',
            role='HEADMASTER',
            school=self.school,
            must_change_password=False,
        )
        self.client.force_login(manager)
        response = self.client.get(url, HTTP_HOST=self.host)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'draft image bytes')

    def test_school_media_cannot_be_read_through_another_tenant_host(self):
        other_school = School.objects.create(
            name='Other School',
            subdomain='otherschool',
            email='other@example.com',
            phone='255700000002',
        )
        self.school.logo = SimpleUploadedFile('logo.png', b'private bytes', content_type='image/png')
        self.school.save()

        response = self.client.get(
            self.asset_url('school-logo', self.school.pk),
            HTTP_HOST=f'{other_school.subdomain}.localhost',
        )

        self.assertEqual(response.status_code, 404)
