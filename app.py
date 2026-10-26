import tkinter as tk
from tkinter import ttk, messagebox

from admin_dashboard import AdminDashboardMixin
from auth_ui import LoginWindow
from database import ADMIN_ROLES, STAFF_ROLES, db
from ordering_ui import OrderingUIMixin
from ui_theme import BG, CARD_BG, NAVY, ORANGE, RED_ACCENT, TEXT_DARK, TEXT_MUTED


class App(OrderingUIMixin, AdminDashboardMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.minsize(1200, 750)
        self.title("QuickBite - Canteen Ordering System")
        self.geometry("1280x760")
        self.configure(bg=NAVY)
        
        self.current_user = ""
        self.current_role = ""
        self.setup_styles()
        self.cart = {}
        self.last_order = None
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        
        self.image_cache = {}
        
        self.withdraw()
        LoginWindow(self, self.start_app)

    def start_app(self, username, role):
        self.current_user = username
        self.current_role = role
        self.deiconify()
        self.build_ui()
        self.refresh()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=CARD_BG,
                        foreground=TEXT_DARK,
                        rowheight=40,
                        fieldbackground=CARD_BG,
                        padding=(8, 4),
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=CARD_BG,
                        foreground=TEXT_MUTED,
                        padding=(10, 8),
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.configure("TEntry", padding=(8, 6))
        style.configure("TCombobox", padding=(8, 5))
        style.configure("TSpinbox", padding=(8, 5))
        style.map("Treeview", background=[("selected", RED_ACCENT)])

    def build_ui(self):
        self.grid_rowconfigure(0, weight=0, minsize=75)
        self.grid_rowconfigure(1, weight=0, minsize=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.header = tk.Frame(self, bg=NAVY, height=75)
        self.header.grid(row=0, column=0, sticky="ew")
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

        tk.Frame(self, bg="#334155", height=1).grid(row=1, column=0, sticky="ew")

        body = tk.Frame(self, bg=BG)
        self.body = body
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=0, minsize=220)
        body.grid_columnconfigure(1, weight=1)
        body.grid_columnconfigure(2, weight=0, minsize=320)

        sidebar = tk.Frame(body, bg=NAVY, width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)
        self.build_sidebar(sidebar)

        self.workspace_outer = tk.Frame(body, bg=BG)
        self.workspace_outer.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.workspace_outer.grid_rowconfigure(0, weight=1)
        self.workspace_outer.grid_columnconfigure(0, weight=1)

        self.right_sidebar = tk.Frame(body, bg=BG, width=320)
        self.right_sidebar.grid(row=0, column=2, sticky="nsew", padx=(0, 16), pady=16)
        self.right_sidebar.pack_propagate(False)
        self.build_right_sidebar(self.right_sidebar)

        self.views = {}
        
        self.views["order"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_order_content(self.views["order"])

        self.build_role_views()

        self.switch_view("order")

    def build_role_views(self):
        if self.current_role in STAFF_ROLES:
            self.views["ingredients"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_ingredients_content(self.views["ingredients"])

            self.views["sales"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_monthly_sales_content(self.views["sales"])
        elif self.current_role in ADMIN_ROLES:
            self.views["settings"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_settings_content(self.views["settings"])

            self.views["verification"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_verification_content(self.views["verification"])

    def remove_role_views(self):
        for key in ("ingredients", "settings", "sales", "verification"):
            frame = self.views.pop(key, None)
            if frame is not None:
                frame.destroy()
        for attribute in (
            "ing_tree", "biz_name_entry", "biz_sub_entry",
            "monthly_sales_tree", "monthly_sales_summary", "report_month",
            "report_year", "pending_tree",
        ):
            if hasattr(self, attribute):
                delattr(self, attribute)

    def relogin(self):
        LoginWindow(self, self.switch_account)

    def switch_account(self, username, role):
        self.current_user = username
        self.current_role = role
        self.prof_name_lbl.config(text=username)
        self.remove_role_views()
        self.build_role_views()
        self.views["order"].destroy()
        self.views["order"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_order_content(self.views["order"])
        for child in self.right_sidebar.winfo_children():
            child.destroy()
        if hasattr(self, "ing_frame"):
            del self.ing_frame
        self.build_right_sidebar(self.right_sidebar)
        self.build_sidebar(self.sidebar)
        self.switch_view("order")

    def build_sidebar(self, parent):
        self.sidebar = parent
        for child in parent.winfo_children():
            child.destroy()
        tk.Label(parent, text="", bg=NAVY).pack(pady=10)
        self.nav_buttons = {}
        nav_items = [
            ("🛒", "Order Food", "order"),
        ]
        if self.current_role in STAFF_ROLES:
            nav_items.extend((
                ("🍯", "Ingredients Status", "ingredients"),
                ("📊", "Monthly Sales", "sales"),
            ))
        elif self.current_role in ADMIN_ROLES:
            nav_items.extend((
                ("⚙", "Settings", "settings"),
                ("✓", "Verify Accounts", "verification"),
            ))
        for icon, label, key in nav_items:
            btn = tk.Frame(parent, bg=NAVY, cursor="hand2")
            btn.pack(fill="x", padx=12, pady=4, ipady=8)
            lbl_icon = tk.Label(btn, text=icon, bg=NAVY, fg="#94a3b8", font=("Segoe UI", 12))
            lbl_icon.pack(side="left", padx=(14, 10))
            lbl_text = tk.Label(btn, text=label, bg=NAVY, fg="#94a3b8", font=("Segoe UI", 10))
            lbl_text.pack(side="left")
        
            for widget in (btn, lbl_icon, lbl_text):
                widget.bind("<Button-1>", lambda e, k=key: self.switch_view(k))
        
            self.nav_buttons[key] = (btn, lbl_icon, lbl_text)

    def switch_view(self, key):
        view_roles = {
            "ingredients": STAFF_ROLES,
            "sales": STAFF_ROLES,
            "settings": ADMIN_ROLES,
            "verification": ADMIN_ROLES,
        }
        if key in view_roles and self.current_role not in view_roles[key]:
            messagebox.showerror(
                "Access denied",
                "You do not have permission to access this view.",
                parent=self,
            )
            return
        if key not in self.views:
            return

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
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_remove()
            
        if key == "order":
            self.body.grid_columnconfigure(2, minsize=320)
            self.right_sidebar.grid()
        else:
            self.right_sidebar.grid_remove()
            self.body.grid_columnconfigure(2, minsize=0)

        self.current_view = key
        if key == "sales":
            self.generate_monthly_sales_report()
        self.refresh()

    def refresh(self):
        self.refresh_table()
        self.refresh_cards()
        self.refresh_summary()
        self.refresh_ingredients()
        self.refresh_ingredients_table()
        self.refresh_pending_accounts()
