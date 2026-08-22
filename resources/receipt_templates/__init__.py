"""Шаблоны печатных чеков (не UI)."""

from config.settings import DEFAULT_LOCALE
from . import en, ru

_TEMPLATES = {
    'ru': (ru.TEMPLATES, ru.WIDTH),
    'en': (en.TEMPLATES, en.WIDTH),
}


def build_sale_receipt(cart, date_str, payment_type_name, total_sum, payed, refused,
                       format_datetime, locale=None):
    """Собрать текст кассового чека продажи.

    cart: список кортежей (product_id, name, price, amount).
    """
    if locale is None:
        from resources.i18n import get_locale
        locale = get_locale()

    tpl, width = _TEMPLATES.get(locale, _TEMPLATES[DEFAULT_LOCALE])

    def sep(char):
        return char * width

    lines = [
        sep('='),
        tpl['store_name'].center(width),
        tpl['title'].center(width),
        sep('='),
        tpl['date'].format(date=format_datetime(date_str)),
        tpl['payment_type'].format(type=payment_type_name),
        sep('-'),
    ]
    for _product_id, name, price, amount in cart:
        item_sum = price * amount
        lines.append(name)
        lines.append(tpl['item_line'].format(qty=amount, price=price, sum=item_sum))
    lines.extend([
        sep('-'),
        tpl['total'].format(sum=total_sum),
        tpl['payed'].format(sum=payed),
        tpl['change'].format(sum=refused),
        sep('='),
        tpl['footer'].center(width),
    ])
    return '\n'.join(lines)
