import tkinter as tk
from tkinter import ttk


def bind_entry_shortcuts(widget):
    """Привязывает Ctrl+C/V/X/Z/Y/A к Entry/Spinbox с собственной историей undo/redo.

    ВАЖНО: tk.Entry и tk.Spinbox НЕ поддерживают опцию undo (в отличие от tk.Text),
    поэтому undo/redo реализованы вручную через стеки состояний.
    """
    state = {'last': widget.get()}
    undo_stack = []
    redo_stack = []

    def _record_change():
        current = widget.get()
        if current == state['last']:
            return
        undo_stack.append(state['last'])
        if len(undo_stack) > 200:
            undo_stack.pop(0)
        redo_stack.clear()
        state['last'] = current

    def _copy(event):
        try:
            sel = widget.selection_get()
        except Exception:
            return 'break'
        widget.clipboard_clear()
        widget.clipboard_append(sel)
        return 'break'

    def _cut(event):
        try:
            sel = widget.selection_get()
        except Exception:
            return 'break'
        widget.clipboard_clear()
        widget.clipboard_append(sel)
        try:
            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception:
            pass
        _record_change()
        return 'break'

    def _paste(event):
        try:
            text = widget.clipboard_get()
        except Exception:
            return 'break'
        try:
            if widget.selection_present():
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception:
            pass
        widget.insert(tk.INSERT, text)
        _record_change()
        return 'break'

    def _undo(event):
        if not undo_stack:
            return 'break'
        redo_stack.append(widget.get())
        prev = undo_stack.pop()
        widget.delete(0, tk.END)
        widget.insert(0, prev)
        state['last'] = prev
        return 'break'

    def _redo(event):
        if not redo_stack:
            return 'break'
        undo_stack.append(widget.get())
        nxt = redo_stack.pop()
        widget.delete(0, tk.END)
        widget.insert(0, nxt)
        state['last'] = nxt
        return 'break'

    def _select_all(event):
        try:
            widget.select_range(0, tk.END)
        except Exception:
            try:
                widget.selection_range(0, tk.END)
            except Exception:
                pass
        try:
            widget.icursor(tk.END)
        except Exception:
            pass
        return 'break'

    def _on_keyrelease(event):
        _record_change()

    widget.bind('<KeyRelease>', _on_keyrelease, add='+')
    widget.bind('<Control-c>', _copy, add='+')
    widget.bind('<Control-v>', _paste, add='+')
    widget.bind('<Control-x>', _cut, add='+')
    widget.bind('<Control-z>', _undo, add='+')
    widget.bind('<Control-y>', _redo, add='+')
    widget.bind('<Control-Shift-Z>', _redo, add='+')
    widget.bind('<Control-a>', _select_all, add='+')


class SortableTreeview(ttk.Frame):
    """Treeview + Scrollbar.

    Возможности:
      - сортировка по клику на заголовок
      - чекбоксы (колонка ☐/☑) + клик по шапке = выбрать всё/снять всё
      - CTRL-клик и двойной клик для чекбоксов
      - горячие клавиши Ctrl+C/X/V/Z/A
      - подсветка активной ячейки жёлтым, Ctrl+C копирует текст именно этой ячейки
    """

    def __init__(self, master=None, checkbox_column=False, **kwargs):
        super().__init__(master)
        self._sort_column = None
        self._sort_reverse = False
        self._checkbox_column = checkbox_column
        self._checked_items = set()
        self._undo_stack = []

        # Активная ячейка (для жёлтой подсветки и Ctrl+C ячейки)
        self._active_cell = None       # (iid, col_name)
        self._active_cell_text = ''
        self._cell_pos = (0, 0)

        self.tree = ttk.Treeview(self, **kwargs)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree["selectmode"] = "extended"

        # Оверлей для жёлтой подсветки активной ячейки
        self._cell_highlight = tk.Label(
            self, bg='#ffe08a', fg='#000000',
            bd=0, relief='flat', highlightthickness=0, takefocus=0
        )
        try:
            style = ttk.Style(self)
            tree_font = style.lookup('Treeview', 'font')
            if tree_font:
                self._cell_highlight.config(font=tree_font)
        except Exception:
            pass
        self._cell_highlight.place_forget()
        self._cell_highlight.bind('<Button-1>', self._label_click)
        self._cell_highlight.bind('<Double-1>', self._label_click)
        self._cell_highlight.bind('<MouseWheel>', self._label_scroll)

        # Отслеживание клика по ячейке (всегда)
        self.tree.bind('<ButtonRelease-1>', self._on_cell_click, add='+')
        self.tree.bind('<MouseWheel>', self._on_scroll_hide, add='+')
        self.tree.bind('<Button-4>', self._on_scroll_hide, add='+')
        self.tree.bind('<Button-5>', self._on_scroll_hide, add='+')

        if checkbox_column:
            self.tree.bind('<ButtonRelease-1>', self._on_click, add='+')
            self.tree.bind('<Control-ButtonRelease-1>', self._on_ctrl_click, add='+')
            self.tree.bind('<Double-1>', self._on_double_click, add='+')

        self.tree.bind('<Control-c>', self._copy_selection)
        self.tree.bind('<Control-x>', self._cut_selection)
        self.tree.bind('<Control-v>', self._paste_selection)
        self.tree.bind('<Control-z>', self._undo)
        self.tree.bind('<Control-a>', self._select_all_rows)

    # ── Прокси-методы ──────────────────────────────────────
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
        self._hide_cell_highlight()
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
    def exists(self, item):
        return self.tree.exists(item)

    # ── Активная ячейка (жёлтая подсветка) ─────────────────
    def _on_cell_click(self, event):
        """Запоминает нажатую ячейку и подсвечивает её жёлтым."""
        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            self._hide_cell_highlight()
            return
        iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not iid or not col_id:
            self._hide_cell_highlight()
            return
        col_idx = int(col_id.replace('#', '')) - 1
        cols = self.tree['columns']
        if col_idx < 0 or col_idx >= len(cols):
            self._hide_cell_highlight()
            return
        if self._checkbox_column and col_idx == 0:
            self._hide_cell_highlight()
            return
        col_name = cols[col_idx]
        text = self.tree.set(iid, col_name)
        self._active_cell = (iid, col_name)
        self._active_cell_text = text
        self._show_cell_highlight(iid, col_id, col_name, text)

    def _show_cell_highlight(self, iid, col_id, col_name, text):
        try:
            x, y, w, h = self.tree.bbox(iid, col_id)
        except Exception:
            return
        self._cell_pos = (x, y)
        anchor = self.tree.column(col_name, 'anchor')
        if anchor not in ('w', 'center', 'e'):
            anchor = 'w'
        self._cell_highlight.config(text=text, anchor=anchor)
        self._cell_highlight.place(x=x, y=y, width=w, height=h)
        self._cell_highlight.lift()

    def _hide_cell_highlight(self):
        self._cell_highlight.place_forget()
        self._active_cell = None
        self._active_cell_text = ''

    def _label_click(self, event):
        cx, cy = self._cell_pos
        self._cell_highlight.place_forget()
        self._active_cell = None
        self._active_cell_text = ''
        self.tree.event_generate('<Button-1>', x=cx + event.x, y=cy + event.y)

    def _label_scroll(self, event):
        self._hide_cell_highlight()

    def _on_scroll_hide(self, event):
        self._hide_cell_highlight()

    # ── Горячие клавиши таблицы ────────────────────────────
    def _copy_selection(self, event=None):
        """Ctrl+C: если есть активная ячейка — копирует её текст,
        иначе — выделенные строки (через табуляцию)."""
        if self._active_cell is not None:
            self.tree.clipboard_clear()
            self.tree.clipboard_append(self._active_cell_text)
            return 'break'
        sel = self.tree.selection()
        if not sel:
            return 'break'
        lines = []
        for iid in sel:
            vals = self.tree.item(iid, 'values')
            if self._checkbox_column and vals:
                vals = vals[1:]
            lines.append('\t'.join(str(v) for v in vals))
        self.tree.clipboard_clear()
        self.tree.clipboard_append('\n'.join(lines))
        return 'break'

    def _cut_selection(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return 'break'
        entries = []
        lines = []
        for iid in sel:
            vals = self.tree.item(iid, 'values')
            idx = self.tree.index(iid)
            entries.append((iid, idx, vals))
            if self._checkbox_column and vals:
                lines.append('\t'.join(str(v) for v in vals[1:]))
            else:
                lines.append('\t'.join(str(v) for v in vals))
        self.tree.clipboard_clear()
        self.tree.clipboard_append('\n'.join(lines))
        for iid in sel:
            self.tree.delete(iid)
            self._checked_items.discard(iid)
        self._undo_stack.append(('cut', entries))
        return 'break'

    def _paste_selection(self, event=None):
        try:
            text = self.tree.clipboard_get()
        except Exception:
            return 'break'
        lines = [l for l in text.split('\n') if l.strip() != '']
        if not lines:
            return 'break'
        added = []
        for line in lines:
            vals = list(line.split('\t'))
            if self._checkbox_column:
                vals = ['☐'] + vals
            iid = self.tree.insert('', 'end', values=tuple(vals))
            added.append(iid)
        self._undo_stack.append(('paste', added))
        return 'break'

    def _undo(self, event=None):
        if not self._undo_stack:
            return 'break'
        action, data = self._undo_stack.pop()
        if action == 'cut':
            for iid, idx, vals in data:
                self.tree.insert('', idx, iid=iid, values=vals)
                if self._checkbox_column and vals and vals[0] == '☑':
                    self._checked_items.add(iid)
        elif action == 'paste':
            for iid in data:
                if self.tree.exists(iid):
                    self.tree.delete(iid)
                    self._checked_items.discard(iid)
        return 'break'

    def _select_all_rows(self, event=None):
        self.tree.selection_set(self.tree.get_children(''))
        return 'break'

    # ── Сортировка ─────────────────────────────────────────
    def setup_sorting(self):
        cols = self.tree["columns"]
        if self._checkbox_column and len(cols) > 0:
            first_col = cols[0]
            self.tree.heading(
                first_col,
                text=self.tree.heading(first_col, "text"),
                command=self._on_checkbox_header_click
            )
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
        self._hide_cell_highlight()
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

    # ── Чекбоксы ───────────────────────────────────────────
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
        bind_entry_shortcuts(self.entry)
        tk.Button(self, text="Очистить", command=self.clear).pack(side=tk.LEFT, padx=2, pady=2)

    def _on_change(self, event):
        self.search_callback(self.entry.get())

    def clear(self):
        self.entry.delete(0, tk.END)
        self.search_callback('')
