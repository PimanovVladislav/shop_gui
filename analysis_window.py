import tkinter as tk
from utils import SortableTreeview
from database_operation import Database

class AnalysisWindow(tk.Toplevel):
    def __init__(self, master, db: Database):
        super().__init__(master)
        self.db = db
        self.title("Анализ")
        self.geometry("700x400")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # Для примера - покажем список чеков с суммами
        self.tree = SortableTreeview(self, columns=('id', 'date', 'status', 'payment_type', 'sum', 'payed_sum', 'refused_sum'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('date', text='Дата')
        self.tree.heading('status', text='Статус')
        self.tree.heading('payment_type', text='Тип оплаты')
        self.tree.heading('sum', text='Сумма')
        self.tree.heading('payed_sum', text='Внесено')
        self.tree.heading('refused_sum', text='Сдача')

        self.tree.column('id', width=2)
        self.tree.column('date', width=50)
        self.tree.column('status', width=30)
        self.tree.column('payment_type', width=30)
        self.tree.column('sum', width=30)
        self.tree.column('payed_sum', width=30)
        self.tree.column('refused_sum', width=30)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.setup_sorting()
        self.refresh_data()

    def refresh_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        c = self.db.conn.cursor()
        c.execute('''
            SELECT checks.id, strftime('%d.%m.%Y %H:%M', checks.date), checks.status, payment_type.name, checks.sum, checks.payed_sum, checks.refused_sum
            FROM checks LEFT JOIN payment_type ON checks.payment_type = payment_type.id
            ORDER BY checks.date DESC
        ''')
        rows = c.fetchall()
        status_map = {0: 'Ожидание оплаты', 1: 'Покупка', 2: 'Возврат'}
        for r in rows:
            self.tree.insert('', 'end', values=(
                r[0], r[1], status_map.get(r[2], 'Неизвестно'), r[3], f"{r[4]:.2f}", f"{r[5]:.2f}", f"{r[6]:.2f}"
            ))

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()