from hashlib import shake_128
from random import randint

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        'Название ингредиента',
        max_length=settings.INGREDIENTS_NAME_MAX_LENGTH,
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=settings.MEASUREMENT_UNITS_MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Список ингредиентов'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='ingredient_unit'
            )
        ]

    def __str__(self):
        return f'{self.name} {self.measurement_unit}'


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        'Название тега',
        max_length=settings.TAGS_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        'Slug',
        max_length=settings.TAGS_MAX_LENGTH,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Список тегов'
        ordering = ('name',)

    def __str__(self):
        return self.slug


class RecipeQuerySet(models.QuerySet):
    def annotate_user_recipe(self, user):
        return self.annotate(
            is_favorited=models.Exists(user.favorites.filter(
                recipe=models.OuterRef('pk'))),
            is_in_shopping_cart=models.Exists(user.carts.filter(
                recipe=models.OuterRef('pk')))
        )


class Recipe(models.Model):
    """Модель рецепта."""

    name = models.CharField(
        'Название рецепта',
        max_length=settings.RECIPES_NAME_MAX_LENGTH,
        help_text='Введите название блюда',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )
    text = models.TextField(
        'Описание',
        help_text='Опишите процесс приготовления блюда',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор')
    image = models.ImageField(
        'Изображение',
        upload_to='recipes/images/',
    )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1, 'Время приготовления не может быть меньше 1'
            )
        ]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredients',
        blank=True,
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    short_link = models.CharField(
        'Сокращенная ссылка', max_length=16
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Список рецептов'

    def __str__(self):
        return self.name

    def generate_unique_short_id(self, text):
        short_link = shake_128(text.encode('utf-8')).hexdigest(6)
        if Recipe.objects.filter(short_link=short_link).exists():
            shift = randint(0, 9)
            return self.generate_unique_short_id(text + str(shift))
        return short_link

    def save(self, *args, **kwargs):
        if self.short_link is None:
            self.short_link = self.generate_unique_short_id(self.text)
        super().save(*args, **kwargs)


class RecipeIngredients(models.Model):
    """Промежуточная модель рецепт-ингредиент."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',)
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                1, 'Количество ингредиента не может быть меньше 1'
            )
        ]
    )

    class Meta:
        verbose_name = 'Состав рецепта'
        verbose_name_plural = 'Состав рецептов'

    def __str__(self):
        return f'{self.ingredient} - {self.amount}'


class RecipeUserModel(models.Model):
    """Абстрактная модель связи пользователь-рецепт."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.recipe} добавлен к пользователю {self.user}'


class FavoriteRecipe(RecipeUserModel):
    """Модель избранных рецептов."""

    class Meta(RecipeUserModel.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(RecipeUserModel):
    """Модель рецептов в корзине."""

    class Meta(RecipeUserModel.Meta):
        default_related_name = 'carts'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
