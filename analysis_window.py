import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
from utils import SearchPanel, SortableTreeview, filter_with_checked, center_window, DATE_PATTERN, format_date, today_str
from excel_export import ExcelExporter


class AnalysisWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.title("Анализ продаж")
        self.geometry("1100x650")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.db = db

        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="Период с:").pack(side=tk.LEFT)
        self.date_from = DateEntry(top_frame, locale="ru_RU", width=12,
                                   background="darkblue", foreground="white",
                                   borderwidth=2, date_pattern=DATE_PATTERN)
        self.date_from.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="по:").pack(side=tk.LEFT)
        self.date_to = DateEntry(top_frame, locale="ru_RU", width=12,
                                 background="darkblue", foreground="white",
                                 borderwidth=2, date_pattern=DATE_PATTERN)
        self.date_to.pack(side=tk.LEFT, padx=5)

        tk.Button(top_frame, text="Обновить",
                  command=self.refresh_data).pack(side=tk.LEFT, padx=10)

        self.search_panel = SearchPanel(top_frame, search_callback=self.filter_rows)
        self.search_panel.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        self.search_panel.bind_shortcuts(self)

        columns = ("check", "last_sale_date", "product_id", "product_name",
                   "sold_qty", "returned_qty", "net_qty", "stock_qty",
                   "sold_sum", "returned_sum", "net_sum")
        self.tree = SortableTreeview(
            self, columns=columns, show='headings', checkbox_column=True
        )

        headings = {
            "check": "☐",
            "last_sale_date": "Дата последней продажи",
            "product_id": "Код товара",
            "product_name": "Наименование",
            "sold_qty": "Продано шт.",
            "returned_qty": "Возврат шт.",
            "net_qty": "Итого шт.",
            "stock_qty": "Остаток на складе",
            "sold_sum": "Сумма продаж",
            "returned_sum": "Сумма возвратов",
            "net_sum": "Итого сумма",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, anchor=tk.CENTER, width=80)
        self.tree.column("check", width=30, stretch=False)
        self.tree.column("last_sale_date", width=130)
        self.tree.column("product_name", width=200, anchor=tk.W)
        self.tree.column("product_id", width=70)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.setup_sorting()

        btn_row = tk.Frame(self)
        btn_row.pack(fill=tk.X, padx=10, pady=(0, 5))
        tk.Button(btn_row, text="Экспорт в Excel",
                  command=self.export_to_excel).pack(side=tk.LEFT, padx=2)

        summary_frame = tk.Frame(self)
        summary_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.label_total_earned = tk.Label(summary_frame,
                                           text="Всего заработано: 0.00")
        self.label_total_earned.pack(anchor=tk.W, pady=2)
        self.label_top_sold = tk.Label(summary_frame,
                                       text="Самый продаваемый товар: -")
        self.label_top_sold.pack(anchor=tk.W, pady=2)
        self.label_top_earned = tk.Label(summary_frame,
                                         text="Товар с наибольшей выручкой: -")
        self.label_top_earned.pack(anchor=tk.W, pady=2)

        today = datetime.today()
        self.date_from.set_date(today.replace(day=1))
        self.date_to.set_date(today)

        self.all_rows = []
        center_window(self)
        self.refresh_data()

    def refresh_data(self):
        self.tree.delete(*self.tree.get_children())

        date_from = self.date_from.get_date()
        date_to = self.date_to.get_date()

        if date_from > date_to:
            messagebox.showerror("Ошибка",
                                 "Дата начала не может быть позже даты конца.",
                                 parent=self)
            return

        rows = self.db.get_sales_analysis(date_from, date_to)

        self.all_rows.clear()
        for r in rows:
            code = r[0]
            name = r[1]
            last_sale = format_date(r[2]) if r[2] else '—'
            sold_qty = r[3] or 0
            returned_qty = r[4] or 0
            net_qty = r[5] or 0
            stock_qty = r[6] or 0
            sold_sum = float(r[7] or 0)
            returned_sum = float(r[8] or 0)
            net_sum = float(r[9] or 0)
            row = (
                last_sale, code, name,
                sold_qty, returned_qty, net_qty, stock_qty,
                f"{sold_sum:.2f}", f"{returned_sum:.2f}", f"{net_sum:.2f}"
            )
            self.all_rows.append(row)

        self._display_rows(self.all_rows)
        self.update_summaries(self.all_rows)

    def _display_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            iid = str(row[1])
            self.tree.insert('', 'end', iid=iid, values=row)
        self.tree.restore_checks()
        self.tree.move_checked_to_top()

    def filter_rows(self, query):
        query = query.strip().lower()
        if not query:
            self._display_rows(self.all_rows)
            self.update_summaries(self.all_rows)
            return

        checked_keys = set(self.tree.get_checked_iids())
        mapping = {
            'last_sale_date': 0, 'product_id': 1, 'product_name': 2,
            'sold_qty': 3, 'returned_qty': 4, 'net_qty': 5, 'stock_qty': 6,
            'sold_sum': 7, 'returned_sum': 8, 'net_sum': 9,
        }
        search_col = self.tree.get_search_column()

        def match(row):
            if search_col is not None and search_col in mapping:
                idx = mapping[search_col]
                return idx < len(row) and query in str(row[idx]).lower()
            return any(query in str(cell).lower() for cell in row)

        filtered = filter_with_checked(
            self.all_rows, checked_keys, match, lambda row: str(row[1])
        )
        self._display_rows(filtered)
        self.update_summaries(filtered)

    def update_summaries(self, rows):
        if not rows:
            self.label_total_earned.config(text="Всего заработано: 0.00")
            self.label_top_sold.config(text="Самый продаваемый товар: -")
            self.label_top_earned.config(text="Товар с наибольшей выручкой: -")
            return
        total_earned = sum(float(row[9]) for row in rows)
        top_sold = max(rows, key=lambda r: int(r[5]))
        top_earned = max(rows, key=lambda r: float(r[9]))
        self.label_total_earned.config(text=f"Всего заработано: {total_earned:.2f}")
        self.label_top_sold.config(
            text=f"Самый продаваемый товар: Код {top_sold[1]}, {top_sold[2]}, "
                 f"Кол-во: {top_sold[5]}")
        self.label_top_earned.config(
            text=f"Товар с наибольшей выручкой: Код {top_earned[1]}, {top_earned[2]}, "
                 f"Сумма: {float(top_earned[9]):.2f}")

    def export_to_excel(self):
        checked = self.tree.get_checked_values()
        rows = checked if checked else self.all_rows
        if not rows:
            messagebox.showwarning("Внимание", "Нет данных для экспорта.", parent=self)
            return
        headers = ["Дата последней продажи", "Код товара", "Наименование",
                   "Продано шт.", "Возврат шт.", "Итого шт.", "Остаток",
                   "Сумма продаж", "Сумма возвратов", "Итого сумма"]
        filename = f"Отчет_{today_str()}.xlsx"
        filepath = ExcelExporter.export_data(
            headers, rows, filename=filename, sheet_title="Анализ продаж")
        ExcelExporter.open_file(filepath)
        messagebox.showinfo("Экспорт", f"Файл сохранён:\n{filepath}", parent=self)

    def on_close(self):
        if hasattr(self.master, "child_windows") and self in self.master.child_windows:
            self.master.child_windows.remove(self)
        self.destroy()
