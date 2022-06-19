from django.test import TestCase, Client
from http import HTTPStatus


class ViewTestClass(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_error_page(self):
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_error_page_uses_correct_template(self):
        response = self.guest_client.get('core/404.html')
        self.assertTemplateUsed(response, 'core/404.html')
