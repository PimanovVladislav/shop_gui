import tkinter as tk
from tkinter import messagebox
from analysis_window import AnalysisWindow
from check_window import ChecksWindow
from cash_register_window import CashRegisterWindow
from database_operation import Database
from warehouse_window import WarehouseWindow
from utils import center_window

DB_NAME = 'fish_store.db'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учет и торговля рыболовными товарами")
        self.geometry("300x200")
        self.wm_iconbitmap("main_icon.ico")

        self.db = Database()
        self.child_windows = []

        btn_cash = tk.Button(self, text="Касса", width=25, command=self.open_cash_register)
        btn_cash.pack(pady=5)

        btn_warehouse = tk.Button(self, text="Склад", width=25, command=self.open_warehouse)
        btn_warehouse.pack(pady=5)

        btn_checks = tk.Button(self, text="Просмотр чеков (возврат)", width=25, command=self.open_checks)
        btn_checks.pack(pady=5)

        btn_analysis = tk.Button(self, text="Анализ", width=25, command=self.open_analysis)
        btn_analysis.pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        center_window(self)

    def open_cash_register(self):
        win = CashRegisterWindow(self, self.db)
        self.child_windows.append(win)

    def open_warehouse(self):
        win = WarehouseWindow(self, self.db)
        self.child_windows.append(win)

    def open_checks(self):
        win = ChecksWindow(self, self.db)
        self.child_windows.append(win)

    def open_analysis(self):
        win = AnalysisWindow(self, self.db)
        self.child_windows.append(win)

    def on_close(self):
        # Если открыты дочерние окна — спрашиваем подтверждение
        if self.child_windows:
            if not messagebox.askyesno(
                    "Подтверждение",
                    "Открыты дочерние окна. Вы уверены, что хотите закрыть приложение?",
                    parent=self):
                return
            # закрываем все дочерние окна
            for win in list(self.child_windows):
                try:
                    win.destroy()
                except Exception:
                    pass
            self.child_windows.clear()
        self.db.close()
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
