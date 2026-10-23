import tkinter as tk
from tkinter import ttk, messagebox

from database import ACCOUNT_ROLES, accounts
from ui_theme import GOLD, NAVY, ORANGE


class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.title("QuickBite - Login or Register")
        self.geometry("460x360")
        self.configure(bg=NAVY)
        self.resizable(False, False)
        self.on_success = on_success
        self.mode = "login"
        
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        
        tk.Label(self, text="QUICKBITE", bg=NAVY, fg="white", font=("Segoe UI", 16, "bold")).pack(pady=(18, 4))
        tk.Label(self, text="Canteen Ordering System", bg=NAVY, fg=GOLD, font=("Segoe UI", 9)).pack(pady=(0, 16))
        
        form_frame = tk.Frame(self, bg=NAVY)
        form_frame.pack(padx=30, fill="x")

        tk.Label(form_frame, text="Username", bg=NAVY, fg="white", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.user_entry = ttk.Entry(form_frame, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(0, 14), ipady=3)

        self.role_label = tk.Label(form_frame, text="Role", bg=NAVY, fg="white", font=("Segoe UI", 9))
        self.role_var = tk.StringVar()
        self.role_select = ttk.Combobox(
            form_frame, textvariable=self.role_var, values=ACCOUNT_ROLES,
            state="readonly", font=("Segoe UI", 10),
        )
        self.role_label.pack_forget()
        self.role_select.pack_forget()

        self.pass_label = tk.Label(form_frame, text="Password", bg=NAVY, fg="white", font=("Segoe UI", 9))
        self.pass_label.pack(anchor="w", pady=(0, 4))
        self.pass_entry, self.pass_toggle = self.create_password_toggle(form_frame)

        self.confirm_label = tk.Label(form_frame, text="Confirm password", bg=NAVY, fg="white", font=("Segoe UI", 9))
        self.confirm_entry, self.confirm_toggle = self.create_password_toggle(form_frame)
        self.confirm_label.pack_forget()
        self.confirm_toggle.master.pack_forget()

        self.action_button = tk.Button(
            self, text="Login", bg=ORANGE, fg="white",
            font=("Segoe UI", 10, "bold"), relief="flat",
            cursor="hand2", command=self.submit,
        )
        self.action_button.pack(fill="x", padx=30, pady=(8, 0), ipady=5)
        self.mode_button = tk.Button(
            self, text="Need an account? Register", bg=NAVY, fg=GOLD,
            font=("Segoe UI", 9), relief="flat", cursor="hand2",
            command=self.toggle_mode,
        )
        self.mode_button.pack(pady=(8, 12))

    def create_password_toggle(self, parent):
        row = tk.Frame(parent, bg=NAVY)
        row.pack(fill="x", pady=(0, 14))
        entry = ttk.Entry(row, show="*", font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True)
        toggle = tk.Button(
            row, text="Show", bg=NAVY, fg=GOLD,
            font=("Segoe UI", 8), relief="flat", cursor="hand2",
            command=lambda: self.toggle_password(entry, toggle),
        )
        toggle.pack(side="right", padx=(8, 0))
        return entry, toggle

    @staticmethod
    def toggle_password(entry, toggle):
        if entry.cget("show"):
            entry.configure(show="")
            toggle.configure(text="Hide")
        else:
            entry.configure(show="*")
            toggle.configure(text="Show")

    def toggle_mode(self):
        if self.mode == "login":
            self.mode = "register"
            self.title("QuickBite - Register")
            self.geometry("460x480")
            self.role_label.pack(before=self.pass_label, anchor="w", pady=(0, 4))
            self.role_select.pack(before=self.pass_label, fill="x", pady=(0, 14), ipady=3)
            self.confirm_label.pack(anchor="w", pady=(0, 4))
            self.confirm_toggle.master.pack(fill="x", pady=(0, 4))
            self.action_button.config(text="Create Account")
            self.mode_button.config(text="Already registered? Login")
        else:
            self.mode = "login"
            self.title("QuickBite - Login")
            self.geometry("460x360")
            self.role_label.pack_forget()
            self.role_select.pack_forget()
            self.confirm_label.pack_forget()
            self.confirm_toggle.master.pack_forget()
            self.action_button.config(text="Login")
            self.mode_button.config(text="Need an account? Register")

    def submit(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get()
        if self.mode == "register":
            if not u:
                messagebox.showerror("Error", "Please enter a username.", parent=self)
                return
            role = self.role_var.get()
            if role not in ACCOUNT_ROLES:
                messagebox.showerror("Error", "Please select a role.", parent=self)
                return
            if len(p) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters long.", parent=self)
                return
            if not any(not character.isalnum() and not character.isspace() for character in p):
                messagebox.showerror("Error", "Password must include at least one special symbol.", parent=self)
                return
            if p != self.confirm_entry.get():
                messagebox.showerror("Error", "Passwords do not match.", parent=self)
                return
            try:
                accounts.register(u, p, role)
            except (OSError, ValueError) as error:
                messagebox.showerror("Registration failed", str(error), parent=self)
                return
        else:
            if not u or not p:
                messagebox.showerror("Error", "Please enter your username and password.", parent=self)
                return
            try:
                account = accounts.authenticate(u, p)
            except (OSError, ValueError) as error:
                messagebox.showerror("Login failed", str(error), parent=self)
                return
            if account is None:
                messagebox.showerror("Login failed", "Incorrect username or password.", parent=self)
                return
            role = account["role"]

        self.grab_release()
        self.destroy()
        self.on_success(u, role)

    def close_app(self):
        self.grab_release()
        self.destroy()
        self.master.destroy()
