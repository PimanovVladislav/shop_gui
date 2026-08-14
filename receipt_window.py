import os
import sys
import subprocess
import tempfile
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False


class ReceiptWindow(tk.Toplevel):
    """Окно просмотра чека с кнопками Печать / Сохранить / Закрыть.

    Горячие клавиши:
      Пробел / Enter — закрыть
      Ctrl+S         — сохранить в PDF
      Ctrl+P         — печать
    """

    def __init__(self, master, check_id, date_str, receipt_text):
        super().__init__(master)
        self.check_id = check_id
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.receipt_text = receipt_text or ""

        self.title("Чек №{0}".format(check_id))
        self.geometry("500x620")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.grab_set()

        self.text = tk.Text(self, font=("Courier", 10), wrap='none',
                            state='disabled', width=64, height=26)
        self.text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._set_text(self.receipt_text)

        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.btn_print = tk.Button(btn_frame, text="Печать (Ctrl+P)",
                                   command=self.print_receipt)
        self.btn_print.pack(side=tk.LEFT, padx=5)

        self.btn_save = tk.Button(btn_frame, text="Сохранить (Ctrl+S)",
                                  command=self.save_pdf)
        self.btn_save.pack(side=tk.LEFT, padx=5)

        self.btn_close = tk.Button(btn_frame, text="Закрыть (Пробел/Enter)",
                                   command=self.on_close)
        self.btn_close.pack(side=tk.LEFT, padx=5)

        # Горячие клавиши (bind_all, т.к. фокус может быть на Text/кнопках)
        self.bind_all('<space>', self._on_close_key)
        self.bind_all('<Return>', self._on_close_key)
        self.bind_all('<Control-s>', self._on_save_key)
        self.bind_all('<Control-p>', self._on_print_key)

        self.after(50, self._focus)

    def _focus(self):
        try:
            self.focus_force()
            self.btn_close.focus_set()
        except Exception:
            pass
        try:
            self.lift()
        except Exception:
            pass

    def _set_text(self, text):
        self.text.config(state='normal')
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", text)
        self.text.config(state='disabled')

    # ── Горячие клавиши ────────────────────────────────────
    def _on_close_key(self, event):
        self.on_close()
        return 'break'

    def _on_save_key(self, event):
        self.save_pdf()
        return 'break'

    def _on_print_key(self, event):
        self.print_receipt()
        return 'break'

    # ── Сохранение в PDF ───────────────────────────────────
    def _build_filepath(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.isdir(desktop):
            desktop = os.path.expanduser("~")
        receipts_dir = os.path.join(desktop, "Чеки")

        date_folder = self.date_str[:10] if len(self.date_str) >= 10 else "unknown"
        target_dir = os.path.join(receipts_dir, date_folder)
        os.makedirs(target_dir, exist_ok=True)

        time_part = ""
        if len(self.date_str) >= 19:
            time_part = self.date_str[11:19].replace(':', '-')
        else:
            time_part = datetime.now().strftime("%H-%M-%S")

        filename = "Чек {0}_{1}.pdf".format(self.check_id, time_part)
        return os.path.join(target_dir, filename)

    @staticmethod
    def _find_font():
        candidates = [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\times.ttf",
            r"C:\Windows\Fonts\segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def _write_pdf(self, filepath):
        if not HAS_FPDF:
            messagebox.showerror(
                "Ошибка",
                "Не установлена библиотека fpdf2.\nУстановите её командой: pip install fpdf2",
                parent=self)
            return False
        try:
            pdf = FPDF()
            pdf.add_page()
            font_path = self._find_font()
            if font_path:
                pdf.add_font("receipt", "", font_path, uni=True)
                pdf.set_font("receipt", size=11)
            else:
                pdf.set_font("Helvetica", size=11)
            # Вычисляем реальную ширину с учетом полей страницы
            effective_page_width = pdf.w - pdf.l_margin - pdf.r_margin

            for line in self.receipt_text.split("\n"):
                # Сбрасываем X в начало строки на случай смещения
                pdf.set_x(pdf.l_margin)
                # Передаем рассчитанную ширину и режим переноса по символам
                pdf.multi_cell(effective_page_width, 6, line, wrapmode="CHAR")
            pdf.output(filepath)
            return True
        except Exception as e:
            messagebox.showerror("Ошибка",
                                 "Не удалось сохранить PDF:\n{0}".format(e),
                                 parent=self)
            return False

    def save_pdf(self):
        filepath = self._build_filepath()
        if self._write_pdf(filepath):
            messagebox.showinfo("Сохранение",
                                "Чек сохранён:\n{0}".format(filepath),
                                parent=self)

    def print_receipt(self):
        if not HAS_FPDF:
            messagebox.showerror(
                "Ошибка",
                "Не установлена библиотека fpdf2.\nУстановите её командой: pip install fpdf2",
                parent=self)
            return
        tmp = os.path.join(tempfile.gettempdir(),
                           "receipt_{0}.pdf".format(self.check_id))
        if not self._write_pdf(tmp):
            return
        try:
            if os.name == 'nt':
                os.startfile(tmp, "print")
            elif sys.platform == 'darwin':
                subprocess.run(["open", tmp])
            else:
                subprocess.run(["lp", tmp])
        except Exception as e:
            messagebox.showerror("Ошибка",
                                 "Не удалось отправить на печать:\n{0}".format(e),
                                 parent=self)

    def on_close(self):
        for seq in ('<space>', '<Return>', '<Control-s>', '<Control-p>'):
            try:
                self.unbind_all(seq)
            except Exception:
                pass
        self.destroy()
