import tkinter as tk
from tkinter import ttk, Toplevel
import database_operation as dbo

def open_analisys():
    analisys = Toplevel()
    analisys.geometry('500x500')
    analisys.title("Анализ")
    analisys.grab_set()
