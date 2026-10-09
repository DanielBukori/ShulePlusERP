from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from shule_core.models import CustomUser


class LoginThrottleTests(TestCase):
    @override_settings(AXES_FAILURE_LIMIT=3)
    def test_repeated_invalid_logins_are_locked_out(self):
        url = reverse('accounts:login')
        response = None
        for _ in range(3):
            response = self.client.post(
                url,
                {'username': 'unknown-user', 'password': 'incorrect-password'},
                REMOTE_ADDR='192.0.2.80',
                HTTP_HOST='localhost',
            )

        self.assertEqual(response.status_code, 429)


class OTPLoginTests(TestCase):
    @patch('accounts.views.send_otp')
    def test_otp_verification_logs_in_with_password_authentication_backend(self, send_otp):
        user = CustomUser.objects.create_user(
            username='teacher-otp',
            password='A-strong-password-123',
            role='TEACHER',
            phone='255700000001',
        )

        login_response = self.client.post(
            reverse('accounts:login'),
            {'username': user.username, 'password': 'A-strong-password-123'},
            HTTP_HOST='localhost',
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(send_otp.call_count, 1)
        otp_session = self.client.session['pending_otp']
        authentication_backend = otp_session['backend']

        verify_response = self.client.post(
            reverse('accounts:otp_verify'),
            {'otp': otp_session['code']},
            HTTP_HOST='localhost',
        )

        self.assertEqual(verify_response.status_code, 302)
        self.assertEqual(
            self.client.session['_auth_user_backend'],
            authentication_backend,
        )
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
