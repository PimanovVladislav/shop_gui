"""Sale receipt print template (English)."""

WIDTH = 42

TEMPLATES = {
    'store_name': 'FISHING STORE "РЫБАЧОК"',
    'title': 'SALES RECEIPT',
    'date': 'Date: {date}',
    'payment_type': 'Payment: {type}',
    'item_line': '  {qty} x {price:.2f} = {sum:.2f}',
    'total': 'TOTAL: {sum:.2f}',
    'payed': 'Paid: {sum:.2f}',
    'change': 'Change: {sum:.2f}',
    'footer': 'THANK YOU!',
}
