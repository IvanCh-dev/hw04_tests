from .. forms import PostForm
from .. models import Post, Group
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user_test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.user_test_user)
        cls.group_1 = Group.objects.create(
            title='Тестовая группа номер 1',
            slug='test-slug-1',
            description='Тестовое описание номер 1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа номер 2',
            slug='test-slug-2',
            description='Тестовое описание номер 2',
        )
        Post.objects.create(
            id=1,
            text='Тестовый пост номер 1',
            author=cls.user_test_user,
        )
        Post.objects.create(
            id=2,
            text='Тестовый пост номер 2',
            author=cls.user_test_user,
        )
        cls.form = PostForm()

    def test_create_form(self):
        """Форма post_create работает правильно при создании поста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост номер 3',
            'group': self.group_1.id,
        }
        response = self.authorized_test_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'test_user'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_3 = Post.objects.get(text='Тестовый пост номер 3')
        self.assertEqual(
            User.objects.get(username='test_user').username,
            post_3.author.username
        )
        self.assertEqual(
            Group.objects.get(title='Тестовая группа номер 1').title,
            post_3.group.title
        )

    def test_edit_form(self):
        """Форма post_create работает правильно при редактировании поста"""
        form_data = {
            'text': 'Тестовый пост номер 2 c изменениями',
            'group': self.group_2.id,
        }
        response = self.authorized_test_user.post(
            reverse('posts:post_edit', kwargs={'post_id': 2}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                             kwargs={'post_id': 2}))
        self.assertEqual(
            Post.objects.get(id=2).text,
            'Тестовый пост номер 2 c изменениями'
        )
        self.assertFalse(
            Post.objects.get(id=2).group.title
            == 'Тестовая группа номер 1'
        )
