import tkinter as tk
from tkinter import ttk
import base_products as bp
import kassa as kas
import analisys as an

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.iconbitmap(default="main_icon.ico")
        self.title("Мой магазин")
        self.geometry("300x250")
        self.put_frames()
        self.mainloop()

    def put_frames(self):
        self.frame_kassa = Kassa(self).pack(padx=10, pady=20)
        self.frame_base_product = Base_product(self).pack(padx=10, pady=10)
        self.frame_analisys = Analisys(self).pack(padx=10, pady=10)


class Kassa(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.put_widgets()
    def put_widgets(self):
        self.kassa_btn = ttk.Button(self, text="Касса", command=kas.open_kassa)
        self.kassa_btn.pack(padx=10, pady=10)

class Base_product(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.put_widgets()

    def put_widgets(self):
        self.base_products_btn = ttk.Button(self, text="Склад", command=bp.open_base_products)
        self.base_products_btn.pack(padx=10, pady=10)


class Analisys(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        self.put_widgets()

    def put_widgets(self):
        self.analisys_btn = ttk.Button(self, text="Анализ", command=an.open_analisys)
        self.analisys_btn.pack(padx=10, pady=10)


# frame_kassa.pack(padx=10, pady=20)
# frame_base_product.pack(padx=10, pady=10)
# frame_analisys.pack(padx=10, pady=10)

# kassa_btn = ttk.Button(frame_kassa, text="Касса", command=kas.open_kassa)
# base_products_btn = ttk.Button(frame_base_product, text="Склад", command=bp.open_base_products)
# analisys_btn = ttk.Button(frame_analisys, text="Анализ", command=an.open_analisys)

# kassa_btn.pack(padx=10, pady=10)
# base_products_btn.pack(padx=10, pady=10)
# analisys_btn.pack(padx=10, pady=10)

main_window = App()
main_window.mainloop()