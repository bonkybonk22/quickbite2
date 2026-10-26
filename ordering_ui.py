import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from database import ADMIN_ROLES, STAFF_ROLES, db
from ui_theme import (
    BG, CARD_BG, GOLD, RED_ACCENT, RED_DARK,
    RED_PALE, STATUS_COLORS, TEXT_DARK, TEXT_MUTED,
)


class OrderingUIMixin:
    MENU_COLUMN_SPECS = {
        "name": {"min": 105, "weight": 1.8},
        "category": {"min": 85, "weight": 1.2},
        "price": {"min": 62, "weight": 0.8},
        "status": {"min": 86, "weight": 1.0},
        "stock": {"min": 98, "weight": 1.1},
        "actions": {"min": 72, "weight": 0.8},
    }

    def build_order_content(self, parent):
        tk.Label(
            parent, text="ORDER FOOD", bg=BG, fg=TEXT_DARK,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            parent, text="Browse the menu and build your order.",
            bg=BG, fg=TEXT_MUTED, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 14))

        table_card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        table_card.pack(fill="x", pady=(0, 16))

        top_bar = tk.Frame(table_card, bg=CARD_BG)
        top_bar.pack(fill="x", padx=18, pady=16)

        search_box = tk.Frame(top_bar, bg="#f8fafc", highlightbackground="#cbd5e1", highlightthickness=1)
        search_box.pack(side="left", fill="x", expand=True, ipady=5, ipadx=10)
        
        tk.Label(search_box, text="Search", bg="#f8fafc", fg=RED_ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        search_entry = ttk.Entry(search_box, textvariable=self.search_var, font=("Segoe UI", 10), width=30)
        search_entry.pack(side="left", fill="x", expand=True)
        tk.Button(
            search_box, text="Clear", bg="#f8fafc", fg=TEXT_MUTED,
            relief="flat", cursor="hand2",
            command=lambda: self.search_var.set(""),
        ).pack(side="right", padx=6)

        if self.current_role in ADMIN_ROLES:
            add_btn = tk.Button(top_bar, text="+ Add Item", bg=RED_ACCENT, fg="white",
                                font=("Segoe UI", 9, "bold"), relief="flat", padx=16, pady=8,
                                cursor="hand2", command=self.add_item)
            add_btn.pack(side="right", padx=(14, 0))

        self.can_manage_menu = self.current_role in ADMIN_ROLES
        cols = ("name", "category", "price", "status", "stock")
        if self.can_manage_menu:
            cols += ("actions",)
        table_frame = tk.Frame(table_card, bg=CARD_BG)
        table_frame.pack(fill="x", padx=12, pady=(0, 16))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=4)
        
        column_labels = {
            "name": "NAME",
            "category": "CATEGORY",
            "price": "PRICE",
            "status": "STATUS",
            "stock": "SERVINGS LEFT",
            "actions": "ACTIONS",
        }
        for c in cols:
            column_anchor = (
                "e" if c == "price"
                else "center" if c in ("status", "stock", "actions")
                else "w"
            )
            self.tree.heading(
                c,
                text=column_labels[c],
                anchor=column_anchor,
            )
            self.tree.column(
                c, width=self.MENU_COLUMN_SPECS[c]["min"],
                minwidth=1,
                stretch=False,
                anchor=column_anchor,
            )
        self.menu_table_columns = cols
        self.tree.bind(
            "<Configure>",
            lambda event: self.resize_menu_columns(event),
            add="+",
        )
        
        for status, color in STATUS_COLORS.items():
            self.tree.tag_configure(status, foreground=color)
        self.tree.grid(row=0, column=0, sticky="nsew")
        if self.can_manage_menu:
            self.tree.bind("<Double-1>", lambda event: self.edit_item())

        tk.Label(parent, text="MENU", bg=BG, fg=TEXT_DARK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.cards_wrapper = tk.Frame(parent, bg=BG)
        self.cards_wrapper.pack(fill="both", expand=True)

    def resize_menu_columns(self, event):
        all_columns = self.menu_table_columns
        compact_columns = tuple(
            column for column in all_columns if column != "category"
        )
        minimum_width = sum(
            self.MENU_COLUMN_SPECS[column]["min"]
            for column in all_columns
        )
        columns = all_columns if event.width >= minimum_width else compact_columns
        self.tree.configure(displaycolumns=columns)

        labels = {
            "name": "NAME",
            "category": "CATEGORY",
            "price": "PRICE",
            "status": "STATUS",
            "stock": "SERVINGS LEFT" if columns == all_columns else "LEFT",
            "actions": "ACTIONS",
        }
        for column in columns:
            column_anchor = (
                "e" if column == "price"
                else "center" if column in ("status", "stock", "actions")
                else "w"
            )
            self.tree.heading(
                column,
                text=labels[column],
                anchor=column_anchor,
            )

        widths = {
            column: self.MENU_COLUMN_SPECS[column]["min"]
            for column in columns
        }
        remaining = max(0, event.width - sum(widths.values()))
        total_weight = sum(
            self.MENU_COLUMN_SPECS[column]["weight"] for column in columns
        )
        for column in columns:
            widths[column] += int(
                remaining
                * self.MENU_COLUMN_SPECS[column]["weight"]
                / total_weight
            )
        remainder = event.width - sum(widths.values())
        for column in columns[:max(0, remainder)]:
            widths[column] += 1

        if sum(widths.values()) > event.width:
            shrinkable = sorted(
                columns,
                key=lambda column: self.MENU_COLUMN_SPECS[column]["min"],
                reverse=True,
            )
            excess = sum(widths.values()) - event.width
            for column in shrinkable:
                reduction = min(excess, widths[column] - 1)
                widths[column] -= reduction
                excess -= reduction
                if excess == 0:
                    break
        for column, width in widths.items():
            self.tree.column(column, width=max(1, width))

    def build_right_sidebar(self, parent):
        box1 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
        box1.pack(fill="x", pady=(0, 14))
        
        tk.Label(box1, text="CURRENT ORDER SUMMARY", bg=CARD_BG, fg=TEXT_DARK,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(16, 6))
        
        self.order_lines = tk.Frame(box1, bg=CARD_BG)
        self.order_lines.pack(fill="x", padx=16, pady=6)
        
        tk.Frame(box1, bg="#e2e8f0", height=1).pack(fill="x", padx=16, pady=8)
        
        self.subtotal_lbl = tk.Label(box1, bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 9, "bold"))
        self.subtotal_lbl.pack(anchor="e", padx=16, pady=(0, 12))
        
        tk.Button(box1, text="✔ Confirm Order", bg=RED_ACCENT, fg="white",
                  activebackground=RED_DARK, activeforeground="white",
                  font=("Segoe UI", 10, "bold"), relief="flat", pady=9, cursor="hand2",
                  command=self.confirm_order).pack(fill="x", padx=16, pady=(0, 8))
        tk.Button(box1, text="Print Receipt", bg="#f1f5f9", fg=TEXT_DARK,
                  font=("Segoe UI", 9, "bold"), relief="flat", pady=7, cursor="hand2",
                  command=self.print_receipt).pack(fill="x", padx=16, pady=(0, 16))

        box2 = tk.Frame(parent, bg=RED_ACCENT, highlightbackground="#e2e8f0", highlightthickness=1)
        box2.pack(fill="x", pady=(0, 14))
        
        header_row = tk.Frame(box2, bg=RED_ACCENT)
        header_row.pack(fill="x", padx=16, pady=12)
        tk.Label(header_row, text="📄", bg=RED_ACCENT, fg="white", font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
        tk.Label(header_row, text="Order Summary", bg=RED_ACCENT, fg="white",
                 font=("Segoe UI", 10, "bold")).pack(side="left")

        details_frame = tk.Frame(box2, bg=CARD_BG)
        details_frame.pack(fill="x", padx=1, pady=(0, 1))
        
        self.qty_lbl = tk.Label(details_frame, bg=CARD_BG, fg=TEXT_MUTED, font=("Segoe UI", 9))
        self.qty_lbl.pack(anchor="w", padx=14, pady=(12, 3))
        
        self.total_lbl = tk.Label(details_frame, bg=CARD_BG, fg=RED_ACCENT, font=("Segoe UI", 12, "bold"))
        self.total_lbl.pack(anchor="w", padx=14, pady=(3, 14))

        if self.current_role in STAFF_ROLES:
            box3 = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
            box3.pack(fill="x", pady=(0, 14))

            tk.Label(box3, text="INGREDIENT STATUS", bg=CARD_BG, fg=TEXT_DARK,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(16, 6))

            self.ing_frame = tk.Frame(box3, bg=CARD_BG)
            self.ing_frame.pack(fill="x", padx=16, pady=6)

            tk.Button(box3, text="Restock Stock", bg=RED_PALE, fg=RED_DARK,
                      font=("Segoe UI", 9, "bold"), relief="flat", pady=7, cursor="hand2",
                      command=self.restock).pack(fill="x", padx=16, pady=(8, 16))

    def refresh_table(self):
        if hasattr(self, 'tree'):
            self.tree.delete(*self.tree.get_children())
            ingredients_by_id = {
                ingredient["id"]: ingredient
                for ingredient in db.get_ingredients()
            }
            for m in db.get_menu(self.search_var.get().strip()):
                values = [m["name"], m["category"], f"₱{m['price']:.0f}", "● " + m["status"]]
                ingredient = ingredients_by_id.get(m["ingredient_id"])
                values.append(
                    ingredient["stock"] if ingredient is not None else "N/A"
                )
                if self.current_role in ADMIN_ROLES:
                    values.append("✏️    🗑️")
                self.tree.insert(
                    "", "end", iid=str(m["id"]), tags=(m["status"],),
                    values=values,
                )

    def refresh_cards(self):
        if not hasattr(self, 'cards_wrapper'):
            return
        for w in self.cards_wrapper.winfo_children():
            w.destroy()
        
        menu_items = db.get_menu()
        if not menu_items:
            return

        self.cards_wrapper.update_idletasks()
        card_width = 168
        card_gap = 12
        column_count = max(
            1, (self.cards_wrapper.winfo_width() + card_gap) // (card_width + card_gap)
        )
        grid_container = tk.Frame(self.cards_wrapper, bg=BG)
        grid_container.pack(fill="x")
        for column in range(column_count):
            grid_container.columnconfigure(column, weight=1)

        for idx, m in enumerate(menu_items):
            card = tk.Frame(
                grid_container, bg=CARD_BG, highlightbackground="#e2e8f0",
                highlightthickness=1, width=card_width, height=220,
            )
            card.grid(
                row=idx // column_count, column=idx % column_count,
                padx=(card_gap // 2, card_gap // 2),
                pady=(0, card_gap), sticky="n",
            )
            card.pack_propagate(False)

            img_container = tk.Frame(card, bg="#f1f5f9", width=146, height=88)
            img_container.pack(fill="x", padx=10, pady=(10, 8))
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
                    pil_img = pil_img.resize((146, 88), Image.Resampling.LANCZOS)
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

            tk.Label(card, text=m["name"], bg=CARD_BG, fg=TEXT_DARK,
                     font=("Segoe UI", 9, "bold")).pack(anchor="center", pady=(5, 0))
            tk.Label(card, text=f"₱{m['price']:.0f}", bg=CARD_BG, fg=RED_ACCENT,
                     font=("Segoe UI", 10, "bold")).pack(anchor="center", pady=(4, 0))

            ctrl_row = tk.Frame(card, bg=CARD_BG)
            ctrl_row.pack(anchor="center", pady=(8, 12))
        
            tk.Button(ctrl_row, text="−", width=3, bg="#f1f5f9", fg=TEXT_DARK,
                      relief="flat", cursor="hand2",
                      command=lambda i=m: self.change_qty(i, -1)).pack(side="left")
            tk.Label(ctrl_row, text=str(self.cart.get(m["id"], 0)), width=3,
                     bg=CARD_BG, font=("Segoe UI", 9, "bold")).pack(side="left", padx=4)
            tk.Button(ctrl_row, text="+", width=3, bg=RED_ACCENT, fg="white",
                      activebackground=RED_DARK, relief="flat", cursor="hand2",
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
        if self.current_role not in ADMIN_ROLES:
            messagebox.showerror("Access denied", "Only admins can manage menu items.", parent=self)
            return
        self.item_form()

    def edit_item(self):
        if self.current_role not in ADMIN_ROLES:
            messagebox.showerror("Access denied", "Only admins can manage menu items.", parent=self)
            return
        item_id = self.selected_id()
        if item_id:
            item = next(m for m in db.get_menu() if m["id"] == item_id)
            self.item_form(item)

    def item_form(self, item=None):
        if self.current_role not in ADMIN_ROLES:
            messagebox.showerror("Access denied", "Only admins can manage menu items.", parent=self)
            return
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
        if self.current_role not in STAFF_ROLES:
            messagebox.showerror("Access denied", "Only canteen staff can restock inventory.", parent=self)
            return
        ings = db.get_ingredients()
        if not ings:
            messagebox.showinfo("No ingredients", "Add an ingredient before restocking.", parent=self)
            return

        win = tk.Toplevel(self)
        win.title("Restock Ingredient")
        win.configure(bg=CARD_BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        form = tk.Frame(win, bg=CARD_BG)
        form.pack(fill="both", padx=24, pady=22)
        tk.Label(
            form, text="RESTOCK INVENTORY", bg=CARD_BG, fg=RED_ACCENT,
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        tk.Label(
            form, text="Ingredient", bg=CARD_BG, fg=TEXT_DARK,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=6)
        ingredient_var = tk.StringVar(value=ings[0]["name"])
        ttk.Combobox(
            form, textvariable=ingredient_var,
            values=tuple(ingredient["name"] for ingredient in ings),
            state="readonly", width=24,
        ).grid(row=1, column=1, sticky="ew", padx=(16, 0), pady=6)

        tk.Label(
            form, text="Quantity to add", bg=CARD_BG, fg=TEXT_DARK,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=0, sticky="w", pady=6)
        amount_var = tk.StringVar(value="1")
        ttk.Spinbox(
            form, textvariable=amount_var, from_=1, to=1_000_000, width=26,
        ).grid(row=2, column=1, sticky="ew", padx=(16, 0), pady=6)

        def save_restock():
            try:
                amount = int(amount_var.get())
                if amount < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid quantity", "Enter a whole number greater than zero.", parent=win
                )
                return
            ingredient = next(
                item for item in ings if item["name"] == ingredient_var.get()
            )
            db.restock_ingredient(ingredient["id"], amount)
            win.destroy()
            self.refresh()
            messagebox.showinfo(
                "Restocked", f"Added {amount} to {ingredient['name']}.", parent=self
            )

        actions = tk.Frame(form, bg=CARD_BG)
        actions.grid(row=3, column=0, columnspan=2, sticky="e", pady=(18, 0))
        tk.Button(
            actions, text="Cancel", bg="#e2e8f0", fg=TEXT_DARK,
            relief="flat", padx=14, pady=7, command=win.destroy,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            actions, text="Add Stock", bg=RED_ACCENT, fg="white",
            font=("Segoe UI", 9, "bold"), relief="flat", padx=16, pady=7,
            command=save_restock,
        ).pack(side="left")
