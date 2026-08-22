"""Локализация интерфейса."""

from config.settings import DEFAULT_LOCALE, SUPPORTED_LOCALES
from domain.constants import (
    CHECK_STATUS_PENDING,
    CHECK_STATUS_RETURN,
    CHECK_STATUS_SALE,
    CHECK_STATUS_WRITEOFF,
)

_LOCALES = {
    'ru': 'resources.strings.ru',
    'en': 'resources.strings.en',
}

_CHECK_STATUS_KEYS = {
    CHECK_STATUS_PENDING: 'check.status.pending',
    CHECK_STATUS_SALE: 'check.status.sale',
    CHECK_STATUS_RETURN: 'check.status.return',
    CHECK_STATUS_WRITEOFF: 'check.status.writeoff',
}

_current_locale = DEFAULT_LOCALE
_strings = {}


def load_locale(locale: str = DEFAULT_LOCALE):
    """Загрузить словарь строк для указанной локали."""
    global _current_locale, _strings
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE
    module_name = _LOCALES[locale]
    module = __import__(module_name, fromlist=['STRINGS'])
    _strings = dict(module.STRINGS)
    _current_locale = locale


def get_locale():
    return _current_locale


def t(key: str, default=None, **kwargs) -> str:
    """Получить локализованную строку. kwargs подставляются через str.format."""
    if not _strings:
        load_locale()
    text = _strings.get(key, default if default is not None else key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def check_status_label(status_id: int) -> str:
    """Подпись статуса чека по числовому коду."""
    key = _CHECK_STATUS_KEYS.get(status_id, 'check.status.unknown')
    return t(key)


# Загрузка локали по умолчанию при импорте модуля
load_locale()
