import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime

ACCOUNT_ROLES = ("Teacher", "Student", "Canteen staff")
VERIFICATION_PENDING = "Pending"
VERIFICATION_ACCEPTED = "Accepted"
VERIFICATION_DECLINED = "Declined"


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
                if i["stock"] >= self.settings["high_threshold"]:
                    i["status"] = "High"
                elif i["stock"] > self.settings["low_threshold"]:
                    i["status"] = "Normal"
                elif i["stock"] > 0:
                    i["status"] = "Low Stock"
        # Update linked menu items stock
        for m in self.menu:
            if m["ingredient_id"] == ing_id:
                ing = next(i for i in self.ingredients if i["id"] == ing_id)
                m["stock"] = ing["stock"]
                m["status"] = (
                    "Out of Stock" if m["stock"] == 0
                    else "Low Stock" if m["stock"] <= self.settings["low_threshold"]
                    else "Available"
                )

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
            m["status"] = (
                "Out of Stock" if m["stock"] == 0
                else "Low Stock" if m["stock"] <= self.settings["low_threshold"]
                else "Available"
            )

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

    def get_monthly_sales(self, year, month):
        sales_by_item = {}
        for order in self.orders:
            order_date = datetime.strptime(order["created_at"], "%Y-%m-%d %H:%M:%S")
            if order_date.year != year or order_date.month != month:
                continue
            for item in order["items"]:
                name = item["name"]
                sales = sales_by_item.setdefault(name, {"quantity": 0, "revenue": 0})
                sales["quantity"] += item["quantity"]
                sales["revenue"] += item["quantity"] * item["price"]
        return [
            {"name": name, **sales}
            for name, sales in sorted(sales_by_item.items())
        ]

    def clear_orders(self):
        self.orders.clear()


class AccountStore:
    def __init__(self):
        self.path = os.path.join(os.path.expanduser("~"), ".quickbite_accounts.json")

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as account_file:
                accounts = json.load(account_file)
        except FileNotFoundError:
            return {}

        if not isinstance(accounts, dict):
            raise ValueError("The account file has an invalid format.")
        migrated = False
        for username, account in accounts.items():
            if (not isinstance(username, str) or not isinstance(account, dict)
                    or not isinstance(account.get("salt"), str)
                    or not isinstance(account.get("password_hash"), str)):
                raise ValueError("The account file has an invalid format.")
            if "role" not in account:
                account["role"] = "Student"
                migrated = True
            if "verification_status" not in account:
                account["verification_status"] = VERIFICATION_PENDING
                migrated = True
            if (account["role"] not in ACCOUNT_ROLES
                    or account["verification_status"] not in (
                        VERIFICATION_PENDING,
                        VERIFICATION_ACCEPTED,
                        VERIFICATION_DECLINED,
                    )):
                raise ValueError("The account file has an invalid format.")
            try:
                bytes.fromhex(account["salt"])
                bytes.fromhex(account["password_hash"])
            except ValueError as error:
                raise ValueError("The account file has an invalid format.") from error
        if migrated:
            self._save(accounts)
        return accounts

    def _save(self, accounts):
        with open(self.path, "w", encoding="utf-8") as account_file:
            json.dump(accounts, account_file)

    def register(self, username, password, role):
        accounts = self._load()
        key = username.casefold()
        if key in accounts:
            raise ValueError("That username is already registered.")
        if role not in ACCOUNT_ROLES:
            raise ValueError("Please select a valid account role.")

        salt = secrets.token_bytes(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, 200_000
        )
        accounts[key] = {
            "salt": salt.hex(),
            "password_hash": password_hash.hex(),
            "role": role,
            "verification_status": VERIFICATION_PENDING,
        }
        self._save(accounts)

    def authenticate(self, username, password):
        account = self._load().get(username.casefold())
        if account is None:
            return None
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(account["salt"]),
            200_000,
        )
        if not hmac.compare_digest(candidate, bytes.fromhex(account["password_hash"])):
            return None
        return account

    def get_pending_accounts(self):
        return [
            {"username": username, **account}
            for username, account in self._load().items()
            if account["verification_status"] == VERIFICATION_PENDING
        ]

    def update_verification(self, reviewer, username, status):
        if status not in (VERIFICATION_ACCEPTED, VERIFICATION_DECLINED):
            raise ValueError("Invalid verification status.")

        stored_accounts = self._load()
        reviewer_key = reviewer.casefold()
        account_key = username.casefold()
        reviewer_account = stored_accounts.get(reviewer_key)
        account = stored_accounts.get(account_key)

        if reviewer_account is None or reviewer_account["role"] != "Canteen staff":
            raise ValueError("Only canteen staff can review accounts.")
        if account is None:
            raise ValueError("The selected account no longer exists.")
        if reviewer_key == account_key:
            raise ValueError("You cannot review your own account.")
        if account["verification_status"] != VERIFICATION_PENDING:
            raise ValueError("The selected account is no longer pending.")

        account["verification_status"] = status
        self._save(stored_accounts)

db = InMemoryDB()
accounts = AccountStore()
