from django.db import transaction
from django.db.models import F
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredients, ShoppingCart, Tag)
from users.models import Subscribe, User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ('__all__',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
        read_only_fields = ('__all__',)


class UsersSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ('is_subscribed',)

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.subscriber.filter(author=author).exists())


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SubscribeViewSerializer(UsersSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

    class Meta(UsersSerializer.Meta):
        fields = UsersSerializer.Meta.fields + ('recipes', 'recipes_count',)
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit') if request else None
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribe
        fields = ('user', 'author',)

    def validate(self, data):
        author = self.initial_data.get('author')
        user = self.context.get('request').user
        if author == user.id:
            raise serializers.ValidationError(
                {'author': 'Нельзя подписаться на себя.'}
            )
        if user.subscriber.filter(author=author).exists():
            raise serializers.ValidationError(
                {'author': 'Вы уже подписаны на автора.'}
            )
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('__all__',)


class RecipeAddIngredientsSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredients
        fields = ('id', 'amount',)


class NotEmptyBase64ImageField(Base64ImageField):
    def to_internal_value(self, base64_data):
        if not base64_data:
            raise serializers.ValidationError('No file was uploaded.')
        return super().to_internal_value(base64_data)


class RecipeReadSerializer(serializers.ModelSerializer):
    author = UsersSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_ingredients(self, obj):
        return obj.ingredients.values(
            'id',
            'name',
            'measurement_unit',
            amount=F('recipeingredients__amount')
        )


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeAddIngredientsSerializer(many=True, write_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True)
    image = NotEmptyBase64ImageField()
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time', 'author')

    def validate(self, data):
        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredient': 'Нужно выбрать хотя бы один ингредиент!'}
            )
        ingredients_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                {'ingredient': 'Ингредиенты должны быть уникальными!'}
            )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один таг!'
            })
        if len(tags) != len(set(tags)):
            not_unique_tag = ', '.join(
                [tag.name for tag in set(tags) if tags.count(tag) > 1]
            )
            raise serializers.ValidationError({
                'tags': f'Теги <{not_unique_tag}> не уникальны!'
            })
        return data

    @staticmethod
    def create_ingredients_amounts(ingredients, recipe):
        RecipeIngredients.objects.bulk_create(
            [RecipeIngredients(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        )

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_ingredients_amounts(ingredients=ingredients, recipe=recipe)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_ingredients_amounts(
            ingredients=ingredients, recipe=instance)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={'request': self.context.get('request')}
        ).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.context.get('request').method == 'POST':
            recipe = self.initial_data.get('recipe')
            user = self.context.get('request').user
            if user.favorites.filter(recipe=recipe).exists():
                raise serializers.ValidationError(
                    {'recipe': 'Рецепт уже добавлен в избранное.'}
                )
            return data
        recipe = data.get('recipe')
        user = data.get('user')
        if not user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                {'recipe': 'Рецепта нет в избранном.'}
            )
        return data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        if self.context.get('request').method == 'POST':
            recipe = self.initial_data.get('recipe')
            user = self.context.get('request').user
            if user.carts.filter(recipe=recipe).exists():
                raise serializers.ValidationError(
                    {'recipe': 'Рецепт уже добавлен в список покупок.'}
                )
            return data
        recipe = data.get('recipe')
        user = data.get('user')
        if not user.carts.filter(recipe=recipe).exists():
            raise serializers.ValidationError(
                {'recipe': 'Рецепта нет в списке покупок.'}
            )
        return data
