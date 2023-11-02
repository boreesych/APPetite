from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from recipes.models import Recipe


@require_http_methods(('GET',))
def redirect_short_link(request, short_link):
    recipe = get_object_or_404(Recipe, short_link=short_link)
    return HttpResponseRedirect(redirect_to=request.build_absolute_uri(
        settings.RECIPE_URL_PATTERN.format(recipe_id=recipe.id)
    ))
