"""
Обратная совместимость.

Новый код должен импортировать из пакетов db, domain, resources.
"""

from db.connection import Database
from domain.constants import (
    CHECK_STATUS_PENDING,
    CHECK_STATUS_RETURN,
    CHECK_STATUS_SALE,
    CHECK_STATUS_WRITEOFF,
)

DB_NAME = 'fish_store.db'

__all__ = [
    'Database',
    'DB_NAME',
    'CHECK_STATUS_SALE',
    'CHECK_STATUS_RETURN',
    'CHECK_STATUS_WRITEOFF',
    'CHECK_STATUS_PENDING',
]
