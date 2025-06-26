import tkinter as tk
from tkinter import ttk, messagebox
from analysis_window import AnalysisWindow
from cash_register_window import CashRegisterWindow
from database_operation import Database
from warehouse_window import WarehouseWindow

DB_NAME = 'fish_store.db'

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учет и торговля рыболовными товарами")
        self.geometry("300x150")
        self.wm_iconbitmap("main_icon.ico")

        self.db = Database()
        self.child_windows = []

        btn_cash = tk.Button(self, text="Касса", width=20, command=self.open_cash_register)
        btn_cash.pack(pady=5)

        btn_warehouse = tk.Button(self, text="Склад", width=20, command=self.open_warehouse)
        btn_warehouse.pack(pady=5)

        btn_analysis = tk.Button(self, text="Анализ", width=20, command=self.open_analysis)
        btn_analysis.pack(pady=5)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def open_cash_register(self):
        win = CashRegisterWindow(self, self.db)
        self.child_windows.append(win)

    def open_warehouse(self):
        win = WarehouseWindow(self, self.db)
        self.child_windows.append(win)

    def open_analysis(self):
        win = AnalysisWindow(self, self.db)
        self.child_windows.append(win)

    def on_close(self):
        if self.child_windows:
            messagebox.showwarning("Внимание", "Закройте все окна перед выходом.")
            return
        self.db.close()
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
