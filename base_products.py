import tkinter as tk
from tkinter import ttk, Toplevel
import database_operation as dbo

class Base_products(tk.Toplevel):
    def __init__(self, parent):
        super.__init__(parent)
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.title("Мои товары")
        self.grab_set()
        self.add_frames()

    def add_frames(self):
        pass

    def add_product(self):
        # получение данных из формы
        # добавление значений в базу
        pass
        # dbo.add_product(str(name_product_entry.get()), float(buy_price_product_entry.get()),
        #                 float(sale_price_product_entry.get()),
        #                 int(amount_product_entry.get()))
        # вывод сообщения об успешности
        # обновление формы

def open_base_products(parent):

    base_products = Base_products(parent)


    add_new_product_frame = ttk.Frame(base_products, height=300, width=500, borderwidth=5, relief=tk.SOLID, padding=[8,10])
    all_products_frame = ttk.Frame(base_products)

    add_new_product_frame.pack()
    all_products_frame.pack(expand=tk.YES, fill=tk.BOTH)

    add_new_product_label = tk.Label(add_new_product_frame, text = 'Добавить/изменить товар')
    id_product_label = tk.Label(add_new_product_frame, text = 'Код товара - ')
    name_product_label = tk.Label(add_new_product_frame, text='Наименование товара')
    buy_price_product_label = tk.Label(add_new_product_frame, text='Цена по закупке')
    sale_price_product_label = tk.Label(add_new_product_frame, text='Цена при продаже')
    amount_product_label = tk.Label(add_new_product_frame, text='Количество')

    name_product_entry = tk.Entry(add_new_product_frame, width = 100, justify=tk.LEFT)
    buy_price_product_entry = tk.Entry(add_new_product_frame, width = 100, justify=tk.LEFT)
    sale_price_product_entry = tk.Entry(add_new_product_frame, width = 100, justify=tk.LEFT)
    amount_product_entry = tk.Entry(add_new_product_frame, width = 100, justify=tk.LEFT)
    save_product_btn = tk.Button(add_new_product_frame, text='Сохранить', command=add_product)

    add_new_product_label.grid(row=0, column=0, columnspan=2, sticky='n', padx=10,pady=10)
    id_product_label.grid(row=1, column=0, sticky='w', padx=10,pady=10)
    name_product_label.grid(row=2, column=0, sticky='w', padx=10,pady=10)
    name_product_entry.grid(row=2, column=1, sticky='e', padx=10,pady=10)
    buy_price_product_label.grid(row=3, column=0, sticky='w', padx=10,pady=10)
    buy_price_product_entry.grid(row=3, column=1, sticky='e', padx=10,pady=10)
    sale_price_product_label.grid(row=4, column=0, sticky='w', padx=10,pady=10)
    sale_price_product_entry.grid(row=4, column=1, sticky='e', padx=10,pady=10)
    amount_product_label.grid(row=5, column=0, sticky='w', padx=10,pady=10)
    amount_product_entry.grid(row=5, column=1, sticky='e', padx=10,pady=10)
    save_product_btn.grid(row=6, column=0, columnspan=2, sticky='n', padx=10,pady=10)

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