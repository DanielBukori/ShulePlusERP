from unittest.mock import patch

from django.test import TestCase
from django.core.management import call_command
from django.urls import reverse

from academic.grading import recompute_derived_results
from shule_core.class_setup import ensure_standard_classes
from shule_core.models import (
    AcademicResult,
    Combination,
    CustomUser,
    School,
    SchoolClass,
    SubjectAssignment,
    Student,
    Subject,
)


class AutoAbsentPublishTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Test School',
            subdomain='testschool',
            email='testschool@example.com',
            phone='255700000001',
        )
        self.school_class = SchoolClass.objects.create(
            name='Form Five',
            school=self.school,
            level='A',
        )
        self.combination = Combination.objects.create(name='PCM')
        self.subject = Subject.objects.create(
            school=self.school,
            name='Physics',
            code='PHY',
            level='A',
            combination=self.combination,
        )
        self.present_student = self.create_student('Present', 'S001')
        self.absent_student = self.create_student('Absent', 'S002')
        self.teacher = CustomUser.objects.create_user(
            username='teacher-user',
            email='teacher@example.com',
            password='test-password',
            role='TEACHER',
            school=self.school,
            must_change_password=False,
        )
        self.assignment = SubjectAssignment.objects.create(
            school=self.school,
            teacher=self.teacher,
            subject=self.subject,
            school_class=self.school_class,
            combination=self.combination,
            academic_year=2026,
        )
        self.user = CustomUser.objects.create_user(
            username='academic-user',
            email='academic@example.com',
            password='test-password',
            role='HEADMASTER',
            school=self.school,
            must_change_password=False,
        )

    def create_student(self, first_name, reg_number):
        return Student.objects.create(
            school=self.school,
            school_class=self.school_class,
            combination=self.combination,
            first_name=first_name,
            last_name='Student',
            reg_number=reg_number,
            parent_name='Parent',
            parent_phone='255700000002',
        )

    def test_publish_creates_auto_absent_and_report_displays_it(self):
        host = f'{self.school.subdomain}.localhost'
        self.client.force_login(self.teacher)
        marks_url = (
            f"{reverse('teacher_portal:enter_marks')}?"
            f"assignment={self.assignment.pk}&term=TERM_1&academic_year=2026"
        )
        response = self.client.post(
            marks_url,
            {f'score_{self.present_student.pk}_TEST_1_A': '65'},
            HTTP_HOST=host,
        )
        self.assertEqual(response.status_code, 302)
        saved_mark = AcademicResult.objects.get(
            student=self.present_student,
            subject=self.subject,
            exam_type='TEST_1_A',
            term='TERM_1',
            academic_year=2026,
        )
        self.assertEqual(saved_mark.combination, self.combination)
        computed_mark = AcademicResult.objects.get(
            student=self.present_student,
            subject=self.subject,
            exam_type='MID_TERM',
            term='TERM_1',
            academic_year=2026,
        )
        self.assertEqual(computed_mark.combination, self.combination)

        self.client.force_login(self.user)

        response = self.client.post(
            reverse('academic:publish_results'),
            {
                'school_class': self.school_class.pk,
                'term': 'TERM_1',
                'exam_type': 'MID_TERM',
                'academic_year': 2026,
                'confirm': 'on',
            },
            HTTP_HOST=host,
        )

        self.assertEqual(response.status_code, 200)
        auto_absent = AcademicResult.objects.get(
            student=self.absent_student,
            subject=self.subject,
            exam_type='MID_TERM',
            term='TERM_1',
            academic_year=2026,
        )
        self.assertEqual(auto_absent.score, 0)
        self.assertEqual(auto_absent.combination, self.combination)
        self.assertTrue(auto_absent.is_auto_absent)
        self.assertTrue(auto_absent.is_published)

        report = self.client.get(
            reverse('academic:auto_absent_report'),
            {
                'term': 'TERM_1',
                'exam_type': 'MID_TERM',
                'academic_year': 2026,
            },
            HTTP_HOST=host,
        )
        self.assertEqual(report.status_code, 200)
        self.assertEqual(report.context['auto_absent_count'], 1)
        self.assertContains(report, 'S002')

    def test_recomputed_a_level_result_keeps_combination(self):
        for exam_type, score in (
            ('TEST_1_A', 60),
            ('TEST_2_A', 70),
            ('MID_TERM_EXAM', 80),
        ):
            AcademicResult.objects.create(
                school=self.school,
                student=self.present_student,
                subject=self.subject,
                combination=self.combination,
                school_class=self.school_class,
                exam_type=exam_type,
                term='TERM_1',
                academic_year=2026,
                score=score,
            )

        recompute_derived_results(
            self.school,
            self.present_student,
            self.subject,
            'TERM_1',
            2026,
            self.school_class,
            combination=self.combination,
        )

        midterm = AcademicResult.objects.get(
            student=self.present_student,
            subject=self.subject,
            exam_type='MID_TERM',
            term='TERM_1',
            academic_year=2026,
        )
        self.assertEqual(midterm.score, 70)
        self.assertEqual(midterm.combination, self.combination)

    def test_backfill_repairs_legacy_a_level_result_combinations(self):
        result = AcademicResult.objects.create(
            school=self.school,
            student=self.present_student,
            subject=self.subject,
            school_class=self.school_class,
            exam_type='TEST_1_A',
            term='TERM_1',
            academic_year=2026,
            score=60,
        )

        call_command('backfill_a_level_result_combinations', dry_run=True)
        result.refresh_from_db()
        self.assertIsNone(result.combination_id)

        call_command('backfill_a_level_result_combinations')
        result.refresh_from_db()
        self.assertEqual(result.combination, self.combination)


class HeadmasterDashboardTenantFallbackTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Dashboard School',
            subdomain='dashboardschool',
            email='dashboard@example.com',
            phone='255700000061',
        )
        self.headmaster = CustomUser.objects.create_user(
            username='dashboard-headmaster',
            password='test-password',
            role='HEADMASTER',
            school=self.school,
            must_change_password=False,
        )

    def test_headmaster_can_open_dashboard_on_base_domain(self):
        self.client.force_login(self.headmaster)

        response = self.client.get(reverse('academic:academic_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['school'], self.school)
        self.assertEqual(
            set(self.school.classes.values_list('name', flat=True)),
            {'Form I', 'Form II', 'Form III', 'Form IV', 'Form V', 'Form VI'},
        )

    def test_school_setup_adds_school_scoped_subject_and_extra_class_stream(self):
        self.client.force_login(self.headmaster)
        setup_url = reverse('academic:school_setup')

        response = self.client.get(setup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Form VI')

        response = self.client.post(
            setup_url,
            {'action': 'add_class', 'name': 'Form I', 'stream': 'SCIENCE'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            self.school.classes.filter(name='Form I', stream='SCIENCE', level='O').exists()
        )

        response = self.client.post(
            setup_url,
            {
                'action': 'add_subject',
                'name': 'Mathematics',
                'code': 'mat',
                'level': 'O',
            },
        )
        self.assertEqual(response.status_code, 302)
        subject = Subject.objects.get(school=self.school, code='MAT')
        self.assertEqual(subject.level, 'O')
        self.assertIsNone(subject.combination_id)

    def test_a_level_subject_requires_matching_combination(self):
        self.client.force_login(self.headmaster)
        setup_url = reverse('academic:school_setup')
        combination = Combination.objects.create(name='PCM')
        invalid_response = self.client.post(
            setup_url,
            {
                'action': 'add_subject',
                'name': 'Physics',
                'code': 'PHY',
                'level': 'A',
            },
        )
        self.assertEqual(invalid_response.status_code, 200)
        self.assertFalse(Subject.objects.filter(school=self.school, code='PHY').exists())

        valid_response = self.client.post(
            setup_url,
            {
                'action': 'add_subject',
                'name': 'Physics',
                'code': 'phy',
                'level': 'A',
                'combination': combination.pk,
            },
        )
        self.assertEqual(valid_response.status_code, 302)
        self.assertTrue(
            Subject.objects.filter(
                school=self.school,
                code='PHY',
                level='A',
                combination=combination,
            ).exists()
        )

    def test_setup_post_creates_subject_only_for_authenticated_school(self):
        other_school = School.objects.create(
            name='Other Setup School',
            subdomain='othersetupschool',
            email='other-setup@example.com',
            phone='255700000062',
        )
        self.client.force_login(self.headmaster)

        response = self.client.post(
            reverse('academic:school_setup'),
            {
                'action': 'add_subject',
                'name': 'Biology',
                'code': 'BIO',
                'level': 'O',
                'school': other_school.pk,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subject.objects.filter(school=self.school, code='BIO').exists())
        self.assertFalse(Subject.objects.filter(school=other_school, code='BIO').exists())

    def test_school_manager_cannot_change_shared_combination_catalog(self):
        self.client.force_login(self.headmaster)
        response = self.client.post(
            reverse('academic:school_setup'),
            {'action': 'add_combination', 'name': 'XYZ'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Combination.objects.filter(name='XYZ', level='A').exists())


class StandardSchoolClassSetupTests(TestCase):
    def test_school_level_classes_are_created_idempotently(self):
        expected = {
            'O': {'Form I', 'Form II', 'Form III', 'Form IV'},
            'A': {'Form V', 'Form VI'},
            'B': {'Form I', 'Form II', 'Form III', 'Form IV', 'Form V', 'Form VI'},
        }
        for level, class_names in expected.items():
            with self.subTest(level=level):
                school = School.objects.create(
                    name=f'{level} Level School',
                    subdomain=f'{level.lower()}levelschool',
                    email=f'{level.lower()}-level@example.com',
                    phone=f'25570000007{"OAB".index(level)}',
                    school_level=level,
                )
                ensure_standard_classes(school)
                ensure_standard_classes(school)
                self.assertEqual(
                    set(school.classes.filter(stream='GENERAL').values_list('name', flat=True)),
                    class_names,
                )

    def test_user_without_school_cannot_open_school_dashboard(self):
        user_without_school = CustomUser.objects.create_user(
            username='school-less-headmaster',
            email='school-less-headmaster@example.com',
            password='test-password',
            role='HEADMASTER',
            must_change_password=False,
        )
        self.client.force_login(user_without_school)

        response = self.client.get(reverse('academic:academic_dashboard'))

        self.assertEqual(response.status_code, 403)


class StudentRegistrationPinTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Student PIN School',
            subdomain='studentpin',
            email='studentpin@example.com',
            phone='255700000021',
        )
        self.school_class = SchoolClass.objects.create(
            name='Form One',
            school=self.school,
            level='O',
        )
        self.academic_user = CustomUser.objects.create_user(
            username='studentpin-academic',
            email='studentpin-academic@example.com',
            password='test-password',
            role='ACADEMIC',
            school=self.school,
            must_change_password=False,
        )
        self.url = reverse('academic:register_student')
        self.host = 'studentpin.localhost'
        self.client.force_login(self.academic_user)
        self.data = {
            'first_name': 'Asha',
            'last_name': 'Mwanafunzi',
            'reg_number': 'REG001',
            'school_class': self.school_class.pk,
            'parent_name': 'Mzazi',
            'parent_phone': '0712345678',
        }

    @patch('academic.views.send_sms', return_value={'sent': True})
    @patch('academic.views.secrets.randbelow', side_effect=[123456, 234567])
    def test_random_student_and_parent_pins_are_sent_not_rendered(self, _pin, send):
        response = self.client.post(self.url, self.data, HTTP_HOST=self.host, follow=True)

        student = Student.objects.get(reg_number='REG001', school=self.school)
        student_user = student.user
        parent_user = student.parent
        self.assertNotEqual(student_user.password, self.data['reg_number'])
        self.assertTrue(student_user.check_password('334567'))
        self.assertTrue(parent_user.check_password('223456'))
        self.assertTrue(student_user.is_active)
        self.assertTrue(parent_user.is_active)
        self.assertEqual(send.call_count, 1)
        sms_message = send.call_args.args[2]
        self.assertNotContains(response, '334567')
        self.assertIn('PIN 334567', sms_message)
        self.assertIn('PIN 223456', sms_message)
        self.assertNotContains(response, '223456')

    @patch('academic.views.send_sms', return_value={'sent': False, 'reason': 'no_credentials'})
    def test_sms_failure_leaves_generated_accounts_disabled(self, send):
        self.data.update(reg_number='REG002', parent_phone='0712345679')

        response = self.client.post(self.url, self.data, HTTP_HOST=self.host, follow=True)

        student = Student.objects.get(reg_number='REG002', school=self.school)
        self.assertFalse(student.user.is_active)
        self.assertFalse(student.parent.is_active)
        self.assertContains(response, 'SMS ya PIN haikutumwa')
