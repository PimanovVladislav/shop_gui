import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, date

DATE_FMT = "%d.%m.%Y"
DATETIME_FMT = "%d.%m.%Y %H:%M:%S"
DATETIME_SHORT_FMT = "%d.%m.%Y %H:%M"
DATE_PATTERN = "dd.mm.yyyy"


def parse_date(value):
    """Разбор даты из строки (ДД.ММ.ГГГГ или ГГГГ-ММ-ДД) или date/datetime."""
    if value is None or value == '' or value == '—':
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = str(value).strip()
    for fmt in (DATE_FMT, "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def parse_datetime(value):
    """Разбор даты-времени из строки или datetime."""
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    for fmt in (DATETIME_FMT, DATETIME_SHORT_FMT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            length = 19 if '%S' in fmt else 16
            return datetime.strptime(s[:length], fmt)
        except ValueError:
            continue
    d = parse_date(s)
    return datetime.combine(d, datetime.min.time()) if d else None


def format_date(value):
    """Форматирование даты для отображения: ДД.ММ.ГГГГ."""
    if value is None or value == '' or value == '—':
        return '—'
    if isinstance(value, datetime):
        return value.strftime(DATE_FMT)
    if isinstance(value, date):
        return value.strftime(DATE_FMT)
    d = parse_date(value)
    return d.strftime(DATE_FMT) if d else str(value)


def format_datetime(value, with_seconds=True):
    """Форматирование даты-времени для отображения."""
    if value is None or value == '':
        return ''
    fmt = DATETIME_FMT if with_seconds else DATETIME_SHORT_FMT
    if isinstance(value, datetime):
        return value.strftime(fmt)
    dt = parse_datetime(value)
    return dt.strftime(fmt) if dt else str(value)


def today_str():
    return datetime.today().strftime(DATE_FMT)

_SHORTCUT_KEYCODE = {
    67: 'copy', 86: 'paste', 88: 'cut', 90: 'undo', 89: 'redo',
    65: 'select_all', 83: 'save', 80: 'print', 70: 'find',
}

# keysym зависит от раскладки, поэтому перечисляем И английские, И русские значения.
_SHORTCUT_KEYSYM = {
    # английская раскладка
    'c': 'copy', 'v': 'paste', 'x': 'cut', 'z': 'undo', 'y': 'redo',
    'a': 'select_all', 's': 'save', 'p': 'print', 'f': 'find',
    # русская раскладка (физические клавиши C/V/X/Z/Y/A/S/P/F)
    'cyrillic_es': 'copy', 'cyrillic_em': 'paste', 'cyrillic_che': 'cut',
    'cyrillic_ya': 'undo', 'cyrillic_en': 'redo', 'cyrillic_ef': 'select_all',
    'cyrillic_yeru': 'save', 'cyrillic_ze': 'print', 'cyrillic_de': 'find',
}


def detect_shortcut(event):
    """Определяет действие по событию клавиши.

    Сначала по keysym (зависит от раскладки, но мы перечислили оба варианта),
    затем по keycode (физическая клавиша) как запасной вариант.
    """
    ks = (event.keysym or '').lower()
    action = _SHORTCUT_KEYSYM.get(ks)
    if action:
        return action
    return _SHORTCUT_KEYCODE.get(event.keycode)


def bind_ctrl_shortcuts(widget, handlers, use_bind_all=False):
    """Привязка Ctrl-сочетаний по keycode (работает в любой раскладке).

    handlers: словарь {action: callback(event)}; callback может вернуть 'break'.
    """
    def _on_ctrl(event):
        action = detect_shortcut(event)
        if action not in handlers:
            return None
        result = handlers[action](event)
        return result if result is not None else 'break'

    bind_fn = widget.bind_all if use_bind_all else widget.bind
    bind_fn('<Control-KeyPress>', _on_ctrl, add='+')
    return _on_ctrl


def bind_entry_shortcuts(widget):
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

    def _do_undo():
        if not undo_stack:
            return
        redo_stack.append(widget.get())
        prev = undo_stack.pop()
        widget.delete(0, tk.END)
        widget.insert(0, prev)
        state['last'] = prev

    def _do_redo():
        if not redo_stack:
            return
        undo_stack.append(widget.get())
        nxt = redo_stack.pop()
        widget.delete(0, tk.END)
        widget.insert(0, nxt)
        state['last'] = nxt

    def _on_ctrl(event):
        action = detect_shortcut(event)
        try:
            if action == 'copy':
                sel = widget.selection_get()
                widget.clipboard_clear()
                widget.clipboard_append(sel)
            elif action == 'cut':
                sel = widget.selection_get()
                widget.clipboard_clear()
                widget.clipboard_append(sel)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                _record_change()
            elif action == 'paste':
                text = widget.clipboard_get()
                if widget.selection_present():
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                widget.insert(tk.INSERT, text)
                _record_change()
            elif action == 'undo':
                _do_undo()
            elif action == 'redo':
                _do_redo()
            elif action == 'select_all':
                widget.select_range(0, tk.END)
                widget.icursor(tk.END)
            else:
                return None
        except Exception:
            return None
        return 'break'

    def _on_keyrelease(event):
        _record_change()

    widget.bind('<KeyRelease>', _on_keyrelease, add='+')
    widget.bind('<Control-KeyPress>', _on_ctrl, add='+')


def center_window(window):
    """Разместить окно по центру экрана."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"+{x}+{y}")


def filter_with_checked(all_items, checked_keys, filter_func, key_func):
    """Отмеченные элементы всегда вверху, остальные — по фильтру."""
    checked = [item for item in all_items if key_func(item) in checked_keys]
    filtered = [item for item in all_items
                if key_func(item) not in checked_keys and filter_func(item)]
    return checked + filtered


class SortableTreeview(ttk.Frame):
    def __init__(self, master=None, checkbox_column=False, double_click_check=True,
                 search_change_callback=None, **kwargs):
        super().__init__(master)
        self._sort_column = None
        self._sort_reverse = False
        self._checkbox_column = checkbox_column
        self._double_click_check = double_click_check
        self._checked_items = set()
        self._undo_stack = []
        self._active_iid = None
        self._active_cell = None
        self._active_cell_text = ''
        self._cell_pos = (0, 0)
        self._last_press = None
        self._skip_release = False
        self._double_click_callback = None
        self._search_column = None
        self._search_change_callback = search_change_callback
        self._heading_base = {}
        self._row_order = []
        self._hover_iid = None
        self._active_row_iid = None
        self._batch_mode = False

        style = ttk.Style(master)
        self._style_name = 'Sortable.Treeview'
        try:
            style.configure(self._style_name, background='white', fieldbackground='white')
            # Не перекрашиваем selected — цвет строк задаётся тегами (hover/active/checked)
            style.map(self._style_name, foreground=[('selected', 'black')])
        except Exception:
            self._style_name = None

        self.tree = ttk.Treeview(self, style=self._style_name, **kwargs)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.vsb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.vsb.set)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree["selectmode"] = "extended"

        # Оверлей жёлтой подсветки кликнутой ячейки
        self._cell_highlight = tk.Label(
            self, bg='#ffe08a', fg='#000000',
            bd=0, relief='flat', highlightthickness=0, takefocus=0)
        self._cell_highlight.place_forget()
        self._cell_highlight.bind('<ButtonPress-1>', self._overlay_press)
        self._cell_highlight.bind('<ButtonRelease-1>', self._overlay_release)
        self._cell_highlight.bind('<MouseWheel>', self._overlay_wheel)

        self.tree.bind('<ButtonPress-1>', self._on_press, add='+')
        self.tree.bind('<ButtonRelease-1>', self._on_release, add='+')
        self.tree.bind('<Button-3>', self._on_right_click, add='+')
        self.tree.bind('<MouseWheel>', self._on_wheel, add='+')
        self.tree.bind('<Button-4>', self._on_wheel, add='+')
        self.tree.bind('<Button-5>', self._on_wheel, add='+')
        self.tree.bind('<Escape>', self._on_escape)

        # Единственный обработчик Ctrl-сочетаний (работает в любой раскладке)
        self.tree.bind('<Control-KeyPress>', self._on_ctrl_key)

        self.tree.tag_configure('hover_row', background='#f2f2f2')
        self.tree.tag_configure('active_row', background='#fffce0')
        self.tree.tag_configure('checked_row', background='#d4e8ff')
        self.tree.bind('<Motion>', self._on_motion, add='+')
        self.tree.bind('<Leave>', self._on_leave, add='+')
        self.bind('<Leave>', self._on_leave)

    def _flush_row_visual(self):
        if self._batch_mode:
            return
        try:
            self.tree.update_idletasks()
        except Exception:
            pass

    def begin_batch(self):
        self._batch_mode = True

    def end_batch(self):
        self._batch_mode = False
        self._flush_row_visual()

    def load_rows(self, rows, iid_fn=None, values_fn=None, clear=True,
                  restore_checked=True):
        """Пакетная загрузка строк без перерисовки после каждой вставки."""
        if iid_fn is None:
            iid_fn = lambda row: str(row[0])
        if values_fn is None:
            values_fn = lambda row: row[1] if isinstance(row, (tuple, list)) and len(row) == 2 else row

        self.begin_batch()
        try:
            if clear:
                children = self.tree.get_children('')
                if children:
                    self.delete(*children)
            for row in rows:
                iid = iid_fn(row)
                values = values_fn(row)
                self.insert('', 'end', iid=iid, values=values)
            if restore_checked and self._checkbox_column:
                self.restore_checks()
                self.move_checked_to_top()
        finally:
            self.end_batch()

    def _update_row_tags(self, iid):
        if not iid or not self.tree.exists(iid):
            return
        tags = []
        if iid in self._checked_items:
            tags.append('checked_row')
        elif iid == self._active_row_iid:
            tags.append('active_row')
        elif iid == self._hover_iid:
            tags.append('hover_row')
        self.tree.item(iid, tags=tuple(tags))
        if tags and iid in self.tree.selection():
            self.tree.selection_remove(iid)
        self._flush_row_visual()

    def _refresh_all_row_tags(self):
        for iid in self.tree.get_children(''):
            self._update_row_tags(iid)

    def _set_hover_iid(self, iid):
        old = self._hover_iid
        self._hover_iid = iid or None
        if old and old != self._hover_iid:
            self._update_row_tags(old)
        if self._hover_iid:
            self._update_row_tags(self._hover_iid)

    def _set_active_row_iid(self, iid):
        old = self._active_row_iid
        self._active_row_iid = iid or None
        if old and old != self._active_row_iid:
            self._update_row_tags(old)
        if self._active_row_iid:
            self._update_row_tags(self._active_row_iid)
        elif old:
            self._update_row_tags(old)

    def _on_motion(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region not in ('cell', 'tree'):
            self._set_hover_iid(None)
            return
        iid = self.tree.identify_row(event.y)
        self._set_hover_iid(iid if iid else None)

    def _on_leave(self, event=None):
        self._set_hover_iid(None)

    # ── Прокси ─────────────────────────────────────────────
    def heading(self, column, **kwargs):
        return self.tree.heading(column, **kwargs)
    def column(self, column, **kwargs):
        return self.tree.column(column, **kwargs)
    def get_columns(self):
        return self.tree['columns']
    def insert(self, parent, index, iid=None, **kwargs):
        values = kwargs.get('values', ())
        if self._checkbox_column:
            if iid in self._checked_items:
                values = ('\u2611',) + tuple(values)
            else:
                values = ('\u2610',) + tuple(values)
            kwargs['values'] = values
        new_iid = self.tree.insert(parent, index, iid=iid, **kwargs)
        self._row_order.append(new_iid)
        self._update_row_tags(new_iid)
        return new_iid
    def delete(self, *items):
        self._hide_cell_highlight()
        for it in items:
            if it in self._row_order:
                self._row_order.remove(it)
            if it == self._active_iid:
                self._active_iid = None
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
        if sequence == '<Double-1>':
            self._double_click_callback = func
            return func
        return self.tree.bind(sequence, func, add)
    def tag_configure(self, tagName, **kwargs):
        return self.tree.tag_configure(tagName, **kwargs)
    def exists(self, item):
        return self.tree.exists(item)

    def see(self, item):
        return self.tree.see(item)

    def move_checked_to_top(self):
        checked = [iid for iid in self.tree.get_children('')
                   if iid in self._checked_items]
        for index, iid in enumerate(checked):
            self.tree.move(iid, '', index)

    def restore_checks(self):
        if self._batch_mode:
            for iid in self._checked_items:
                if self.tree.exists(iid):
                    vals = list(self.tree.item(iid, 'values'))
                    if vals and self._checkbox_column:
                        vals[0] = '\u2611'
                        self.tree.item(iid, values=vals)
                    tags = ['checked_row'] if iid in self._checked_items else []
                    if tags:
                        self.tree.item(iid, tags=tuple(tags))
            return
        for iid in self._checked_items:
            if self.tree.exists(iid):
                vals = list(self.tree.item(iid, 'values'))
                if vals and self._checkbox_column:
                    vals[0] = '\u2611'
                    self.tree.item(iid, values=vals)
                self._update_row_tags(iid)

    # ── Клики ──────────────────────────────────────────────
    def _on_press(self, event):
        region = self.tree.identify('region', event.x, event.y)
        if region == 'heading':
            return
        iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        col_idx = int(col_id.replace('#', '')) - 1 if col_id else -1

        if iid:
            if iid in self.tree.selection():
                self.tree.selection_remove(iid)
            self._set_active_row_iid(iid)
            if region == 'cell' and col_id:
                if not (self._checkbox_column and col_idx == 0):
                    cols = self.tree['columns']
                    if 0 <= col_idx < len(cols):
                        col_name = cols[col_idx]
                        text = self.tree.set(iid, col_name)
                        self._active_iid = iid
                        self._active_cell = (iid, col_name)
                        self._active_cell_text = text
                        self._show_cell_highlight(iid, col_id, col_name, text)
        now = time.time()
        if self._last_press is not None:
            last_time, last_iid, last_col = self._last_press
            if (now - last_time < 0.5 and iid and iid == last_iid and col_id == last_col):
                self._last_press = None
                self._fire_double_click(event)
                return
        self._last_press = (now, iid, col_id)

    def _fire_double_click(self, event):
        self._hide_cell_highlight()
        self._skip_release = True
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        handled = False
        if self._double_click_callback is not None:
            result = self._double_click_callback(event)
            handled = result is not False
        if not handled and self._double_click_check and self._checkbox_column:
            self._toggle_check(iid)

    def _on_release(self, event):
        if self._skip_release:
            self._skip_release = False
            return
        region = self.tree.identify('region', event.x, event.y)
        if region != 'cell':
            self._hide_cell_highlight()
            self._set_active_row_iid(None)
            return
        iid = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)
        if not iid or not col_id:
            self._hide_cell_highlight()
            self._set_active_row_iid(None)
            return
        col_idx = int(col_id.replace('#', '')) - 1
        if self._checkbox_column and col_idx == 0:
            self._toggle_check(iid)
            self._set_active_row_iid(iid)
            self._hide_cell_highlight()
            return
        cols = self.tree['columns']
        if col_idx < 0 or col_idx >= len(cols):
            self._hide_cell_highlight()
            return
        col_name = cols[col_idx]
        text = self.tree.set(iid, col_name)
        self._active_iid = iid
        self._active_cell = (iid, col_name)
        self._active_cell_text = text
        self._show_cell_highlight(iid, col_id, col_name, text)

    def _on_right_click(self, event):
        """ПКМ по шапке — сортировка по возрастанию/убыванию/отключить."""
        if self.tree.identify('region', event.x, event.y) != 'heading':
            return
        col_id = self.tree.identify_column(event.x)
        if not col_id:
            return
        idx = int(col_id.replace('#', '')) - 1
        cols = self.tree['columns']
        if idx < 0 or idx >= len(cols):
            return
        col = cols[idx]
        if self._checkbox_column and idx == 0:
            return
        self._cycle_sort(col)

    def _on_wheel(self, event):
        self._hide_cell_highlight()

    # ── Горячие клавиши таблицы ────────────────────────────
    def _on_ctrl_key(self, event):
        action = detect_shortcut(event)
        if action == 'copy':
            return self._copy()
        elif action == 'cut':
            return self._cut()
        elif action == 'paste':
            return self._paste()
        elif action == 'undo':
            return self._undo()
        elif action == 'select_all':
            return self._select_all()
        return None

    def _copy(self, event=None):
        if self._active_cell_text:
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

    def _cut(self, event=None):
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

    def _paste(self, event=None):
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
                vals = ['\u2610'] + vals
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
                if self._checkbox_column and vals and vals[0] == '\u2611':
                    self._checked_items.add(iid)
        elif action == 'paste':
            for iid in data:
                if self.tree.exists(iid):
                    self.tree.delete(iid)
                    self._checked_items.discard(iid)
        return 'break'

    def _select_all(self, event=None):
        self.tree.selection_set(self.tree.get_children(''))
        return 'break'

    # ── Оверлей ячейки ─────────────────────────────────────
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

    def hide_cell_highlight(self):
        self._hide_cell_highlight()

    def _forward(self, sequence, event):
        cx, cy = self._cell_pos
        try:
            self.tree.event_generate(sequence, x=cx + event.x, y=cy + event.y)
        except Exception:
            pass

    def _overlay_press(self, event):
        self._forward('<ButtonPress-1>', event)

    def _overlay_release(self, event):
        self._forward('<ButtonRelease-1>', event)

    def _overlay_wheel(self, event):
        self._hide_cell_highlight()
        try:
            self.tree.event_generate('<MouseWheel>', delta=event.delta)
        except Exception:
            pass

    # ── Шапка ──────────────────────────────────────────────
    def setup_sorting(self):
        cols = self.tree['columns']
        for i, col in enumerate(cols):
            base = self.tree.heading(col, 'text')
            self._heading_base[col] = base
            if self._checkbox_column and i == 0:
                self.tree.heading(col, text=base, command=self._on_checkbox_header_click)
            else:
                self.tree.heading(col, text=base,
                                  command=lambda c=col: self._toggle_search_column(c))

    def _toggle_search_column(self, col):
        if self._search_column == col:
            self._search_column = None
        else:
            self._search_column = col
        self._refresh_all_headings()
        if self._search_change_callback is not None:
            self._search_change_callback()

    def _cycle_sort(self, col):
        if self._sort_column == col:
            if not self._sort_reverse:
                self._sort_reverse = True
            else:
                self._sort_column = None
                self._sort_reverse = False
        else:
            self._sort_column = col
            self._sort_reverse = False
        if self._sort_column is None:
            self._reset_order()
        else:
            self._apply_sort()
        self._refresh_all_headings()

    def _apply_sort(self):
        if self._sort_column is None:
            return
        data = []
        for iid in self.tree.get_children(''):
            val = self.tree.set(iid, self._sort_column)
            try:
                key = float(val.replace(',', '.').replace(' ', ''))
            except Exception:
                key = val.lower() if isinstance(val, str) else val
            data.append((key, iid))
        data.sort(key=lambda x: x[0], reverse=self._sort_reverse)
        for index, (_, iid) in enumerate(data):
            self.tree.move(iid, '', index)
        self.move_checked_to_top()

    def _reset_order(self):
        order = [iid for iid in self._row_order if self.tree.exists(iid)]
        for index, iid in enumerate(order):
            self.tree.move(iid, '', index)

    def reset_sort(self):
        self._sort_column = None
        self._sort_reverse = False
        self._reset_order()
        self._refresh_all_headings()

    def _on_escape(self, event):
        self.reset_sort()
        return 'break'

    def _refresh_all_headings(self):
        for col in self._heading_base:
            base = self._heading_base[col]
            text = base
            if col == self._search_column:
                text = '\U0001F50D ' + text
            if col == self._sort_column:
                arrow = ' \u25B2' if not self._sort_reverse else ' \u25BC'
                text = text + arrow
            self.tree.heading(col, text=text)

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

    # ── Чекбоксы ───────────────────────────────────────────
    def _toggle_check(self, iid):
        if iid in self._checked_items:
            self._checked_items.discard(iid)
        else:
            self._checked_items.add(iid)
        values = list(self.tree.item(iid, 'values'))
        if values:
            values[0] = '\u2611' if iid in self._checked_items else '\u2610'
            self.tree.item(iid, values=values)
        self._update_row_tags(iid)
        self.move_checked_to_top()

    def uncheck(self, iid):
        self._checked_items.discard(iid)
        self._update_row_tags(iid)

    def get_checked_iids(self):
        return list(self._checked_items)

    def get_checked_values(self):
        result = []
        for iid in self._checked_items:
            if self.tree.exists(iid):
                vals = list(self.tree.item(iid, 'values'))
                result.append(tuple(vals[1:]) if vals else ())
        return result

    def check_all(self):
        for iid in self.tree.get_children(''):
            if iid not in self._checked_items:
                self._checked_items.add(iid)
                values = list(self.tree.item(iid, 'values'))
                if values:
                    values[0] = '\u2611'
                    self.tree.item(iid, values=values)
                self._update_row_tags(iid)
        self._flush_row_visual()

    def uncheck_all(self):
        for iid in self.tree.get_children(''):
            if iid in self._checked_items:
                self._checked_items.discard(iid)
                values = list(self.tree.item(iid, 'values'))
                if values:
                    values[0] = '\u2610'
                    self.tree.item(iid, values=values)
                self._update_row_tags(iid)
        self._flush_row_visual()

    def clear_checks(self):
        checked = list(self._checked_items)
        self._checked_items.clear()
        for iid in checked:
            if self.tree.exists(iid):
                self._update_row_tags(iid)

    # ── Активная строка ────────────────────────────────────
    def get_active_iid(self):
        return self._active_iid

    def set_active(self, iid):
        self._active_iid = iid
        self._set_active_row_iid(iid)

    def get_focused_row_iid(self):
        """Строка с фокусом: tree.focus() или последняя активная (клик)."""
        iid = self.tree.focus()
        if iid and self.tree.exists(iid):
            return iid
        if self._active_row_iid and self.tree.exists(self._active_row_iid):
            return self._active_row_iid
        return None

    def clear_active(self):
        self._active_iid = None
        self._set_active_row_iid(None)

    # ── Поиск по колонке ───────────────────────────────────
    def get_search_column(self):
        return self._search_column


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

    def focus_search(self, event=None):
        self.entry.focus_set()
        self.entry.select_range(0, tk.END)
        return 'break'

    def bind_shortcuts(self, widget):
        bind_ctrl_shortcuts(widget, {'find': lambda e: self.focus_search()})
