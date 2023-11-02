from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    '''Модель пользователя'''
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    username = models.CharField(
        'Логин',
        validators=(validate_username,),
        max_length=settings.USER_FIELD_MAX_LENGTH,
        unique=True,
        null=False,
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.USER_FIELD_MAX_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.USER_FIELD_MAX_LENGTH,
    )
    email = models.EmailField(
        'Почта',
        max_length=settings.EMAIL_MAX_LENGTH,
        unique=True,
        null=False,
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to='users/',
        blank=True,
    )

    class Meta:
        ordering = ('email', )
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribing',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                name='subscribe_object_unique',
                fields=['user', 'author'],
            ),
            models.CheckConstraint(
                name='prevent_self_subscribe',
                check=~models.Q(user=models.F('author')),
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
