from tkinter import *
from tkinter import ttk

root = Tk()

root.title("GUI test")

label = ttk.Label(root, text = "test")
label.grid()

print(label['text'])

root.mainloop()