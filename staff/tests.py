from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from staff.forms import SubjectAssignmentForm
from shule_core.models import (
    Combination,
    CustomUser,
    School,
    SchoolClass,
    Staff,
    Subject,
)


class StaffRegistrationPinTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Staff PIN School',
            subdomain='staffpin',
            email='staffpin@example.com',
            phone='255700000031',
        )
        self.manager = CustomUser.objects.create_user(
            username='staffpin-manager',
            email='staffpin-manager@example.com',
            password='test-password',
            role='HEADMASTER',
            school=self.school,
            must_change_password=False,
        )
        self.client.force_login(self.manager)
        self.url = reverse('staff:register_teacher')
        self.host = 'staffpin.localhost'
        self.data = {
            'role': 'TEACHER',
            'first_name': 'Mwalimu',
            'last_name': 'Mmoja',
            'phone': '0712345680',
            'email': 'new-teacher@example.com',
        }

    @patch('staff.views.send_sms', return_value={'sent': True})
    @patch('staff.views.secrets.randbelow', return_value=123456)
    def test_random_pin_is_sent_and_not_shown_in_registration_response(self, _pin, send):
        response = self.client.post(self.url, self.data, HTTP_HOST=self.host, follow=True)

        user = CustomUser.objects.get(email='new-teacher@example.com')
        staff = Staff.objects.get(user=user)
        self.assertTrue(user.check_password('223456'))
        self.assertTrue(user.is_active)
        self.assertIn('PIN 223456', send.call_args.args[2])
        self.assertNotContains(response, '223456')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(staff.pk)

    @patch('staff.views.send_sms', return_value={'sent': False, 'reason': 'no_credentials'})
    def test_failed_sms_leaves_staff_account_disabled(self, _send):
        response = self.client.post(self.url, self.data, HTTP_HOST=self.host, follow=True)

        user = CustomUser.objects.get(email='new-teacher@example.com')
        self.assertFalse(user.is_active)
        self.assertContains(response, 'SMS ya PIN haikutumwa')


class StaffManagerBaseDomainTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Base Domain Staff School',
            subdomain='basedomainstaff',
            email='basedomainstaff@example.com',
            phone='255700000041',
        )
        self.manager = CustomUser.objects.create_user(
            username='basedomain-manager',
            email='basedomain-manager@example.com',
            password='test-password',
            role='HEADMASTER',
            school=self.school,
            must_change_password=False,
        )
        self.client.force_login(self.manager)

    def test_school_manager_can_open_teacher_list_on_render_domain(self):
        response = self.client.get(reverse('staff:teacher_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['school'], self.school)


class SubjectAssignmentIntegrityFormTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name='Assignment Form School',
            subdomain='assignmentform',
            email='assignmentform@example.com',
            phone='255700000081',
        )
        self.o_class = SchoolClass.objects.create(
            school=self.school, name='Form One', level='O'
        )
        self.a_class = SchoolClass.objects.create(
            school=self.school, name='Form Five', level='A'
        )
        self.combination = Combination.objects.create(name='PCM')
        self.other_combination = Combination.objects.create(name='PCB')
        self.o_subject = Subject.objects.create(
            school=self.school, name='Mathematics', code='MAT', level='O'
        )
        self.a_subject = Subject.objects.create(
            school=self.school,
            name='Physics',
            code='PHY',
            level='A',
            combination=self.combination,
        )

    def test_assignment_rejects_mismatched_class_and_subject_levels(self):
        form = SubjectAssignmentForm(
            {
                'subject': self.o_subject.pk,
                'school_class': self.a_class.pk,
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('school_class', form.errors)

    def test_assignment_rejects_a_different_a_level_combination(self):
        form = SubjectAssignmentForm(
            {
                'subject': self.a_subject.pk,
                'school_class': self.a_class.pk,
                'combination': self.other_combination.pk,
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('combination', form.errors)

    def test_assignment_fields_are_limited_to_the_current_school(self):
        other_school = School.objects.create(
            name='Other Assignment School',
            subdomain='otherassignment',
            email='otherassignment@example.com',
            phone='255700000082',
        )
        other_class = SchoolClass.objects.create(
            school=other_school, name='Form One', level='O'
        )
        other_subject = Subject.objects.create(
            school=other_school, name='Biology', code='BIO', level='O'
        )
        form = SubjectAssignmentForm(
            {
                'subject': other_subject.pk,
                'school_class': other_class.pk,
                'academic_year': 2026,
            },
            school=self.school,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('subject', form.errors)
        self.assertIn('school_class', form.errors)
