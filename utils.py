import tkinter as tk
from tkinter import ttk


class SortableTreeview(ttk.Treeview):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self._sort_column = None
        self._sort_reverse = False

    def setup_sorting(self):
        # Для каждого столбца назначаем функцию сортировки при клике
        for col in self['columns']:
            self.heading(col, command=lambda c=col: self.sort_by_column(c, False))

    def sort_by_column(self, col, reverse):
        # Получаем все элементы
        data = [(self.set(k, col), k) for k in self.get_children('')]

        # Пытаемся преобразовать к числу для числовой сортировки
        try:
            data = [(float(item[0]), item[1]) for item in data]
        except ValueError:
            pass  # если не число, сортируем как строки

        # Сортируем данные
        data.sort(reverse=reverse)

        # Перемещаем элементы в отсортированном порядке
        for index, (val, k) in enumerate(data):
            self.move(k, '', index)

        # Переключаем направление сортировки для следующего клика
        self.heading(col, command=lambda: self.sort_by_column(col, not reverse))


class SearchPanel(tk.Frame):
    def __init__(self, master, on_search_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search_callback = on_search_callback

        tk.Label(self, text="Поиск:").pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self._on_search)

        self.entry = tk.Entry(self, textvariable=self.search_var)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _on_search(self, *args):
        query = self.search_var.get()
        self.on_search_callback(query)

    def clear(self):
        self.search_var.set('')