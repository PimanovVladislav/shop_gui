"""Шаблон печатного чека продажи (русский)."""

WIDTH = 42

TEMPLATES = {
    'store_name': 'МАГАЗИН РЫБОЛОВНЫХ ТОВАРОВ "РЫБАЧОК"',
    'title': 'КАССОВЫЙ ЧЕК',
    'date': 'Дата: {date}',
    'payment_type': 'Тип оплаты: {type}',
    'item_line': '  {qty} x {price:.2f} = {sum:.2f}',
    'total': 'ИТОГО: {sum:.2f}',
    'payed': 'Внесено: {sum:.2f}',
    'change': 'Сдача: {sum:.2f}',
    'footer': 'СПАСИБО ЗА ПОКУПКУ!',
}
