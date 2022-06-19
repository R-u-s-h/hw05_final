from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Group, Post, User
from posts.forms import PostForm


class TestsPostPostForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cls.author = User.objects.create(username='Levadniy')
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Описание группы',
            slug='test-slug')
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.author,
            group=cls.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """При отправке формы со страницы создания создаётся новый пост."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=self.group.id,
            ).exists()
        )
        response = (self.authorized_client.get(reverse('posts:index')))
        first_object = response.context['page_obj'][0].text
        self.assertEqual(first_object, 'Тестовый текст')

    def test_post_edit(self):
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст изменённый',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id':
                                                       self.post.pk}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст изменённый',
                group=self.group.id,
            ).exists()
        )
