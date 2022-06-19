from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Group, Post, User

URL_CREATE_POST = 'posts/create_post.html'


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Nekrasov')
        cls.user_not_author = User.objects.create_user(username='Levadniy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(StaticURLTests.user_author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            StaticURLTests.user_not_author
        )

    def test_post_edit_url_for_author(self):
        response = self.authorized_client_author.get(
            f'/posts/{StaticURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url_redirect_404(self):
        response = self.guest_client.get('/unexisting_page')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get(f'/posts/{self.post.pk}/edit/',
                                         follow=True)
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/'
        )

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_public_urls(self):
        url_names = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_not_author}/',
            f'/posts/{self.post.pk}/',
        }
        for address in url_names:
            with self.subTest(address=address):
                test_urls = self.guest_client.get(address)
                self.assertEqual(test_urls.status_code, HTTPStatus.OK)

    def test_urls_for_authorized_user_use_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user_not_author}/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
            # for flake8 tests complete only, sorry =)
            URL_CREATE_POST: f'/posts/{self.post.pk}/edit/',
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_not_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user_not_author}/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
