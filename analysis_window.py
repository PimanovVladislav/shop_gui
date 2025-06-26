import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from utils import SearchPanel, SortableTreeview


class AnalysisWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.title("Анализ продаж")
        self.geometry("900x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.db = db

        # Верхняя панель с выбором периода
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="Период с:").pack(side=tk.LEFT)
        self.date_from = DateEntry(top_frame, locale='ru_RU', width=12, background='darkblue',
                                   foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_from.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="по:").pack(side=tk.LEFT)
        self.date_to = DateEntry(top_frame, locale='ru_RU', width=12, background='darkblue',
                                 foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.date_to.pack(side=tk.LEFT, padx=5)

        btn_refresh = tk.Button(top_frame, text="Обновить", command=self.refresh_data)
        btn_refresh.pack(side=tk.LEFT, padx=10)

        self.search_panel = SearchPanel(top_frame, on_search_callback=self.filter_rows)
        self.search_panel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))

        # Таблица
        columns = ("product_id", "product_name", "sold_qty", "returned_qty",
                   "net_qty", "stock_qty", "sold_sum", "returned_sum", "net_sum")
        self.tree = SortableTreeview(self, columns=columns, show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        headings = {
            "product_id": "Код товара",
            "product_name": "Наименование",
            "sold_qty": "Продано шт.",
            "returned_qty": "Возврат шт.",
            "net_qty": "Итого шт.",
            "stock_qty": "Остаток на складе",
            "sold_sum": "Сумма продаж",
            "returned_sum": "Сумма возвратов",
            "net_sum": "Итого сумма"
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, anchor=tk.CENTER, width=90)
        self.tree.column("product_name", width=200, anchor=tk.W)
        self.tree.column("product_id", width=50)
        self.tree.setup_sorting()

        today = datetime.today()
        self.date_from.set_date(today.replace(day=1))
        self.date_to.set_date(today)

        self.all_rows = []

        # Фрейм для итогов
        summary_frame = tk.Frame(self)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.label_total_earned = tk.Label(summary_frame, text="Всего заработано: 0.00")
        self.label_total_earned.pack(anchor=tk.W, pady=2)

        self.label_top_sold = tk.Label(summary_frame, text="Самый продаваемый товар: -")
        self.label_top_sold.pack(anchor=tk.W, pady=2)

        self.label_top_earned = tk.Label(summary_frame, text="Товар с наибольшей выручкой: -")
        self.label_top_earned.pack(anchor=tk.W, pady=2)

        self.refresh_data()

    def refresh_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        date_from = self.date_from.get_date()
        date_to = self.date_to.get_date()

        if date_from > date_to:
            messagebox.showerror("Ошибка", "Дата начала периода не может быть позже даты конца.")
            return

        rows = self.db.get_sales_analysis(date_from, date_to)

        self.all_rows.clear()
        for r in rows:
            product_id = r[0]
            product_name = r[1]
            sold_qty = r[2] or 0
            returned_qty = r[3] or 0
            net_qty = r[4] or 0
            stock_qty = r[5] or 0
            sold_sum = float(r[6] or 0)
            returned_sum = float(r[7] or 0)
            net_sum = float(r[8] or 0)

            row = (
                product_id,
                product_name,
                sold_qty,
                returned_qty,
                net_qty,
                stock_qty,
                f"{sold_sum:.2f}",
                f"{returned_sum:.2f}",
                f"{net_sum:.2f}"
            )
            self.all_rows.append(row)

        self._display_rows(self.all_rows)
        self.update_summaries(self.all_rows)

    def _display_rows(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in rows:
            self.tree.insert('', 'end', values=row)

    def filter_rows(self, query):
        query = query.strip().lower()
        if not query:
            self._display_rows(self.all_rows)
            self.update_summaries(self.all_rows)
            return

        filtered = []
        for row in self.all_rows:
            if any(query in str(cell).lower() for cell in row):
                filtered.append(row)

        self._display_rows(filtered)
        self.update_summaries(filtered)

    def update_summaries(self, rows):
        if not rows:
            self.label_total_earned.config(text="Всего заработано: 0.00")
            self.label_top_sold.config(text="Самый продаваемый товар: -")
            self.label_top_earned.config(text="Товар с наибольшей выручкой: -")
            return

        # Общая сумма заработка (net_sum - 9-й элемент, индекс 8)
        total_earned = sum(float(row[8]) for row in rows)

        # Самый продаваемый товар по net_qty (5-й элемент, индекс 4)
        top_sold = max(rows, key=lambda r: int(r[4]))

        # Товар с наибольшей выручкой по net_sum (индекс 8)
        top_earned = max(rows, key=lambda r: float(r[8]))

        self.label_total_earned.config(text=f"Всего заработано: {total_earned:.2f}")
        self.label_top_sold.config(
            text=f"Самый продаваемый товар: Код {top_sold[0]}, {top_sold[1]}, Кол-во: {top_sold[4]}"
        )
        self.label_top_earned.config(
            text=f"Товар с наибольшей выручкой: Код {top_earned[0]}, {top_earned[1]}, Сумма: {float(top_earned[8]):.2f}"
        )

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()