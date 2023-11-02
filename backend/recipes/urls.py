from django.conf import settings
from django.urls import path

from recipes.views import redirect_short_link

urlpatterns = [
    path(f'{settings.SHORT_LINK_PREFIX_PATH}<str:short_link>',
         redirect_short_link)
]
