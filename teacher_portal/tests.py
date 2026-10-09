from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from shule_core.models import CustomUser, School, SchoolClass, Subject
from teacher_portal.models import HomePackage


class HomePackageDownloadTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Package Test School',
            subdomain='packagetest',
            email='package-school@example.com',
            phone='255700000003',
        )
        self.media_dir = TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.teacher = CustomUser.objects.create_user(
            username='package-teacher',
            email='package-teacher@example.com',
            password='test-password',
            role='TEACHER',
            school=self.school,
            must_change_password=False,
        )
        school_class = SchoolClass.objects.create(
            name='Form 1',
            school=self.school,
            level='O',
        )
        subject = Subject.objects.create(
            school=self.school,
            name='Mathematics',
            code='MATH',
            level='O',
        )
        self.package = HomePackage.objects.create(
            school=self.school,
            teacher=self.teacher,
            subject=subject,
            school_class=school_class,
            term='TERM_1',
            academic_year=2026,
            title='Revision',
            file=SimpleUploadedFile('revision.txt', b'homework content'),
        )
        self.url = reverse(
            'teacher_portal:download_home_package',
            kwargs={'package_id': self.package.pk},
        )

    def test_only_the_package_teacher_can_download_the_file(self):
        other_teacher = CustomUser.objects.create_user(
            username='other-package-teacher',
            email='other-package-teacher@example.com',
            password='test-password',
            role='TEACHER',
            school=self.school,
            must_change_password=False,
        )
        self.client.force_login(other_teacher)
        forbidden = self.client.get(self.url, HTTP_HOST='packagetest.localhost')
        self.assertEqual(forbidden.status_code, 403)

        self.client.force_login(self.teacher)
        response = self.client.get(self.url, HTTP_HOST='packagetest.localhost')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'homework content')
