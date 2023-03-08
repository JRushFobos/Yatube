from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
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
        cls.another_user = User.objects.create_user(
            username='Миллер',
            first_name='Евгений',
            last_name='Мокрушин',
            email='fobos_media@mail.ru',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_edit_url_exists_at_desired_location(self):
        '''Страница /posts/<post_id>/edit/ доступна любому пользователю.'''
        self.authorized_client.force_login(self.another_user)
        addresses = (
            (
                (self.guest_client.get(reverse('posts:post_create'))),
                (
                    reverse('users:login')
                    + '?next='
                    + reverse('posts:post_create')
                ),
            ),
            (
                (
                    self.guest_client.get(
                        reverse(
                            'posts:post_edit', kwargs={'post_id': self.post.id}
                        )
                    )
                ),
                (
                    reverse('users:login')
                    + '?next='
                    + reverse(
                        'posts:post_edit', kwargs={'post_id': self.post.id}
                    )
                ),
            ),
            (
                (
                    self.authorized_client.get(
                        reverse(
                            'posts:post_edit',
                            kwargs={'post_id': self.post.id},
                        )
                    )
                ),
                (
                    reverse(
                        'posts:post_detail', kwargs={'post_id': self.post.id}
                    )
                ),
            ),
        )

        for address, redirect in addresses:
            with self.subTest(address=address):
                self.assertRedirects(address, redirect)

    def test_status_code_template_non_auth_and_auth(self):
        '''Тесты статусов ответов и шаблонов неавторизированного и
        авторизированного пользователя.
        '''
        templates_url_names = [
            (reverse('posts:index'), HTTPStatus.OK, self.guest_client),
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                HTTPStatus.OK,
                self.guest_client,
            ),
            (
                reverse('posts:profile', kwargs={'username': self.user}),
                HTTPStatus.OK,
                self.guest_client,
            ),
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
                HTTPStatus.OK,
                self.guest_client,
            ),
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                HTTPStatus.OK,
                self.authorized_client,
            ),
            (
                reverse('posts:post_create'),
                HTTPStatus.OK,
                self.authorized_client,
            ),
            ('/unexisting_page', HTTPStatus.NOT_FOUND, self.guest_client),
        ]

        for address, code, auth in templates_url_names:
            with self.subTest(address=address):
                response = auth.get(address)
                self.assertEqual(response.status_code, code)

    def test_status_code_template(self):
        '''Тесты шаблонов пользователя.'''
        templates_url_names = (
            (reverse('posts:index'), 'posts/index.html'),
            (
                reverse('posts:group_list', kwargs={'slug': self.group.slug}),
                'posts/group_list.html',
            ),
            (
                reverse('posts:profile', kwargs={'username': self.user}),
                'posts/profile.html',
            ),
            (
                reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
                'posts/post_detail.html',
            ),
            (
                reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
                'posts/create_post.html',
            ),
            (
                reverse('posts:post_create'),
                'posts/create_post.html',
            ),
            (
                reverse('users:password_reset_form'),
                'users/password_reset_form.html',
            ),
            (
                '/unexisting_page',
                'core/404.html',
            ),
        )

        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_name_address(self):
        '''Проверка соответствия фактических адресов страниц с их именами.'''
        templates_address_names = [
            ('/', reverse('posts:index')),
            (
                f'/group/{self.group.slug}/',
                reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            ),
            (
                f'/profile/{self.user}/',
                reverse('posts:profile', args=[self.user.username]),
            ),
            (
                f'/posts/{self.post.id}/',
                reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            ),
            ('/create/', reverse('posts:post_create')),
            (
                f'/posts/{self.post.id}/edit/',
                reverse('posts:post_edit', args=[self.post.id]),
            ),
        ]
        for address, name in templates_address_names:
            with self.subTest(address=address):
                self.assertEqual(address, name)
