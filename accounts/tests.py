from django.test import TestCase, override_settings
from django.urls import reverse


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
