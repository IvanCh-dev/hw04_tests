import datetime

from unittest import mock
from django.forms import fields
from django.utils import dateparse
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.urls import reverse

from .. models import Group, Post
from .. forms import PostForm
from .. views import DISPLAYED_POSTS


User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='auth')

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
        with mock.patch('django.utils.timezone.now') as mock_now:
            moment = dateparse.parse_datetime('2022-09-01 12:00:00')
            for i in range(1, 16):
                mock_now.return_value = moment + datetime.timedelta(seconds=i)
                Post.objects.create(
                    id=i,
                    author=cls.user_auth,
                    text=f'Тестовый пост номер {i}',
                    group=cls.group_1,
                )
        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.user_auth)
        cls.user_test_user = User.objects.create_user(username='test_user')
        cls.authorized_test_user = Client()
        cls.authorized_test_user.force_login(cls.user_test_user)
        Post.objects.create(
            id=16,
            author=cls.user_test_user,
            text='Тестовый пост номер 16',
            group=cls.group_2,
        )

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug-1'}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'auth'}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 15}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': 15}):
                'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_auth.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        for i in range(3):
            first_object = response.context['page_obj'][i]
            first_object_text = first_object.text
            self.assertEqual(
                first_object_text, f'Тестовый пост номер {16 - i}')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-1'})
        )
        group_1 = response.context['group']
        group_1_title = group_1.title
        group_1_slug = group_1.slug
        group_1_description = group_1.description
        self.assertEqual(group_1_title, 'Тестовая группа номер 1')
        self.assertEqual(group_1_slug, 'test-slug-1')
        self.assertEqual(group_1_description, 'Тестовое описание номер 1')
        for i in range(3):
            first_object = response.context['page_obj'][i]
            first_object_text = first_object.text
            first_object_author = first_object.author.username
            first_object_group = first_object.group.title
            self.assertEqual(
                first_object_text, f'Тестовый пост номер {15 - i}')
            self.assertEqual(first_object_author, 'auth')
            self.assertEqual(first_object_group, 'Тестовая группа номер 1')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        user = response.context['author']
        user_username = user.username
        self.assertEqual(user_username, 'auth')
        for i in range(3):
            first_object = response.context['page_obj'][i]
            first_object_text = first_object.text
            first_object_author = first_object.author.username
            first_object_group = first_object.group.title
            self.assertEqual(
                first_object_text, f'Тестовый пост номер {15 - i}')
            self.assertEqual(first_object_author, 'auth')
            self.assertEqual(first_object_group, 'Тестовая группа номер 1')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1})
        )
        post = response.context['post']
        post_id = post.id
        post_text = post.text
        post_author = post.author.username
        post_group = post.group.title
        self.assertEqual(post_id, 1)
        self.assertEqual(post_text, 'Тестовый пост номер 1')
        self.assertEqual(post_author, 'auth')
        self.assertEqual(post_group, 'Тестовая группа номер 1')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_test_user.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': fields.CharField,
            'group': fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context.get('form')
                self.assertIsNotNone(form)
                self.assertIsInstance(form, PostForm)
                self.assertIsInstance(form.fields.get(field_name), field_type)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_test_user.get(
            reverse('posts:post_edit', kwargs={'post_id': 16})
        )
        form_fields = {
            'text': fields.CharField,
            'group': fields.ChoiceField,
        }
        for field_name, field_type in form_fields.items():
            with self.subTest(name=field_name, type=field_type):
                form = response.context.get('form')
                self.assertIsNotNone(form)
                self.assertIsInstance(form, PostForm)
                self.assertIsInstance(form.fields.get(field_name), field_type)

    def test_paginator(self):
        """Paginator index, group_list, profile"""
        urls_to_check = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug-1'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        latest_posts = Post.objects.filter(
            author__username='auth').all()[:DISPLAYED_POSTS]
        for url in urls_to_check:
            response = self.guest_client.get(url)
            context = response.context
            with self.subTest(url=url):
                if url == reverse('posts:index'):
                    latest_posts = Post.objects.all()[:DISPLAYED_POSTS]
                page_obj = context.get('page_obj')
                self.assertIsNotNone(page_obj)
                self.assertIsInstance(page_obj, Page)
                self.assertQuerysetEqual(
                    latest_posts, page_obj, transform=lambda x: x)
                if url == reverse('posts:index'):
                    latest_posts = Post.objects.filter(
                        author__username='auth').all()[:DISPLAYED_POSTS]

    def test_create_post_correct_group_and_profile(self):
        """
        Отображение поста в group_list и profile после его создания.
        """
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-2'})
        )
        post_16 = response.context['page_obj'][0]
        post_16_text = post_16.text
        self.assertEqual(post_16_text, 'Тестовый пост номер 16')
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'test_user'})
        )
        post_16 = response.context['page_obj'][0]
        post_16_text = post_16.text
        self.assertEqual(post_16_text, 'Тестовый пост номер 16')
