from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollablePage(ttk.Frame):
    """A tab-sized scroll container that keeps its content usable on small screens."""

    def __init__(self, parent, *, horizontal: bool = False) -> None:
        super().__init__(parent)
        self.horizontal = horizontal
        background = ttk.Style(self).lookup("TFrame", "background") or "SystemButtonFace"
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, background=background)
        self.vertical_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vertical_scrollbar.set)
        self.vertical_scrollbar.pack(side="right", fill="y")
        if horizontal:
            self.horizontal_scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self.horizontal_scrollbar.set)
            self.horizontal_scrollbar.pack(side="bottom", fill="x")
        else:
            self.horizontal_scrollbar = None
        self.canvas.pack(side="left", fill="both", expand=True)

        self.body = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._sync_scroll_region)
        self.canvas.bind("<Configure>", self._resize_body)

    def _sync_scroll_region(self, _event=None) -> None:
        if self.horizontal:
            width = max(self.canvas.winfo_width(), self.body.winfo_reqwidth())
            self.canvas.itemconfigure(self._window, width=width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_body(self, event) -> None:
        width = max(event.width, self.body.winfo_reqwidth()) if self.horizontal else event.width
        self.canvas.itemconfigure(self._window, width=width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
