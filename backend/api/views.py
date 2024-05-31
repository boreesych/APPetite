from django.conf import settings
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .paginations import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeReadSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SetAvatarSerializer,
                          SubscribeSerializer, SubscribeViewSerializer,
                          ShoppingCartSerializer, TagSerializer)
from recipes.models import (FavoriteRecipe, Ingredient,
                            Recipe, RecipeIngredients,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        methods=('post',),
        detail=True,
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={'author': author.id, 'user': request.user.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            SubscribeViewSerializer(
                author, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        author = get_object_or_404(User, id=id)
        is_deleted, _ = (
            Subscribe.objects.filter(author=author, user=request.user).delete()
        )
        if not is_deleted:
            return Response({"message": "Подписки не существует"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        return self.get_paginated_response(
            SubscribeViewSerializer(
                self.paginate_queryset(
                    User.objects.filter(subscribing__user=request.user)
                ),
                many=True,
                context={'request': request}
            ).data
        )

    @action(
        methods=('put',),
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def set_avatar(self, request):
        serializer = SetAvatarSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        setattr(request.user, 'avatar', None)
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    pagination_class = LimitPageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recipe.objects.prefetch_related(
                'tags', 'ingredients').select_related(
                'author').annotate_user_recipe(self.request.user)
        return Recipe.objects.prefetch_related(
            'tags', 'ingredients').select_related(
            'author')

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk):
        return self.create_object(FavoriteRecipeSerializer, request, pk)

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        is_deleted, _ = FavoriteRecipe.objects.filter(
            user=request.user,
            recipe=recipe).delete()
        if not is_deleted:
            return Response({"message": "Не удалось удалить"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        return self.create_object(ShoppingCartSerializer, request, pk)

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        is_deleted, _ = (
            ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).delete()
        )
        if not is_deleted:
            return Response({"message": "Не удалось удалить"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @staticmethod
    def create_object(serializer_name, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = serializer_name(
            data={'user': request.user.id, 'recipe': recipe.pk, },
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeShortSerializer(
                get_object_or_404(Recipe, id=pk)
            ).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def create_shopping_list(ingredients):
        shopping_list = ('Список покупок\n\n')
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        filename = 'shopping_list.txt'
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response

    @action(detail=False,
            methods=['get'],
            permission_classes=[IsAuthorOrReadOnly])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.carts.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        ingredients = RecipeIngredients.objects.filter(
            recipe__carts__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(
                    amount=Sum('amount')).order_by(
                        'ingredient__name')
        return self.create_shopping_list(ingredients)

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(
            f'/{settings.SHORT_LINK_PREFIX_PATH}{recipe.short_link}'
        )
        return Response({'short-link': short_link})
