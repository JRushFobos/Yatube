from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse


from ..models import Follow, Group, Post
from ..forms import PostForm

from django.conf import settings

User = get_user_model()


class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        '''Вызывается один раз перед запуском всех тестов класса.'''
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mokrushin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_without_posts = Group.objects.create(
            title='Группа без постов',
            slug='test-slug_without_posts',
            description='Тестовое описание',
        )
        cls.another_user = User.objects.create_user(
            username='Миллер',
            first_name='Евгений',
            last_name='Мокрушин',
            email='fobos_media@mail.ru',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост №1',
            group=cls.group,
            image=uploaded,
        )

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.follower_client = Client()
        self.follower_client.force_login(self.another_user)

    def test_show_correct_context_index_group_list_profile(self):
        '''Шаблон index group_list profile сформирован с правильным
        контекстом.
        '''
        cache.clear()
        objects = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        ]

        for object in objects:
            response = self.authorized_client.get(object)
            first_object = response.context['page_obj'][0]
            self.assertEqual(first_object, self.post)
            self.assertEqual(first_object.image, self.post.image)

    def test_show_correct_context_post_detail(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context['post'], self.post)
        self.assertEqual(response.context['post'].image, self.post.image)

    def test_show_correct_object_group_list(self):
        '''Проверка страницы группы передается объект группы.'''
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        response_profile = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        objects = (
            (response_profile.context.get('author'), self.post.author),
            (
                response_group_list.context.get('group').title,
                self.post.group.title,
            ),
            (
                response_group_list.context.get('group').slug,
                self.post.group.slug,
            ),
            (
                response_group_list.context.get('group').description,
                self.post.group.description,
            ),
        )
        for value, expected in objects:
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_create_post_correct_context(self):
        '''Форма добавления поста с правильным контекстом'''
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)

    def test_create_edit_correct_context(self):
        '''Шаблон create_edit сформирован с правильным контекстом.'''
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['form'].instance, self.post)

    def test_post_with_group_not_shown_on_page_another_group(self):
        '''Проверяем пост с группой не отображается в другой группе.'''
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_without_posts.slug},
            )
        )
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_index_cache(self):
        '''Проверка работы кеша на странице index'''
        post_for_del = Post.objects.create(
            text='Пост для удаления', author=self.user
        )
        check_index_before_del = self.authorized_client.get(
            reverse('posts:index')
        ).content
        post_for_del.delete()
        check_index_after_del = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(check_index_before_del, check_index_after_del)
        cache.clear()
        check_index_after_clear = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(check_index_before_del, check_index_after_clear)

    def test_follow(self):
        '''Проверка подписки.'''
        Follow.objects.all().delete()
        self.follower_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        self.assertEqual(Follow.objects.count(), 1)
        self.assertEqual(Follow.objects.first().user, self.another_user)

    def test_unfollow(self):
        '''Проверка отписки.'''
        Follow.objects.all().delete()
        Follow.objects.create(user=self.another_user, author=self.user)
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user},
            )
        )
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_tape_for_subscribed(self):
        '''Проверка ленты кто на автора подписан.'''
        self.follower_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user})
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertIn(self.post, response.context['page_obj'])

    def test_no_follow_tape_for_sauthors(self):
        '''Проверка ленты кто на автора не подписан.'''
        Follow.objects.all().delete()
        response = self.follower_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response.context['page_obj'])


class Paginator(TestCase):
    TOTAL_POSTS_COUNT = 13
    COEFFICIENT_FOR_NUMBER_LAST_PAGE = 9
    NUMBER_LAST_PAGE = (
        TOTAL_POSTS_COUNT + COEFFICIENT_FOR_NUMBER_LAST_PAGE
    ) // settings.NUM_POSTS

    def posts_on_last_page(TOTAL_POSTS_COUNT):
        if TOTAL_POSTS_COUNT % settings.NUM_POSTS == 0:
            return settings.NUM_POSTS
        else:
            return TOTAL_POSTS_COUNT % settings.NUM_POSTS

    POSTS_ON_LAST_PAGE = posts_on_last_page(TOTAL_POSTS_COUNT)

    @classmethod
    def setUpClass(cls):
        '''Вызывается один раз перед запуском всех тестов класса.'''
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mokrushin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text='Пост для пайджинга',
                    group=cls.group,
                )
                for post in range(cls.TOTAL_POSTS_COUNT)
            ]
        )

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        '''Проверка: количество постов на первой странице равно 10'''
        cache.clear()
        addresses = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', args=[self.user.username]),
        )
        for address in addresses:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                count_post = len(response.context.get('page_obj'))
                self.assertEqual(count_post, settings.NUM_POSTS)

    def test_second_page_contains_three_records(self):
        '''Проверка: на второй странице должно быть три поста.'''
        addresses = (
            reverse('posts:index') + f'?page={self.NUMBER_LAST_PAGE}',
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
            + f'?page={self.NUMBER_LAST_PAGE}',
            reverse('posts:profile', args=[self.user.username])
            + f'?page={self.NUMBER_LAST_PAGE}',
        )

        for address in addresses:
            with self.subTest(address=address):
                response = self.client.get(address)
                count_post = len(response.context.get('page_obj'))
                self.assertEqual(count_post, self.POSTS_ON_LAST_PAGE)
