import tkinter as tk
from tkinter import ttk


class SortableTreeview(ttk.Frame):
    """Treeview + Scrollbar. Чекбоксы, CTRL, сортировка, шапка-галочка."""

    def __init__(self, master=None, checkbox_column=False, **kwargs):
        super().__init__(master)
        self._sort_column = None
        self._sort_reverse = False
        self._checkbox_column = checkbox_column
        self._checked_items: set = set()

        self.tree = ttk.Treeview(self, **kwargs)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree["selectmode"] = "extended"

        if checkbox_column:
            self.tree.bind('<ButtonRelease-1>', self._on_click)
            self.tree.bind('<Control-ButtonRelease-1>', self._on_ctrl_click)
            self.tree.bind('<Double-1>', self._on_double_click)

    # ── Прокси ────────────────────────────────────────────
    def heading(self, column, **kwargs):
        return self.tree.heading(column, **kwargs)
    def column(self, column, **kwargs):
        return self.tree.column(column, **kwargs)
    def insert(self, parent, index, iid=None, **kwargs):
        if self._checkbox_column:
            values = kwargs.get('values', ())
            values = ('☐',) + tuple(values)
            kwargs['values'] = values
        return self.tree.insert(parent, index, iid=iid, **kwargs)
    def delete(self, *items):
        self.tree.delete(*items)
    def get_children(self, item=None):
        return self.tree.get_children(item)
    def item(self, item, option=None, **kwargs):
        return self.tree.item(item, option=option, **kwargs)
    def set(self, item, column=None, value=None):
        return self.tree.set(item, column, value)
    def selection(self):
        return self.tree.selection()
    def selection_set(self, items):
        self.tree.selection_set(items)
    def selection_remove(self, items):
        self.tree.selection_remove(items)
    def focus(self):
        return self.tree.focus()
    def move(self, item, parent, index):
        self.tree.move(item, parent, index)
    def identify(self, component, x, y):
        return self.tree.identify(component, x, y)
    def identify_row(self, y):
        return self.tree.identify_row(y)
    def identify_column(self, x):
        return self.tree.identify_column(x)
    def bbox(self, item, column=None):
        return self.tree.bbox(item, column)
    def index(self, item):
        return self.tree.index(item)
    def bind(self, sequence=None, func=None, add=None):
        return self.tree.bind(sequence, func, add)
    def tag_configure(self, tagName, **kwargs):
        return self.tree.tag_configure(tagName, **kwargs)

    # ── Сортировка ────────────────────────────────────────
    def setup_sorting(self):
        cols = self.tree["columns"]
        # Шапка чекбокса (первая колонка) — всегда получает command
        if self._checkbox_column and len(cols) > 0:
            first_col = cols[0]
            self.tree.heading(
                first_col,
                text=self.tree.heading(first_col, "text"),
                command=self._on_checkbox_header_click
            )
        # Остальные колонки — сортировка
        start = 1 if self._checkbox_column else 0
        for i in range(start, len(cols)):
            col = cols[i]
            self.tree.heading(
                col,
                text=self.tree.heading(col, "text"),
                command=lambda _col=col: self._on_heading_click(_col)
            )

    def _on_checkbox_header_click(self):
        if not self._checkbox_column:
            return
        children = self.tree.get_children('')
        if not children:
            return
        all_checked = all(iid in self._checked_items for iid in children)
        if all_checked:
            self.uncheck_all()
        else:
            self.check_all()

    def _on_heading_click(self, col):
        data = []
        for iid in self.tree.get_children(""):
            val = self.tree.set(iid, col)
            try:
                val_key = float(val.replace(',', '.').replace(' ', ''))
            except Exception:
                val_key = val.lower() if isinstance(val, str) else val
            data.append((val_key, iid))

        if self._sort_column == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = col
            self._sort_reverse = False

        data.sort(key=lambda x: x[0], reverse=self._sort_reverse)
        for index, (_, iid) in enumerate(data):
            self.tree.move(iid, '', index)

        for c in self.tree["columns"]:
            text = self.tree.heading(c, "text").replace(' ▲', '').replace(' ▼', '')
            if c == self._sort_column:
                arrow = "▲" if not self._sort_reverse else "▼"
                self.tree.heading(c, text=f"{text} {arrow}")
            else:
                self.tree.heading(c, text=text)

    # ── Чекбоксы ──────────────────────────────────────────
    def _on_click(self, event):
        if not self._checkbox_column:
            return
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = self.tree.identify_column(event.x)
        if int(column.replace('#', '')) != 1:
            return
        rowid = self.tree.identify_row(event.y)
        if not rowid:
            return
        self._toggle_check(rowid)

    def _on_ctrl_click(self, event):
        if not self._checkbox_column:
            return
        rowid = self.tree.identify_row(event.y)
        if not rowid:
            return
        self._toggle_check(rowid)

    def _on_double_click(self, event):
        if not self._checkbox_column:
            return
        rowid = self.tree.identify_row(event.y)
        if not rowid:
            return
        self._toggle_check(rowid)

    def _toggle_check(self, iid):
        values = list(self.tree.item(iid, 'values'))
        if iid in self._checked_items:
            self._checked_items.discard(iid)
            values[0] = '☐'
        else:
            self._checked_items.add(iid)
            values[0] = '☑'
        self.tree.item(iid, values=values)

    def get_checked_iids(self):
        return list(self._checked_items)

    def get_checked_values(self):
        return [tuple(list(self.tree.item(iid, 'values'))[1:])
                for iid in self._checked_items]

    def check_all(self):
        for iid in self.tree.get_children(''):
            if iid not in self._checked_items:
                self._checked_items.add(iid)
                vals = list(self.tree.item(iid, 'values'))
                vals[0] = '☑'
                self.tree.item(iid, values=vals)

    def uncheck_all(self):
        for iid in self.tree.get_children(''):
            if iid in self._checked_items:
                self._checked_items.discard(iid)
                vals = list(self.tree.item(iid, 'values'))
                vals[0] = '☐'
                self.tree.item(iid, values=vals)

    def clear_checks(self):
        self._checked_items.clear()


class SearchPanel(tk.Frame):
    def __init__(self, master, search_callback, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.search_callback = search_callback
        tk.Label(self, text="Поиск:").pack(side=tk.LEFT, padx=(5, 2), pady=2)
        self.entry = tk.Entry(self)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)
        self.entry.bind("<KeyRelease>", self._on_change)
        tk.Button(self, text="Очистить", command=self.clear).pack(side=tk.LEFT, padx=2, pady=2)

    def _on_change(self, event):
        self.search_callback(self.entry.get())

    def clear(self):
        self.entry.delete(0, tk.END)
        self.search_callback('')
