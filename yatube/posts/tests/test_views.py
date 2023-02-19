from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post, User

from ..forms import PostForm
from ..settings import PER_PAGE

TOTAL_POSTS = PER_PAGE + 1
INDEX = reverse('posts:index')
HTTP_404_NOT_FOUND = 404
HTTP_403_FORBIDDEN = 403


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем авторизованый клиент
        cls.user = User.objects.create(username='User')
        cls.second_user = User.objects.create(username='Second_User')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client.force_login(cls.second_user)
        # Создадим группу в БД
        cls.group = Group.objects.create(
            title='Первая группа',
            slug='test-slug',
            description='Описание группы'
        )
        # Создадим вторую группу в БД
        cls.second_group = Group.objects.create(
            title='Вторая группа',
            slug='test-slug-new',
            description='Отличная группа от тестовой'
        )
        # Создадим 13 постов в первой группе БД
        for post in range(13):
            cls.post = Post.objects.bulk_create([
                Post(
                    text='Записи первой группы',
                    author=cls.user,
                    group=cls.group,)
                for i in range(TOTAL_POSTS)
            ])

        # Создадим 2 поста во второй группе в БД
        for post in range(2):
            cls.post = Post.objects.create(
                text='Записи второй группы',
                author=cls.second_user,
                group=cls.second_group
            )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse('posts:profile', kwargs={'username': 'User'}): (
                'posts/profile.html'
            ),
            reverse('posts:post_detail', kwargs={'post_id': (self.post.pk)}): (
                'posts/post_detail.html'
            ),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': (self.post.pk)}): (
                'posts/create_post.html'
            ),
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)
        self.assertIn('text', response.context)
        self.assertIn('description', response.context)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'User'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)
        self.assertIn('page_obj', response.context)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': (self.post.pk)})
        )
        self.assertIn('post', response.context)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', args=(self.post.pk,)))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], PostForm)

    class PaginatorViewsTest(TestCase):
        @classmethod
        def setUpClass(cls):
            super().setUpClass()
            cls.user = User.objects.create(username='tester')
            Post.objects.bulk_create([
                Post(
                    text='Тестовый текст',
                    author=cls.user,
                ) for i in range(TOTAL_POSTS)
            ])

        def test_first_page_contains_records(self):
            response = self.client.get(INDEX)
            self.assertEqual(len(response.context['page_obj']), PER_PAGE)

        def test_second_page_contains_records(self):
            response = self.client.get(f'{INDEX}?page=2')
            calculation_len_obj = len(response.context['page_obj'])
            calculation_obj = TOTAL_POSTS % PER_PAGE
            self.assertEqual(calculation_len_obj, calculation_obj)

    # проверка комментов
    def test_comment_available(self):
        '''Комментировать посты может только авторизованный пользователь'''
        form_data = {'text': 'Тестовый комметарий'}
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertTrue(response, 'Тестовый комметарий')

    def comment_in_context(self):
        '''После успешной отправки комментарий появляется на странице поста'''
        form_data = {'text': 'Тестовый комметарий'}
        self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True)
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        self.assertIn('comments', response.context)

    # Проверка работы кеша
    def test_cache_index(self):
        """Проверка cache index.html"""
        response = self.authorized_client.get(INDEX)
        post = Post.objects.create(
            text=self.post.pk,
            author=self.post.author
        )
        page = response.content
        self.assertEqual(page, response.content)
        post.delete()
        response = self.client.get(INDEX)
        cache.clear()
        self.assertNotEqual(response, response.content)

    class CoreTestClass(TestCase):
        """Тест на проверку 404 ошибки"""
        def test_page_not_found(self):
            response = self.client.get('/nonexist-page/')
            self.assertEqual(response.status_code, HTTP_404_NOT_FOUND)
            self.assertTemplateUsed(response, 'core/404.html')

        def test_csrf_failure(self):
            response = self.client.get('core/403csrf.html')
            self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
            self.assertTemplateUsed(response, 'core/403csrf.html')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create(username='user')
        cls.user_following = User.objects.create(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.following_client = Client()
        self.follower_client = Client()
        self.following_client.force_login(self.user_following)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Зарегистрированный пользователь может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписавшихся."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)


cache.clear()
