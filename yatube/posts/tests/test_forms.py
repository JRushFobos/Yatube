import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        '''Вызывается один раз перед запуском всех тестов класса.'''
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='Мокрушин',
            first_name='Евгений',
            last_name='Мокрушин',
            email='fobos_media@mail.ru',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        '''Подготовка прогона теста. Вызывается перед каждым тестом.'''
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_form_create(self):
        '''Проверка создания нового поста, авторизированным пользователем'''
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст поста для формы',
            'image': uploaded,
        }
        Post.objects.all().delete()
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )

        self.assertRedirects(
            response,
            reverse('posts:profile', args=[self.post.author.username]),
        )
        object = Post.objects.all().first()
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(object.text, form_data['text'])
        self.assertEqual(object.group.id, form_data['group'])
        self.assertEqual(object.author, self.post.author)
        self.assertEqual(object.image.name, 'posts/small.gif')

    def test_form_update(self):
        '''Проверка редактирования поста через форму на странице.'''
        post_count = Post.objects.count()
        form_data = {
            'group': self.group.id,
            'text': 'Обновленный текст поста',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.pk]),
            data=form_data,
            follow=True,
        )
        object = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(object.text, form_data['text'])
        self.assertEqual(object.group.id, form_data['group'])
        self.assertEqual(object.author, self.post.author)
        self.assertEqual(Post.objects.count(), post_count)

    def test_authorized_client_create_comment(self):
        Comment.objects.all().delete()
        post = Post.objects.create(
            text='Пост для комментария', author=self.post.author
        )
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.author)
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[post.id])
        )

    def test_non_authorized_client_create_comment(self):
        Comment.objects.all().delete()
        post = Post.objects.create(
            text='Пост для комментария', author=self.post.author
        )
        form_data = {'text': 'Тестовый комментарий'}
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('login')
            + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': post.id}),
        )
