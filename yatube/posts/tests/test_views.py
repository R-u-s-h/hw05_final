from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.conf import settings
from posts.models import Group, Post, User, Comment, Follow
import tempfile
import shutil


POSTS_COUNT: int = 17


class TestsPostPages(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user_author = User.objects.create_user(username='Nekrasov')
        cls.user_not_author = User.objects.create_user(username='Levadniy')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        for i in range(POSTS_COUNT):
            cls.posts = []

            if i == 12:
                group = None
                author = cls.user_not_author
            else:
                group = cls.group
                author = cls.user_author
            post = Post.objects.create(
                author=author,
                text=f'Тестовый пост {i}',
                group=group,
                image=SimpleUploadedFile(
                    name=f'small{i}.gif',
                    content=small_gif,
                    content_type='image/gif')
            )
            cls.posts.append(post)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self) -> None:
        self.guest_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(TestsPostPages.user_author)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(
            TestsPostPages.user_not_author
        )

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user_author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestsPostPages.posts[0].pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': TestsPostPages.posts[0].pk}
            ): 'posts/create_post.html',

            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_page_show_correct_context(self):
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author.username, 'Nekrasov')
        self.assertEqual(first_object.text, 'Тестовый пост 16')
        self.assertEqual(first_object.group.title, 'Тестовая группа')
        self.assertEqual(first_object.image, TestsPostPages.posts[0].image)

    def test_post_group_posts_page_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author.username, 'Nekrasov')
        self.assertEqual(first_object.text, 'Тестовый пост 16')
        self.assertEqual(first_object.group.title, 'Тестовая группа')
        self.assertEqual(first_object.image, TestsPostPages.posts[0].image)

    def test_post_profile_page_show_correct_context(self):
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.user_author})
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author.username, 'Nekrasov')
        self.assertEqual(first_object.text, 'Тестовый пост 16')
        self.assertEqual(first_object.group.title, 'Тестовая группа')
        self.assertEqual(first_object.image, TestsPostPages.posts[0].image)

    def test_post_detail_page_show_correct_context(self):
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': TestsPostPages.posts[0].pk}
            )
        )
        first_object = response.context['post']
        text_0 = first_object.text
        author_0 = first_object.author.username
        group_0 = first_object.group.title
        image_0 = first_object.image
        self.assertEqual(author_0, 'Nekrasov')
        self.assertEqual(text_0, 'Тестовый пост 16')
        self.assertEqual(group_0, 'Тестовая группа')
        self.assertEqual(image_0, TestsPostPages.posts[0].image)

    def test_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user_author}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_seven_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 7)

        response = self.guest_client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 6)

        response = self.guest_client.get(
            reverse(
                'posts:profile', kwargs={'username': self.user_author}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 6)

    def test_page_edit_form_show_correct_context(self):
        response = self.authorized_client_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': TestsPostPages.posts[0].pk}
            )
        )

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_page_create_form_show_correct_context(self):
        response = self.authorized_client_author.get(
            reverse('posts:post_create')
        )

        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PostWithGroupCreationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='Lermontov')
        cls.group_author = Group.objects.create(title='test-title1',
                                                slug='slug_group_author')
        cls.post = Post.objects.create(text='Тестовый текст1',
                                       author=cls.user_author,
                                       group=cls.group_author)
        cls.group_other = Group.objects.create(title='test-title2',
                                               slug='slug_group_other')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_author)

    def test_new_post_on_index_page(self):
        response = (self.authorized_client.get(reverse('posts:index')))
        page_text = str(response.context['page_obj'].object_list)
        self.assertIn(self.post.text, page_text)

    def test_new_post_on_group_page(self):
        response = (self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug':
                                                 self.group_author.slug})))
        page_text = str(response.context['page_obj'].object_list)
        self.assertIn(self.post.text, page_text)

    def test_new_post_on_profile_page(self):
        response = (self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user_author})))
        page_text = str(response.context['page_obj'].object_list)
        self.assertIn(self.post.text, page_text)

    def test_new_post_on_wrong_group_page(self):
        response = (self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug':
                                                 self.group_other.slug})))
        page_text = str(response.context['page_obj'].object_list)
        self.assertNotIn(self.post.text, page_text)


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Nekrasov')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text='Тестовый комментарий',
            post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_comment_view(self):

        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            )
        )
        first_object = response.context.get('comment')[0]
        comment_post_0 = first_object
        self.assertEqual(comment_post_0, CommentViewsTest.comment)

    def test_add_comment_authorized_user(self):
        form_data = {'text': 'Тестовый текст'}
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk},),
            data=form_data)
        self.assertFalse(Comment.objects.filter(
            text='Тестовый текст',).exists())

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk},),
            data=form_data)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertTrue(Comment.objects.filter(
            text='Тестовый текст',).exists())


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Nekrasov')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание группы'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

        self.user = User.objects.create_user(username='HasNoName1')
        self.authorized_client_not_author_1 = Client()
        self.authorized_client_not_author_1.force_login(self.user)

        self.other_user = User.objects.create_user(username='HasNoName2')
        self.authorized_client_not_author_2 = Client()
        self.authorized_client_not_author_2.force_login(self.other_user)

    def test_follower_view(self):
        Follow.objects.create(user=self.user, author=self.author)
        new_post_author = Post.objects.create(
            text='Тестовый текст новый',
            author=self.author,
            group=self.group
        )
        response = self.authorized_client_not_author_1.get(
            reverse('posts:follow_index')
        )
        first_object = response.context.get('page_obj').object_list[0]
        self.assertEqual(first_object, new_post_author)

    def test_not_follower_view(self):
        Follow.objects.create(user=self.other_user, author=self.user)
        Post.objects.create(
            text='Тестовый текст новый',
            author=self.user,
            group=self.group
        )
        new_post_author = Post.objects.create(
            text='Тестовый текст самый новый',
            author=self.author,
            group=self.group
        )
        response = self.authorized_client_not_author_2.get(
            reverse('posts:follow_index')
        )
        first_object = response.context.get('page_obj').object_list[0]
        self.assertNotEqual(first_object, new_post_author)
