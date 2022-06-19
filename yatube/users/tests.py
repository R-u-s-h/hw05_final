from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Nekrasov')
        cls.user_not_author = User.objects.create_user(username='Levadniy')

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user_author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            StaticURLTests.user_not_author
        )

    def test_return_status_ok_for_unauth_user(self):
        http_addresses = (
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_return_status_ok_for_auth_user(self):
        http_addresses = (
            '/auth/logout/',
            '/auth/password_reset/',
        )
        for url in http_addresses:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
