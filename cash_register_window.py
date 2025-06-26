import tkinter as tk
from tkinter import messagebox
from payment_window import PaymentWindow
from utils import SortableTreeview, SearchPanel


class CashRegisterWindow(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("Касса")
        self.geometry("1000x500")
        self.wm_iconbitmap("main_icon.ico")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.all_products = []  # здесь будем хранить все продукты для поиска и фильтрации
        self.cart = []

        # Основной контейнер для поиска и таблицы — чтобы связать их ширину и высоту
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Панель поиска в main_frame сверху, растягивается по ширине
        self.search_panel = SearchPanel(main_frame, self.on_search)
        self.search_panel.pack(fill=tk.X, padx=5, pady=5)

        # Таблица товаров под поиском, занимает всё остальное пространство
        self.products_tree = SortableTreeview(main_frame, columns=('code', 'name', 'price', 'amount'), show='headings')
        self.products_tree.heading('code', text='Код')
        self.products_tree.heading('name', text='Наименование')
        self.products_tree.heading('price', text='Цена продажи')
        self.products_tree.heading('amount', text='На складе')
        self.products_tree.column('code', width=50)
        self.products_tree.column('name', width=200)
        self.products_tree.column('price', width=80)
        self.products_tree.column('amount', width=80)
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        self.products_tree.setup_sorting()

        # Панель справа — корзина и управление
        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Корзина
        tk.Label(right_frame, text="Корзина").pack()
        self.cart_tree = SortableTreeview(right_frame, columns=('name', 'price', 'amount', 'sum'), show='headings')
        self.cart_tree.heading('name', text='Наименование')
        self.cart_tree.heading('price', text='Цена')
        self.cart_tree.heading('amount', text='Кол-во')
        self.cart_tree.heading('sum', text='Сумма')
        self.cart_tree.column('name', width=200)
        self.cart_tree.column('price', width=80)
        self.cart_tree.column('amount', width=80)
        self.cart_tree.column('sum', width=80)
        self.cart_tree.setup_sorting()
        self.cart_tree.bind('<Double-1>', self.on_cart_double_click)
        self.editing_entry = None
        self.cart_tree.pack(fill=tk.BOTH, expand=True)

        # Кол-во для добавления
        qty_frame = tk.Frame(right_frame)
        qty_frame.pack(pady=5)
        tk.Label(qty_frame, text="Количество:").pack(side=tk.LEFT)
        self.qty_var = tk.IntVar(value=1)
        self.qty_spinbox = tk.Spinbox(qty_frame, from_=1, to=100, textvariable=self.qty_var, width=5)
        self.qty_spinbox.pack(side=tk.LEFT)

        # Кнопки
        btn_add = tk.Button(right_frame, text="Добавить в корзину", command=self.add_to_cart)
        btn_add.pack(pady=5)

        btn_remove = tk.Button(right_frame, text="Удалить из корзины", command=self.remove_from_cart)
        btn_remove.pack(pady=5)

        btn_pay = tk.Button(right_frame, text="Оформить продажу", command=self.checkout)
        btn_pay.pack(pady=20)

        # Итог
        self.total_var = tk.StringVar(value="Итого: 0.00")
        tk.Label(right_frame, textvariable=self.total_var, font=("Arial", 14)).pack()
        self.refresh_products()

    def refresh_products(self):
        # Получаем все доступные продукты из БД
        self.all_products = self.db.get_available_products()
        # Обновляем таблицу полным списком
        self.update_tree(self.all_products)
        # Очищаем поле поиска при обновлении данных
        self.search_panel.clear()

    def update_tree(self, products):
        self.products_tree.delete(*self.products_tree.get_children())
        for p in products:
            # p[0] — ID, используем как iid
            self.products_tree.insert('', 'end', iid=str(p[0]), values=(p[1], p[2], p[4], p[5]))

    def on_search(self, query):
        query = query.lower()
        if not query:
            self.update_tree(self.all_products)
            return

        filtered = []
        for p in self.all_products:
            # Формируем кортеж только с отображаемыми полями
            fields = (str(p[1]), str(p[2]), str(p[4]), str(p[5]))
            if any(query in field.lower() for field in fields):
                filtered.append(p)

        self.update_tree(filtered)

    def add_to_cart(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для добавления.")
            return
        product_id = int(selected[0])  # iid — это ID товара
        product = self.db.get_product_by_id(product_id)
        if product is None:
            messagebox.showerror("Ошибка", "Товар не найден.")
            return
        qty = self.qty_var.get()
        if qty <= 0:
            messagebox.showwarning("Внимание", "Количество должно быть положительным.")
            return
        if qty > product[5]:
            messagebox.showwarning("Внимание", f"На складе недостаточно товара. Доступно: {product[5]}")
            return

        # Если товар уже в корзине, увеличить количество
        for idx, item in enumerate(self.cart):
            if item[0] == product_id:
                new_amount = item[3] + qty
                if new_amount > product[5]:
                    messagebox.showwarning("Внимание", f"На складе недостаточно товара. Доступно: {product[5]}")
                    return
                self.cart[idx] = (product_id, product[1], product[4], new_amount)
                break
        else:
            self.cart.append((product_id, product[1], product[4], qty))

        self.refresh_cart()

    def refresh_cart(self):
        for i in self.cart_tree.get_children():
            self.cart_tree.delete(i)
        total = 0
        for item in self.cart:
            sum_ = item[2] * item[3]
            total += sum_
            self.cart_tree.insert('', 'end', values=(item[1], f"{item[2]:.2f}", item[3], f"{sum_:.2f}"))
        self.total_var.set(f"Итого: {total:.2f}")

    def remove_from_cart(self):
        selected = self.cart_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар для удаления.")
            return
        item_idx = self.cart_tree.index(selected[0])
        del self.cart[item_idx]
        self.refresh_cart()

    def checkout(self):
        if not self.cart:
            messagebox.showwarning("Внимание", "Корзина пуста.")
            return

        # Окно оплаты
        pay_window = PaymentWindow(self, self.db, self.cart, self.refresh_products, self.clear_cart)
        pay_window.grab_set()

    def clear_cart(self):
        self.cart.clear()
        self.refresh_cart()

    def on_cart_double_click(self, event):
        # Определяем, по какой ячейке кликнули
        region = self.cart_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.cart_tree.identify_row(event.y)
        column = self.cart_tree.identify_column(event.x)

        # Колонка 'amount' у вас 3-я (начинается с #1)
        if column != '#3':
            return  # редактируем только колонку с количеством

        if not row_id:
            return

        # Координаты ячейки
        x, y, width, height = self.cart_tree.bbox(row_id, column)

        # Текущий текст в ячейке
        value = self.cart_tree.set(row_id, 'amount')

        # Создаем Entry поверх ячейки
        if self.editing_entry:
            self.editing_entry.destroy()

        self.editing_entry = tk.Entry(self.cart_tree, width=5)
        self.editing_entry.place(x=x, y=y, width=width, height=height)
        self.editing_entry.insert(0, value)
        self.editing_entry.focus()

        def save_edit(event=None):
            new_val = self.editing_entry.get()
            try:
                new_qty = int(new_val)
                if new_qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Внимание", "Количество должно быть положительным целым числом.")
                self.editing_entry.focus()
                return

            # Обновляем self.cart
            index = self.cart_tree.index(row_id)
            product_id, name, price, old_qty = self.cart[index]

            # Проверяем наличие на складе
            product = self.db.get_product_by_id(product_id)
            if not product:
                messagebox.showerror("Ошибка", "Товар не найден в базе.")
                self.editing_entry.destroy()
                self.editing_entry = None
                return

            if new_qty > product[5]:
                messagebox.showwarning("Внимание", f"На складе недостаточно товара. Доступно: {product[5]}")
                self.editing_entry.focus()
                return

            self.cart[index] = (product_id, name, price, new_qty)
            self.refresh_cart()
            self.editing_entry.destroy()
            self.editing_entry = None

        self.editing_entry.bind('<Return>', save_edit)
        self.editing_entry.bind('<FocusOut>', lambda e: self.editing_entry and self.editing_entry.destroy())

    def on_close(self):
        self.master.child_windows.remove(self)
        self.destroy()