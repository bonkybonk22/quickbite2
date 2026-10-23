import tkinter as tk
from tkinter import ttk, messagebox

from admin_dashboard import AdminDashboardMixin
from auth_ui import LoginWindow
from database import db
from ordering_ui import OrderingUIMixin
from ui_theme import BG, CARD_BG, NAVY, ORANGE, RED_ACCENT, TEXT_DARK, TEXT_MUTED


class App(OrderingUIMixin, AdminDashboardMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuickBite - Canteen Ordering System")
        self.geometry("1280x760")
        self.minsize(1100, 700)
        self.configure(bg=NAVY)
        
        self.current_user = ""
        self.current_role = ""
        self.setup_styles()
        self.cart = {}
        self.last_order = None
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh_table())
        
        self.image_cache = {}
        
        # Show login dialog first
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
                        rowheight=36,
                        fieldbackground=CARD_BG,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background=CARD_BG,
                        foreground=TEXT_MUTED,
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.map("Treeview", background=[("selected", RED_ACCENT)])

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

        # View 4: Monthly Sales Report
        self.views["sales"] = tk.Frame(self.workspace_outer, bg=BG)
        self.build_monthly_sales_content(self.views["sales"])

        if self.current_role == "Canteen staff":
            self.views["verification"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_verification_content(self.views["verification"])

        self.switch_view("order")

    def relogin(self):
        LoginWindow(self, self.switch_account)

    def switch_account(self, username, role):
        self.current_user = username
        self.current_role = role
        self.prof_name_lbl.config(text=username)
        if role == "Canteen staff" and "verification" not in self.views:
            self.views["verification"] = tk.Frame(self.workspace_outer, bg=BG)
            self.build_verification_content(self.views["verification"])
        elif role != "Canteen staff" and "verification" in self.views:
            self.views.pop("verification").destroy()
            if hasattr(self, "pending_tree"):
                del self.pending_tree
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
            ("🍯", "Ingredients Status", "ingredients"),
            ("📊", "Monthly Sales", "sales"),
            ("⚙", "Settings", "settings"),
        ]
        if self.current_role == "Canteen staff":
            nav_items.append(("✓", "Verify Accounts", "verification"))
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
        if key not in self.views:
            return
        if key == "verification" and self.current_role != "Canteen staff":
            messagebox.showerror("Access denied", "Only canteen staff can verify accounts.", parent=self)
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
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
            
        # Toggle right sidebar visibility depending on view
        if key == "order":
            self.right_sidebar.pack(side="right", fill="y", padx=(0, 16), pady=16)
        else:
            self.right_sidebar.pack_forget()

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
        self.refresh_settings_stats()
        self.refresh_pending_accounts()
