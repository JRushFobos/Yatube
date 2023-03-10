from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    SYMBOL_POST_QUANTITY = 15
    text = models.TextField(
        verbose_name='Тест', help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
    )
    image = models.ImageField('Картинка', upload_to='posts/', blank=True)

    class Meta:
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'
        ordering = ('-pub_date',)

    def __str__(self):
        '''Возвращает строковое представление модели'''
        return self.text


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        help_text='200 characters max.',
        verbose_name='Заголовок',
    )
    slug = models.SlugField(unique=True, verbose_name='Слаг')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name_plural = 'Группы'
        verbose_name = 'Группы'

    def __str__(self):
        '''Возвращает строковое представление модели'''
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Комментарий',
        help_text='Текст комментария',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(
        verbose_name='Тест комментария', help_text='Текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        constraints = [
            (
                models.UniqueConstraint(
                    fields=['user', 'author'], name='unique_follower'
                )
            ),
            (
                models.CheckConstraint(
                    # имя констрейна
                    name='restriction_of_following_yourself',
                    # ~ отрицание | Q условие | F - field (author)
                    check=~models.Q(user=models.F('author')),
                )
            ),
        ]
