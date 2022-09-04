from .. forms import PostForm
from .. models import Post
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.user_test_user)
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
        }
        response = self.authorized_test_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:profile',
                             kwargs={'username': 'test_user'}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый пост номер 3',
            ).exists()
        )

    def test_edit_form(self):
        """Форма post_create работает правильно при редактировании поста"""
        form_data = {
            'text': 'Тестовый пост номер 2 c изменениями',
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
