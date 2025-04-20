import tkinter as tk
from tkinter import ttk, Toplevel
import database_operation as dbo

def open_kassa():
    kassa = Toplevel()
    kassa.geometry('400x400')
    kassa.title("Касса")
    kassa.grab_set()

def open_base_products():
    base_products = Toplevel()
    screen_width = base_products.winfo_screenwidth()
    screen_height = base_products.winfo_screenheight()
    # base_products.geometry(f"{screen_width}x{screen_height}+0+0")
    base_products.title("Мои товары")
    base_products.grab_set()

    add_new_product_frame = ttk.Frame(base_products, height=300, width=500)
    all_products_frame = ttk.Frame(base_products)

    add_new_product_frame.pack(expand=tk.YES, fill=tk.BOTH)
    all_products_frame.pack(expand=tk.YES, fill=tk.BOTH)

    name_product_label = tk.Label(add_new_product_frame, text='Наименование товара')
    buy_price_product_label = tk.Label(add_new_product_frame, text='Цена по закупке')
    sale_price_product_label = tk.Label(add_new_product_frame, text='Цена при продаже')
    amount_product_label = tk.Label(add_new_product_frame, text='Количество')

    name_product_entry = tk.Entry(add_new_product_frame)
    buy_price_product_entry = tk.Entry(add_new_product_frame)
    sale_price_product_entry = tk.Entry(add_new_product_frame)
    amount_product_entry = tk.Entry(add_new_product_frame)
    save_product_btn = tk.Button(add_new_product_frame, text='Сохранить')

    name_product_label.grid(row=0, column=0)
    name_product_entry.grid(row=0, column=1)
    buy_price_product_label.grid(row=1, column=0)
    buy_price_product_entry.grid(row=1, column=1)
    sale_price_product_label.grid(row=2, column=0)
    sale_price_product_entry.grid(row=2, column=1)
    amount_product_label.grid(row=3, column=0)
    amount_product_entry.grid(row=3, column=1)
    save_product_btn.grid(row=4, column=0)

    heads = ['Код товара','Наименование','Цена по закупке','Цена при продаже','Количество']
    table = ttk.Treeview(all_products_frame, show='headings')
    table['columns'] = heads
    table['displaycolumns'] = heads

    for header in heads:
        table.heading(header, text=header, anchor='center')
        table.column(header, anchor='center')

    for row in dbo.get_products():
        table.insert('', tk.END, values=row)

    scroll_pane = ttk.Scrollbar(all_products_frame, command=table.yview)
    scroll_pane.pack(side=tk.RIGHT, fill=tk.Y, padx=10)
    table.configure(yscrollcommand=scroll_pane.set)
    table.pack(expand=tk.YES, fill=tk.BOTH)





def open_analisys():
    analisys = Toplevel()
    analisys.geometry('500x500')
    analisys.title("Анализ")
    analisys.grab_set()

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

kassa_btn = ttk.Button(frame_kassa, text="Касса", command=open_kassa)
base_products_btn = ttk.Button(frame_base_product, text="Склад", command=open_base_products)
analisys_btn = ttk.Button(frame_analisys, text="Анализ", command=open_analisys)

kassa_btn.pack(padx=10, pady=10)
base_products_btn.pack(padx=10, pady=10)
analisys_btn.pack(padx=10, pady=10)


main_window.mainloop()