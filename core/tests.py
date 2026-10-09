import logging

from django.http import HttpRequest
from django.test import SimpleTestCase

from core.middleware import ExceptionLoggingMiddleware


class ExceptionLoggingMiddlewareTests(SimpleTestCase):
    def test_logs_exception_path_and_traceback_without_request_data(self):
        request = HttpRequest()
        request.method = 'GET'
        request.path = '/register-school/'
        middleware = ExceptionLoggingMiddleware(lambda request: None)

        try:
            raise RuntimeError('template failure')
        except RuntimeError as error:
            with self.assertLogs('core.exceptions', level='ERROR') as captured:
                middleware.process_exception(request, error)

        self.assertIn('GET /register-school/', captured.output[0])
        self.assertIn('RuntimeError: template failure', captured.output[0])
