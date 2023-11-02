import re

from django.core.exceptions import ValidationError


def validate_username(value):
    """
    Проверка используемых символов в поле username.
    """
    value_check = ', '.join(set(re.sub(r'[\w.@+-]+', r'', value)))
    if value_check:
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы:{value_check}')
