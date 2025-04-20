import tkinter as tk
from tkinter import ttk, Toplevel
import base_products as bp
import kassa as kas
import analisys as an

main_window = tk.Tk()
main_window.iconbitmap(default="main_icon.ico")
main_window.title("Мой магазин")
main_window.geometry("300x250")

frame_kassa = tk.Frame(main_window)
frame_base_product = tk.Frame(main_window)
frame_analisys = tk.Frame(main_window)

frame_kassa.pack(padx=10, pady=20)
frame_base_product.pack(padx=10, pady=10)
frame_analisys.pack(padx=10, pady=10)

kassa_btn = ttk.Button(frame_kassa, text="Касса", command=kas.open_kassa)
base_products_btn = ttk.Button(frame_base_product, text="Склад", command=bp.open_base_products)
analisys_btn = ttk.Button(frame_analisys, text="Анализ", command=an.open_analisys)

kassa_btn.pack(padx=10, pady=10)
base_products_btn.pack(padx=10, pady=10)
analisys_btn.pack(padx=10, pady=10)


main_window.mainloop()