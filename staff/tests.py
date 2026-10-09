from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from shule_core.models import CustomUser, School, Staff


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
