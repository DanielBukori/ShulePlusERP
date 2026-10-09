from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from shule_core.models import Combination, CustomUser, School, SchoolClass, Subject
from teacher_portal.forms import EmergencyMarksFilterForm
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


class EmergencyMarksFilterIntegrityFormTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Emergency Marks School',
            subdomain='emergencymarks',
            email='emergencymarks@example.com',
            phone='255700000091',
        )
        self.o_class = SchoolClass.objects.create(
            school=self.school, name='Form One', level='O'
        )
        self.a_class = SchoolClass.objects.create(
            school=self.school, name='Form Five', level='A'
        )
        self.combination = Combination.objects.create(name='CBG')
        self.other_combination = Combination.objects.create(name='HGL')
        self.o_subject = Subject.objects.create(
            school=self.school, name='Mathematics', code='MATH', level='O'
        )
        self.a_subject = Subject.objects.create(
            school=self.school,
            name='Biology',
            code='BIO',
            level='A',
            combination=self.combination,
        )

    def test_emergency_marks_rejects_class_subject_level_mismatch(self):
        form = EmergencyMarksFilterForm(
            {
                'subject': self.o_subject.pk,
                'school_class': self.a_class.pk,
                'term': 'TERM_1',
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('school_class', form.errors)

    def test_emergency_marks_rejects_wrong_combination(self):
        form = EmergencyMarksFilterForm(
            {
                'subject': self.a_subject.pk,
                'school_class': self.a_class.pk,
                'combination': self.other_combination.pk,
                'term': 'TERM_1',
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('combination', form.errors)

    def test_emergency_marks_fields_are_limited_to_the_current_school(self):
        other_school = School.objects.create(
            name='Other Emergency School',
            subdomain='otheremergencymarks',
            email='otheremergencymarks@example.com',
            phone='255700000092',
        )
        other_class = SchoolClass.objects.create(
            school=other_school, name='Form One', level='O'
        )
        other_subject = Subject.objects.create(
            school=other_school, name='Chemistry', code='CHEM', level='O'
        )
        form = EmergencyMarksFilterForm(
            {
                'subject': other_subject.pk,
                'school_class': other_class.pk,
                'term': 'TERM_1',
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('school_class', form.errors)
