import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import os
from datetime import datetime

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
    "Normal": "#2e9e5b", 
    "High": "#2e9e5b"
}

# --- In-Memory Data Store (Replaces database.py) ---
class InMemoryDB:
    def __init__(self):
        self.settings = {
            "business_name": "QUICKBITE",
            "receipt_header": "CANTEEN ORDERING SYSTEM",
            "low_threshold": 5,
            "high_threshold": 50
        }
        self.ingredients = [
            {"id": 1, "name": "Pork", "status": "Normal", "stock": 25},
            {"id": 2, "name": "Chicken", "status": "Normal", "stock": 30},
            {"id": 3, "name": "Noodles", "status": "Low Stock", "stock": 3},
            {"id": 4, "name": "Vegetables", "status": "Normal", "stock": 15},
        ]
        self.menu = [
            {"id": 1, "name": "Adobo", "category": "Main Dish", "price": 95, "status": "Available", "stock": 15, "ingredient_id": 1},
            {"id": 2, "name": "Sinigang", "category": "Soup", "price": 110, "status": "Available", "stock": 10, "ingredient_id": 1},
            {"id": 3, "name": "Pancit", "category": "Noodles", "price": 80, "status": "Low Stock", "stock": 3, "ingredient_id": 3},
            {"id": 4, "name": "Lumpia", "category": "Appetizer", "price": 50, "status": "Available", "stock": 20, "ingredient_id": 2},
        ]
        self.orders = []
        self._next_order_id = 1

    def get_menu(self, search=""):
        if not search:
            return self.menu
        return [m for m in self.menu if search.lower() in m["name"].lower() or search.lower() in m["category"].lower()]

    def get_ingredients(self):
        return self.ingredients

    def add_item(self, name, category, price, ingredient_id):
        new_id = max([m["id"] for m in self.menu], default=0) + 1
        ing = next((i for i in self.ingredients if i["id"] == ingredient_id), None)
        stock = ing["stock"] if ing else 10
        status = "Available" if stock > 0 else "Out of Stock"
        self.menu.append({
            "id": new_id, "name": name, "category": category,
            "price": price, "status": status, "stock": stock, "ingredient_id": ingredient_id
        })

    def update_item(self, item_id, name, category, price, ingredient_id):
        for m in self.menu:
            if m["id"] == item_id:
                m["name"] = name
                m["category"] = category
                m["price"] = price
                m["ingredient_id"] = ingredient_id

    def restock_ingredient(self, ing_id, amount):
        for i in self.ingredients:
            if i["id"] == ing_id:
                i["stock"] += amount
                if i["stock"] > self.settings["low_threshold"]:
                    i["status"] = "Normal"
        # Update linked menu items stock
        for m in self.menu:
            if m["ingredient_id"] == ing_id:
                ing = next(i for i in self.ingredients if i["id"] == ing_id)
                m["stock"] = ing["stock"]
                m["status"] = "Available" if m["stock"] > 0 else "Out of Stock"

    def save_order(self, cart):
        total = 0
        order_items = []
        for item_id, qty in cart.items():
            m = next((item for item in self.menu if item["id"] == item_id), None)
            if not m or m["stock"] < qty:
                raise ValueError(f"Insufficient stock for {m['name'] if m else 'item'}")
            total += m["price"] * qty
            order_items.append({"name": m["name"], "price": m["price"], "quantity": qty})
            m["stock"] -= qty
            if m["stock"] == 0:
                m["status"] = "Out of Stock"

        order_id = self._next_order_id
        self._next_order_id += 1
        order_record = {
            "id": order_id,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "items": order_items
        }
        self.orders.append(order_record)
        return order_id

    def get_order(self, order_id):
        o = next((ord for ord in self.orders if ord["id"] == order_id), None)
        if o:
            return o, o["items"]
        return None, []

    def clear_orders(self):
        self.orders.clear()


db = InMemoryDB()


# --- Login Window ---
class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("QuickBite - Login")
        self.geometry("380x280")
        self.configure(bg=NAVY)
        self.resizable(False, False)
        self.on_success = on_success
        
        self.grab_set()
        
        tk.Label(self, text="QUICKBITE", bg=NAVY, fg="white", font=("Segoe UI", 16, "bold")).pack(pady=(25, 5))
        tk.Label(self, text="Canteen Ordering System", bg=NAVY, fg=GOLD, font=("Segoe UI", 9)).pack(pady=(0, 20))
        
        form_frame = tk.Frame(self, bg=NAVY)
        form_frame.pack(padx=30, fill="x")
        
        tk.Label(form_frame, text="Username", bg=NAVY, fg="white", font=("Segoe UI", 9)).pack(anchor="w")
        self.user_entry = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(2, 10))
        self.user_entry.insert(0, "admin")
        
        tk.Label(form_frame, text="Password", bg=NAVY, fg="white", font=("Segoe UI", 9)).pack(anchor="w")
        self.pass_entry = ttk.Entry(form_frame, show="*", font=("Segoe UI", 10))
        self.pass_entry.pack(fill="x", pady=(2, 15))
        self.pass_entry.insert(0, "admin")
        
        tk.Button(self, text="Login", bg=ORANGE, fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", command=self.verify_login).pack(fill="x", padx=30, ipady=4)

    def verify_login(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        if u and p:
            self.destroy()
            self.on_success(u)
        else:
            messagebox.showerror("Error", "Please enter valid credentials.", parent=self)


# --- Main Application ---
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuickBite - Canteen Ordering System")
        self.geometry("1280x760")
        self.minsize(1100, 700)
        self.configure(bg=NAVY)
        
        self.current_user = "Admin"
        self.setup_styles()
        self.cart = {}
        self.last_order = None
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        
        self.image_cache = {}
        
        # Show login dialog first
        self.withdraw()
        LoginWindow(self, self.start_app)

    def start_app(self, username):
        self.current_user = username
        self.deiconify()
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
        self.header = tk.Frame(self, bg=NAVY, height=75)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        logo_frame = tk.Frame(self.header, bg=NAVY)
        logo_frame.pack(side="left", padx=20, pady=12)
        
        qb_box = tk.Frame(logo_frame, bg=ORANGE, width=42, height=42)
        qb_box.pack(side="left", padx=(0, 10))
        qb_box.pack_propagate(False)
        tk.Label(qb_box, text="QB", bg=ORANGE, fg="white", font=("Segoe UI", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        self.title_text_frame = tk.Frame(logo_frame, bg=NAVY)
        self.title_text_frame.pack(side="left")
        self.header_main_lbl = tk.Label(self.title_text_frame, text=db.settings["business_name"], bg=NAVY, fg="white", font=("Segoe UI", 18, "bold"))
        self.header_main_lbl.pack(anchor="w")
        self.header_sub_lbl = tk.Label(self.title_text_frame, text=db.settings["receipt_header"], bg=NAVY, fg="#9ca3af", font=("Segoe UI", 8, "bold"))
        self.header_sub_lbl.pack(anchor="w")

        profile_frame = tk.Frame(self.header, bg=NAVY, cursor="hand2")
        profile_frame.pack(side="right", padx=24, pady=16)
        profile_frame.bind("<Button-1>", lambda e: self.relogin())
        
        avatar = tk.Label(profile_frame, text="👤", bg="#cbd5e1", fg=NAVY, font=("Segoe UI", 16), width=2, height=1)
        avatar.pack(side="left", padx=(0, 10))
        avatar.bind("<Button-1>", lambda e: self.relogin())
        
        prof_text = tk.Frame(profile_frame, bg=NAVY)
        prof_text.pack(side="left")
        self.prof_name_lbl = tk.Label(prof_text, text=self.current_user, bg=NAVY, fg="white", font=("Segoe UI", 10, "bold"))
        self.prof_name_lbl.pack(anchor="w")
        tk.Label(prof_text, text="Switch / Logout", bg=NAVY, fg="#9ca3af", font=("Segoe UI", 8)).pack(anchor="w")

        tk.Frame(self, bg="#334155", height=1).pack(fill="x")

        # 2. Main Body Split Container
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        sidebar = tk.Frame(body, bg=NAVY, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.build_sidebar(sidebar)

        # Workspace container holding different views
        self.workspace_outer = tk.Frame(body, bg=BG)
        self.workspace_outer.pack(side="left", fill="both", expand=True, padx=16, pady=16)

        # Right Sidebar (Order Summary & Quick Ingredients)
        self.right_sidebar = tk.Frame(body, bg=BG, width=320)
        self.right_sidebar.pack(side="right", fill="y", padx=(0, 16), pady=16)
        self.right_sidebar.pack_propagate(False)
        self.build_right_sidebar(self.right_sidebar)

        # Build views
        self.views = {}
        
        # View 1: Order Food (Dashboard)
        self.views["order"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_order_content(self.views["order"])

        # View 2: Ingredients Stock
        self.views["ingredients"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_ingredients_content(self.views["ingredients"])

        # View 3: Settings
        self.views["settings"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_settings_content(self.views["settings"])

        self.switch_view("order")

    def relogin(self):
        LoginWindow(self, lambda u: setattr(self, 'current_user', u) or self.prof_name_lbl.config(text=u))

    def build_sidebar(self, parent):
        tk.Label(parent, text="", bg=NAVY).pack(pady=10)
        self.nav_buttons = {}
        nav_items = [
            ("🛒", "Order Food", "order"),
            ("🍯", "Ingredients Status", "ingredients"),
            ("⚙", "Settings", "settings")
        ]
        for icon, label, key in nav_items:
            btn = tk.Frame(parent, bg=NAVY, cursor="hand2")
            btn.pack(fill="x", padx=12, pady=4, ipady=8)
            lbl_icon = tk.Label(btn, text=icon, bg=NAVY, fg="#94a3b8", font=("Segoe UI", 12))
            lbl_icon.pack(side="left", padx=(14, 10))
            lbl_text = tk.Label(btn, text=label, bg=NAVY, fg="#94a3b8", font=("Segoe UI", 10))
            lbl_text.pack(side="left")
            
            # Bind click events
            for widget in (btn, lbl_icon, lbl_text):
                widget.bind("<Button-1>", lambda e, k=key: self.switch_view(k))
            
            self.nav_buttons[key] = (btn, lbl_icon, lbl_text)

    def switch_view(self, key):
        for k, (btn, icon_l, text_l) in self.nav_buttons.items():
            if k == key:
                btn.config(bg="#1e293b")
                icon_l.config(bg="#1e293b", fg="white")
                text_l.config(bg="#1e293b", fg="white", font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg=NAVY)
                icon_l.config(bg=NAVY, fg="#94a3b8")
                text_l.config(bg=NAVY, fg="#94a3b8", font=("Segoe UI", 10, "normal"))

        for v_key, frame in self.views.items():
            if v_key == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
                
        # Toggle right sidebar visibility depending on view
        if key == "order":
            self.right_sidebar.pack(side="right", fill="y", padx=(0, 16), pady=16)
        else:
            self.right_sidebar.pack_forget()

        self.refresh()

    # ---------------- View 1: Order Food ----------------
    def build_order_content(self, parent):
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

    # ---------------- View 2: Ingredients Stock ----------------
    def build_ingredients_content(self, parent):
        tk.Label(parent, text="INGREDIENT STOCK MANAGEMENT", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

        ing_card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        ing_card.pack(fill="both", expand=True, padx=0, pady=0)

        top_act = tk.Frame(ing_card, bg=CARD_BG)
        top_act.pack(fill="x", padx=16, pady=16)

        tk.Button(top_act, text="+ Restock Ingredient", bg=ORANGE, fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", padx=12, pady=6,
                  cursor="hand2", command=self.restock).pack(side="left")

        cols = ("id", "name", "status", "stock")
        self.ing_tree = ttk.Treeview(ing_card, columns=cols, show="headings", height=12)
        
        col_widths = (80, 250, 180, 120)
        col_names = ("ID", "Ingredient Name", "Status", "Stock Level")
        for c, w, name in zip(cols, col_widths, col_names):
            self.ing_tree.heading(c, text=name)
            self.ing_tree.column(c, width=w, anchor="w" if c != "stock" else "e")
            
        self.ing_tree.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    # ---------------- View 3: Settings ----------------
    def build_settings_content(self, parent):
        tk.Label(parent, text="SYSTEM SETTINGS", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

        settings_card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        settings_card.pack(fill="x", padx=0, pady=(0, 16))

        inner = tk.Frame(settings_card, bg=CARD_BG)
        inner.pack(fill="x", padx=20, pady=20)

        tk.Label(inner, text="Business Name:", bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        self.biz_name_entry = ttk.Entry(inner, font=("Segoe UI", 10), width=30)
        self.biz_name_entry.grid(row=0, column=1, sticky="w", padx=12, pady=8)
        self.biz_name_entry.insert(0, db.settings["business_name"])

        tk.Label(inner, text="Receipt Header Subtitle:", bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.biz_sub_entry = ttk.Entry(inner, font=("Segoe UI", 10), width=30)
        self.biz_sub_entry.grid(row=1, column=1, sticky="w", padx=12, pady=8)
        self.biz_sub_entry.insert(0, db.settings["receipt_header"])

        tk.Label(inner, text="Low Stock Threshold:", bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=8)
        self.low_thresh_entry = ttk.Entry(inner, font=("Segoe UI", 10), width=30)
        self.low_thresh_entry.grid(row=2, column=1, sticky="w", padx=12, pady=8)
        self.low_thresh_entry.insert(0, str(db.settings["low_threshold"]))

        tk.Button(inner, text="Save Settings", bg=NAVY, fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=16, pady=6, cursor="hand2", command=self.save_settings).grid(row=3, column=1, sticky="w", padx=12, pady=12)

        # Sales Summary & History Management Card
        stats_card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        stats_card.pack(fill="x", padx=0, pady=0)

        stats_inner = tk.Frame(stats_card, bg=CARD_BG)
        stats_inner.pack(fill="x", padx=20, pady=20)

        tk.Label(stats_inner, text="SALES SUMMARY & HISTORY", bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.sales_stat_lbl = tk.Label(stats_inner, text="", bg=CARD_BG, fg=TEXT_MUTED, font=("Segoe UI", 10))
        self.sales_stat_lbl.pack(anchor="w", pady=4)

        tk.Button(stats_inner, text="🗑 Clear Order History", bg="#d62828", fg="white", font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=14, pady=6, cursor="hand2", command=self.clear_history).pack(anchor="w", pady=(12, 0))

    def save_settings(self):
        try:
            db.settings["business_name"] = self.biz_name_entry.get().strip()
            db.settings["receipt_header"] = self.biz_sub_entry.get().strip()
            db.settings["low_threshold"] = int(self.low_thresh_entry.get().strip())
            
            self.header_main_lbl.config(text=db.settings["business_name"])
            self.header_sub_lbl.config(text=db.settings["receipt_header"])
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.refresh()
        except ValueError:
            messagebox.showerror("Error", "Low stock threshold must be a valid integer.")

    def clear_history(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all order history and sales stats?"):
            db.clear_orders()
            self.refresh()
            messagebox.showinfo("Cleared", "Order history cleared.")

    # ---------------- Right Sidebar ----------------
    def build_right_sidebar(self, parent):
        box1 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        box1.pack(fill="x", pady=(0, 12))
        
        tk.Label(box1, text="CURRENT ORDER SUMMARY", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        
        self.order_lines = tk.Frame(box1, bg=CARD_BG)
        self.order_lines.pack(fill="x", padx=12, pady=4)
        
        tk.Frame(box1, bg="#e2e8f0", height=1).pack(fill="x", padx=12, pady=6)
        
        self.subtotal_lbl = tk.Label(box1, bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 9, "bold"))
        self.subtotal_lbl.pack(anchor="e", padx=12, pady=(0, 10))
        
        tk.Button(box1, text="✔ Confirm Order", bg=NAVY, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=8, cursor="hand2",
                  command=self.confirm_order).pack(fill="x", padx=12, pady=(0, 6))
        tk.Button(box1, text="Print Receipt", bg=GOLD, fg=TEXT_DARK,
                  font=("Segoe UI", 9, "bold"), relief="flat", pady=6, cursor="hand2",
                  command=self.print_receipt).pack(fill="x", padx=12, pady=(0, 12))

        # Order Summary Card (Styled with orange header banner)
        box2 = tk.Frame(parent, bg=ORANGE, highlightbackground="#e2e8f0", highlightthickness=1)
        box2.pack(fill="x", pady=(0, 12))
        
        header_row = tk.Frame(box2, bg=ORANGE)
        header_row.pack(fill="x", padx=12, pady=10)
        tk.Label(header_row, text="📄", bg=ORANGE, fg="white", font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
        tk.Label(header_row, text="Order Summary", bg=ORANGE, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left")

        details_frame = tk.Frame(box2, bg=CARD_BG)
        details_frame.pack(fill="x", padx=1, pady=(0, 1))
        
        self.qty_lbl = tk.Label(details_frame, bg=CARD_BG, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.qty_lbl.pack(anchor="w", padx=12, pady=(10, 2))
        
        self.total_lbl = tk.Label(details_frame, bg=CARD_BG, fg=ORANGE, font=("Segoe UI", 12, "bold"))
        self.total_lbl.pack(anchor="w", padx=12, pady=(2, 12))

        box3 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        box3.pack(fill="x")
        
        tk.Label(box3, text="INGREDIENT STATUS", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        
        self.ing_frame = tk.Frame(box3, bg=CARD_BG)
        self.ing_frame.pack(fill="x", padx=12, pady=4)
        
        tk.Button(box3, text="Restock", bg="#e2e8f0", fg=TEXT_DARK,
                  font=("Segoe UI", 9, "bold"), relief="flat", pady=6, cursor="hand2",
                  command=self.restock).pack(fill="x", padx=12, pady=(8, 12))

    # ---------------- Data Binding & Refresh ----------------
    def refresh(self):
        self.refresh_table()
        self.refresh_cards()
        self.refresh_summary()
        self.refresh_ingredients()
        self.refresh_ingredients_table()
        self.refresh_settings_stats()

    def refresh_table(self):
        if hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            for m in db.get_menu(self.search_var.get().strip()):
                self.tree.insert(
                    "", "end", iid=str(m["id"]), tags=(m["status"],),
                    values=(m["name"], m["category"], f"₱{m['price']:.0f}",
                            "● " + m["status"], "✏️    🗑️")
                )

    def refresh_ingredients_table(self):
        if hasattr(self, 'ing_tree'):
            self.ing_tree.delete(*self.ing_tree.get_children())
            for ing in db.get_ingredients():
                self.ing_tree.insert(
                    "", "end", iid=str(ing["id"]), tags=(ing["status"],),
                    values=(ing["id"], ing["name"], ing["status"], ing["stock"])
                )

    def refresh_settings_stats(self):
        if hasattr(self, 'sales_stat_lbl'):
            total_orders = len(db.orders)
            total_revenue = sum(o["total"] for o in db.orders)
            self.sales_stat_lbl.config(text=f"Total Completed Orders: {total_orders}\nTotal Sales Revenue: ₱{total_revenue:.2f}")

    def refresh_cards(self):
        if not hasattr(self, 'cards_wrapper'):
            return
        for w in self.cards_wrapper.winfo_children():
            w.destroy()
            
        menu_items = db.get_menu()
        if not menu_items:
            return

        grid_container = tk.Frame(self.cards_wrapper, bg=BG)
        grid_container.pack(anchor="w")

        for idx, m in enumerate(menu_items):
            card = tk.Frame(grid_container, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1, width=155, height=185)
            card.grid(row=0, column=idx, padx=(0, 12), sticky="n")
            card.pack_propagate(False)

            img_container = tk.Frame(card, bg="#e2e8f0", height=80)
            img_container.pack(fill="x", padx=8, pady=8)
            img_container.pack_propagate(False)

            base_name = m["name"].lower().replace(' ', '_')
            image_path = None
            for ext in [".jpg", ".jpeg", ".png"]:
                if os.path.exists(base_name + ext):
                    image_path = base_name + ext
                    break

            if image_path:
                try:
                    pil_img = Image.open(image_path)
                    pil_img = pil_img.resize((135, 80), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(pil_img)
                    self.image_cache[m["id"]] = photo
                    img_lbl = tk.Label(img_container, image=photo, bg="#e2e8f0")
                    img_lbl.pack(fill="both", expand=True)
                except Exception as e:
                    tk.Label(img_container, text="🍽️", bg="#e2e8f0", font=("Segoe UI", 22)).place(relx=0.5, rely=0.5, anchor="center")
            else:
                food_emojis = {"Adobo": "🥘", "Sinigang": "🍲", "Pancit": "🍜", "Lumpia": "🥟"}
                emoji = food_emojis.get(m["name"], "🍽️")
                tk.Label(img_container, text=emoji, bg="#e2e8f0", font=("Segoe UI", 22)).place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(card, text=f"₱{m['price']:.0f}", bg=CARD_BG, fg=TEXT_DARK,
                     font=("Segoe UI", 10, "bold")).pack(anchor="center")

            ctrl_row = tk.Frame(card, bg=CARD_BG)
            ctrl_row.pack(anchor="center", pady=(4, 8))
            
            tk.Button(ctrl_row, text="-", width=2, bg="#e2e8f0", relief="flat",
                      command=lambda i=m: self.change_qty(i, -1)).pack(side="left")
            tk.Label(ctrl_row, text=str(self.cart.get(m["id"], 0)), width=3,
                     bg=CARD_BG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=2)
            tk.Button(ctrl_row, text="+", width=2, bg=ORANGE, fg="white", relief="flat",
                      command=lambda i=m: self.change_qty(i, 1)).pack(side="left")

    def refresh_summary(self):
        if not hasattr(self, 'order_lines'):
            return
        for w in self.order_lines.winfo_children():
            w.destroy()
            
        menu = {m["id"]: m for m in db.get_menu()}
        total = qty_total = 0
        
        for item_id, qty in self.cart.items():
            if item_id not in menu:
                continue
            m = menu[item_id]
            line = tk.Frame(self.order_lines, bg=CARD_BG)
            line.pack(fill="x", pady=2)
            tk.Label(line, text=m["name"], bg=CARD_BG, font=("Segoe UI", 9)).pack(side="left")
            tk.Label(line, text=f"{qty} × ₱{m['price']:.0f}", bg=CARD_BG, font=("Segoe UI", 9)).pack(side="right")
            total += m["price"] * qty
            qty_total += qty
            
        self.subtotal_lbl.config(text=f"Subtotal  ₱{total:.2f}")
        self.qty_lbl.config(text=f"Quantity / Serving:  {qty_total}")
        self.total_lbl.config(text=f"Total Amount:  ₱{total:.2f}")

    def refresh_ingredients(self):
        if not hasattr(self, 'ing_frame'):
            return
        for w in self.ing_frame.winfo_children():
            w.destroy()
            
        for ing in db.get_ingredients():
            row = tk.Frame(self.ing_frame, bg=CARD_BG)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{ing['name']}:", bg=CARD_BG, font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row, text=ing['status'], bg=CARD_BG, fg=STATUS_COLORS.get(ing['status'], TEXT_MUTED),
                     font=("Segoe UI", 9, "bold")).pack(side="right")

    # ---------------- Actions & Modals ----------------
    def change_qty(self, item, delta):
        new = max(0, self.cart.get(item["id"], 0) + delta)
        if new > item["stock"]:
            messagebox.showwarning("Out of stock", f"Only {item['stock']} serving(s) left.")
            return
        if new == 0:
            self.cart.pop(item["id"], None)
        else:
            self.cart[item["id"]] = new
        self.refresh_cards()
        self.refresh_summary()

    def confirm_order(self):
        if not self.cart:
            messagebox.showinfo("Empty order", "Add at least one item first.")
            return
        try:
            self.last_order = db.save_order(self.cart)
        except ValueError as e:
            messagebox.showerror("Cannot place order", str(e))
            return
        messagebox.showinfo("Order confirmed", f"Order #{self.last_order} saved successfully.")
        self.cart.clear()
        self.refresh()

    def print_receipt(self):
        if self.last_order is None:
            messagebox.showinfo("No receipt", "Confirm an order first.")
            return
        order, items = db.get_order(self.last_order)
        lines = [
            db.settings["business_name"],
            db.settings["receipt_header"],
            f"Order #{order['id']}  {order['created_at']}",
            "-" * 32
        ]
        for i in items:
            lines.append(
                f"{i['name']:<14}{i['quantity']} x P{i['price']:.0f}".ljust(24)
                + f"P{i['quantity'] * i['price']:.2f}"
            )
        lines += ["-" * 32, f"TOTAL: P{order['total']:.2f}"]
        filename = f"receipt_{order['id']}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Receipt saved", f"Saved as {filename}\n\n" + "\n".join(lines))

    def selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select an item", "Click a row in the table first.")
            return None
        return int(sel[0])

    def add_item(self):
        self.item_form()

    def edit_item(self):
        item_id = self.selected_id()
        if item_id:
            item = next(m for m in db.get_menu() if m["id"] == item_id)
            self.item_form(item)

    def item_form(self, item=None):
        win = tk.Toplevel(self)
        win.title("Edit Item" if item else "Add Item")
        win.geometry("340x280")
        win.grab_set()
        
        ings = db.get_ingredients()
        names = [i["name"] for i in ings]
        
        name_v = tk.StringVar(value=item["name"] if item else "")
        cat_v = tk.StringVar(value=item["category"] if item else "")
        price_v = tk.StringVar(value=str(item["price"]) if item else "")
        current = next((i["name"] for i in ings if item and i["id"] == item["ingredient_id"]), names[0] if names else "")
        ing_v = tk.StringVar(value=current)

        for r, (label, var) in enumerate([("Name", name_v), ("Category", cat_v), ("Price", price_v)]):
            tk.Label(win, text=label).grid(row=r, column=0, padx=8, pady=6, sticky="e")
            ttk.Entry(win, textvariable=var).grid(row=r, column=1, padx=8, pady=6)

        tk.Label(win, text="Ingredient").grid(row=3, column=0, padx=8, pady=6, sticky="e")
        ttk.Combobox(win, textvariable=ing_v, values=names, state="readonly").grid(row=3, column=1, padx=8, pady=6)

        def save():
            try:
                price = float(price_v.get())
                if not name_v.get().strip() or not cat_v.get().strip() or price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid", "Fill in every field with a valid price.", parent=win)
                return
            ing_id = next(i["id"] for i in ings if i["name"] == ing_v.get())
            if item:
                db.update_item(item["id"], name_v.get().strip(), cat_v.get().strip(), price, ing_id)
            else:
                db.add_item(name_v.get().strip(), cat_v.get().strip(), price, ing_id)
            win.destroy()
            self.refresh()

        tk.Button(win, text="Save", bg=GOLD, relief="flat", command=save).grid(row=4, column=0, columnspan=2, pady=12)

    def restock(self):
        ings = db.get_ingredients()
        name = simpledialog.askstring("Restock", "Ingredient (" + ", ".join(i["name"] for i in ings) + "):")
        if not name:
            return
        match = next((i for i in ings if i["name"].lower() == name.strip().lower()), None)
        if not match:
            messagebox.showerror("Not found", "No ingredient with that name.")
            return
        amount = simpledialog.askinteger("Restock", f"Add how many to {match['name']}?", minvalue=1)
        if amount:
            db.restock_ingredient(match["id"], amount)
            self.refresh()
            messagebox.showinfo("Restocked", f"Successfully added {amount} to {match['name']}.")

if __name__ == "__main__":
    App().mainloop()