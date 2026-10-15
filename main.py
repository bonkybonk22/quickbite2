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
        
        tk.Frame(box1, bg="#e2e8f0", height=1).pack(fill="x", padx=12, pady=6)
        
        self.subtotal_lbl = tk.Label(box1, bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 9, "bold"))
        self.subtotal_lbl.pack(anchor="e", padx=12, pady=(0, 10))
        
        tk.Button(box1, text="✔ Confirm Order", bg=NAVY, fg="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=8, cursor="hand2",
                  command=self.confirm_order).pack(fill="x", padx=12, pady=(0, 6))
        tk.Button(box1, text="Print Receipt", bg=GOLD, fg=TEXT_DARK,
                  font=("Segoe UI", 9, "bold"), relief="flat", pady=6, cursor="hand2",
                  command=self.print_receipt).pack(fill="x", padx=12, pady=(0, 12))

        box2 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        box2.pack(fill="x", pady=(0, 12))
        
        tk.Label(box2, text="Order Summary", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        
        self.qty_lbl = tk.Label(box2, bg=CARD_BG, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.qty_lbl.pack(anchor="w", padx=12, pady=2)
        
        self.total_lbl = tk.Label(box2, bg=CARD_BG, fg=ORANGE, font=("Segoe UI", 12, "bold"))
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

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for m in db.get_menu(self.search_var.get().strip()):
            self.tree.insert(
                "", "end", iid=str(m["id"]), tags=(m["status"],),
                values=(m["name"], m["category"], f"₱{m['price']:.0f}",
                        "● " + m["status"], "✏️    🗑️")
            )

    def refresh_cards(self):
        print("Current working folder:", os.getcwd())
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
                    print(f"Error loading image {image_path}: {e}")
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
        messagebox.showinfo("Order confirmed", f"Order #{self.last_order} saved.")
        self.cart.clear()
        self.refresh()

    def print_receipt(self):
        if self.last_order is None:
            messagebox.showinfo("No receipt", "Confirm an order first.")
            return
        order, items = db.get_order(self.last_order)
        lines = [
            "QUICKBITE CANTEEN",
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
            db.restock(match["id"], amount)
            self.refresh()


if __name__ == "__main__":
    App().mainloop()