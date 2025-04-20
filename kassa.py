import tkinter as tk
from tkinter import ttk, Toplevel
import database_operation as dbo

def open_kassa():
    kassa = Toplevel()
    kassa.geometry('400x400')
    kassa.title("Касса")
    kassa.grab_set()