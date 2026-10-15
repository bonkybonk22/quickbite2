import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
import database as db

# --- Design Tokens & Color Palette ---
NAVY = "#0f172a"
ORANGE = "#ea7a2b"
GOLD = "#f6bf5f"
BG = "#f3f4f6"
CARD_BG = "#ffffff"
TEXT_DARK = "#1e293b"
TEXT_MUTED = "#64748b"

STATUS_COLORS = {
    "Available": "#2e9e5b", 
    "Low Stock": "#d62828", 
    "Out of Stock": "#7f1d1d",
    "Normal": "#444444", 
    "High": "#2e9e5b"
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuickBite - Canteen Ordering System")
        self.geometry("1280x760")
        self.minsize(1100, 700)
        self.configure(bg=NAVY)
        
        self.setup_styles()
        db.init_db()
        self.cart = {}
        self.last_order = None
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        
        # Dictionary to store image references and prevent garbage collection
        self.image_cache = {}
        
        self.build_ui()
        self.refresh()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD_BG,
                        foreground=TEXT_DARK,
                        rowheight=36,
                        fieldbackground=CARD_BG,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=CARD_BG,
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")

    # ---------------- Layout Structure ----------------
    def build_ui(self):
        # 1. Top Header Banner
        header = tk.Frame(self, bg=NAVY, height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        logo_frame = tk.Frame(header, bg=NAVY)
        logo_frame.pack(side="left", padx=20, pady=12)
        
        qb_box = tk.Frame(logo_frame, bg=ORANGE, width=42, height=42)
        qb_box.pack(side="left", padx=(0, 10))
        qb_box.pack_propagate(False)
        tk.Label(qb_box, text="QB", bg=ORANGE, fg="white", font=("Segoe UI", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        title_text = tk.Frame(logo_frame, bg=NAVY)
        title_text.pack(side="left")
        tk.Label(title_text, text="QUICKBITE", bg=NAVY, fg="white", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(title_text, text="CANTEEN ORDERING SYSTEM", bg=NAVY, fg="#9ca3af", font=("Segoe UI", 8, "bold")).pack(anchor="w")

        profile_frame = tk.Frame(header, bg=NAVY)
        profile_frame.pack(side="right", padx=24, pady=16)
        
        avatar = tk.Label(profile_frame, text="👤", bg="#cbd5e1", fg=NAVY, font=("Segoe UI", 16), width=2, height=1)
        avatar.pack(side="left", padx=(0, 10))
        
        prof_text = tk.Frame(profile_frame, bg=NAVY)
        prof_text.pack(side="left")
        tk.Label(prof_text, text="Profile", bg=NAVY, fg="white", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(prof_text, text="Log-in/Profile", bg=NAVY, fg="#9ca3af", font=("Segoe UI", 8)).pack(anchor="w")

        tk.Frame(self, bg="#334155", height=1).pack(fill="x")

        # 2. Main Body Split Container
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=NAVY, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.build_sidebar(sidebar)

        workspace = tk.Frame(body, bg=BG)
        workspace.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        right_sidebar = tk.Frame(body, bg=BG, width=320)
        right_sidebar.pack(side="right", fill="y", padx=(0, 16), pady=16)
        right_sidebar.pack_propagate(False)
        self.build_right_sidebar(right_sidebar)

        self.build_center_content(workspace)

    def build_sidebar(self, parent):
        tk.Label(parent, text="", bg=NAVY).pack(pady=10)
        nav_items = [
            ("🛒", "Order Food", True),
            ("🍯", "Ingredients Status", False),
            ("⚙", "Settings", False)
        ]
        for icon, label, active in nav_items:
            bg_color = "#1e293b" if active else NAVY
            fg_color = "white" if active else "#94a3b8"
            btn = tk.Frame(parent, bg=bg_color, cursor="hand2")
            btn.pack(fill="x", padx=12, pady=4, ipady=8)
            tk.Label(btn, text=icon, bg=bg_color, fg=fg_color, font=("Segoe UI", 12)).pack(side="left", padx=(14, 10))
            tk.Label(btn, text=label, bg=bg_color, fg=fg_color, font=("Segoe UI", 10, "bold" if active else "normal")).pack(side="left")

    def build_center_content(self, parent):
        table_card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        table_card.pack(fill="x", pady=(0, 16))

        top_bar = tk.Frame(table_card, bg=CARD_BG)
        top_bar.pack(fill="x", padx=16, pady=14)

        search_box = tk.Frame(top_bar, bg=BG, highlightbackground="#cbd5e1", highlightthickness=1)
        search_box.pack(side="left", fill="x", expand=True, ipady=4, ipadx=8)
        
        tk.Label(search_box, text="🔍", bg=BG, fg=TEXT_MUTED).pack(side="left", padx=(0, 6))
        search_entry = ttk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 10), width=30)
        search_entry.pack(side="left", fill="x", expand=True)
        tk.Label(search_box, text="✕", bg=BG, fg=TEXT_MUTED, cursor="hand2").pack(side="right", padx=6)

        add_btn = tk.Button(top_bar, text="+ Add Item", bg=GOLD, fg=TEXT_DARK,
                            font=("Segoe UI", 9, "bold"), relief="flat", padx=14, pady=6,
                            cursor="hand2", command=self.add_item)
        add_btn.pack(side="right", padx=(12, 0))

        cols = ("name", "category", "price", "status", "actions")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", height=4)
        
        col_widths = (200, 140, 90, 120, 90)
        for c, w in zip(cols, col_widths):
            self.tree.heading(c, text=c.upper() if c != "actions" else "ACTIONS")
            self.tree.column(c, width=w, anchor="w" if c != "price" else "e")
            
        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=color)
            
        self.tree.pack(fill="x", padx=16, pady=(0, 14))
        self.tree.bind("<Double-1>", lambda event: self.edit_item())

        tk.Label(parent, text="PLACE ORDER", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.cards_wrapper = tk.Frame(parent, bg=BG)
        self.cards_wrapper.pack(fill="both", expand=True)

    def build_right_sidebar(self, parent):
        box1 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        box1.pack(fill="x", pady=(0, 12))
        
        tk.Label(box1, text="CURRENT ORDER SUMMARY", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        
        self.order_lines = tk.Frame(box1, bg=CARD_BG)
        self.order_lines.pack(fill="x", padx=12, pady=4)