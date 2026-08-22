import tkinter as tk
from tkinter import messagebox

from analysis_window import AnalysisWindow
from cash_register_window import CashRegisterWindow
from check_window import ChecksWindow
from database_operation import Database
from product_store import ProductStore
from config.paths import resource_path
from resources.i18n import load_locale, t
from warehouse_window import WarehouseWindow
from utils import center_window


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        load_locale()

        self.title(t('app.title'))
        self.geometry('300x200')
        self.wm_iconbitmap(resource_path('main_icon.ico'))

        self.db = Database()
        self.product_store = ProductStore(self.db)
        self.child_windows = []

        tk.Button(self, text=t('main.btn.cash'), width=25,
                  command=self.open_cash_register).pack(pady=5)
        tk.Button(self, text=t('main.btn.warehouse'), width=25,
                  command=self.open_warehouse).pack(pady=5)
        tk.Button(self, text=t('main.btn.checks'), width=25,
                  command=self.open_checks).pack(pady=5)
        tk.Button(self, text=t('main.btn.analysis'), width=25,
                  command=self.open_analysis).pack(pady=5)

        self.protocol('WM_DELETE_WINDOW', self.on_close)
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
        if self.child_windows:
            if not messagebox.askyesno(
                    t('common.confirm'),
                    t('main.close_confirm'),
                    parent=self):
                return
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
