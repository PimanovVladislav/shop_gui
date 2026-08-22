"""Доменные константы (не зависят от UI и БД)."""

# Статусы чеков: 0 — ожидание, 1 — продажа, 2 — возврат, 3 — списание
CHECK_STATUS_PENDING = 0
CHECK_STATUS_SALE = 1
CHECK_STATUS_RETURN = 2
CHECK_STATUS_WRITEOFF = 3

# Обратная совместимость со старыми именами
CHECK_STATUS_SALE_LEGACY = CHECK_STATUS_SALE
CHECK_STATUS_RETURN_LEGACY = CHECK_STATUS_RETURN
CHECK_STATUS_WRITEOFF_LEGACY = CHECK_STATUS_WRITEOFF
