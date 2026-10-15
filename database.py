import sqlite3
from datetime import datetime
 
DB_NAME = "quickbite.db"
 
 
def connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
 
 
def init_db():
    """Create tables and seed sample data on first run."""
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL UNIQUE,
            quantity   INTEGER NOT NULL DEFAULT 0,
            low_level  INTEGER NOT NULL DEFAULT 10,   -- at or below = Low Stock
            high_level INTEGER NOT NULL DEFAULT 50    -- at or above = High
        );
 
        CREATE TABLE IF NOT EXISTS menu_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL UNIQUE,
            category      TEXT NOT NULL,
            price         REAL NOT NULL CHECK (price >= 0),
            ingredient_id INTEGER REFERENCES ingredients(id)
        );
 
        CREATE TABLE IF NOT EXISTS orders (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            total      REAL NOT NULL,
            created_at TEXT NOT NULL
        );
 
        -- name/price are copied so old receipts survive menu edits or deletes
        CREATE TABLE IF NOT EXISTS order_items (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            name     TEXT NOT NULL,
            price    REAL NOT NULL,
            quantity INTEGER NOT NULL
        );
        """)
        if conn.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0] == 0:
            _seed(conn)
 
 
def _seed(conn):
    conn.executemany(
        "INSERT INTO ingredients (name, quantity, low_level, high_level) VALUES (?,?,?,?)",
        [("Chicken", 30, 10, 50), ("Pork", 8, 10, 50), ("Noodles", 40, 10, 50),
         ("Vegetables", 60, 10, 50), ("Oil", 25, 10, 50)])
    ids = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM ingredients")}
    conn.executemany(
        "INSERT INTO menu_items (name, category, price, ingredient_id) VALUES (?,?,?,?)",
        [("Adobo", "Main Dish", 95, ids["Chicken"]),
         ("Sinigang", "Soup", 110, ids["Pork"]),
         ("Pancit", "Noodles", 85, ids["Noodles"]),
         ("Lumpia", "Snack", 15, ids["Vegetables"])])
 
 
# ---------- status helpers ----------
def item_status(qty, low):
    if qty <= 0:
        return "Out of Stock"
    return "Low Stock" if qty <= low else "Available"
 
 
def ingredient_status(qty, low, high):
    if qty <= low:
        return "Low Stock"
    return "High" if qty >= high else "Normal"
 
 
# ---------- menu ----------
def get_menu(search=""):
    sql = """SELECT m.id, m.name, m.category, m.price, m.ingredient_id,
                    i.quantity AS stock, i.low_level
             FROM menu_items m LEFT JOIN ingredients i ON i.id = m.ingredient_id
             WHERE m.name LIKE ? OR m.category LIKE ?
             ORDER BY m.id"""
    like = f"%{search}%"
    with connect() as conn:
        rows = conn.execute(sql, (like, like)).fetchall()
    menu = []
    for r in rows:
        d = dict(r)
        d["stock"] = d["stock"] if d["stock"] is not None else 999
        d["status"] = item_status(d["stock"], d["low_level"] or 0)
        menu.append(d)
    return menu
 
 
def add_item(name, category, price, ingredient_id):
    with connect() as conn:
        conn.execute("INSERT INTO menu_items (name, category, price, ingredient_id) VALUES (?,?,?,?)",
                     (name, category, price, ingredient_id))
 
 
def update_item(item_id, name, category, price, ingredient_id):
    with connect() as conn:
        conn.execute("UPDATE menu_items SET name=?, category=?, price=?, ingredient_id=? WHERE id=?",
                     (name, category, price, ingredient_id, item_id))
 
 
def delete_item(item_id):
    with connect() as conn:
        conn.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
 
 
# ---------- ingredients ----------
def get_ingredients():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM ingredients ORDER BY name").fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["status"] = ingredient_status(d["quantity"], d["low_level"], d["high_level"])
        result.append(d)
    return result
 
 
def restock(ingredient_id, amount):
    with connect() as conn:
        conn.execute("UPDATE ingredients SET quantity = quantity + ? WHERE id=?", (amount, ingredient_id))
 
 
# ---------- orders ----------
def save_order(cart):
    """cart: {item_id: qty}. Saves the order and deducts ingredient stock.
    Raises ValueError if any item lacks stock. Returns the new order id."""
    with connect() as conn:
        lines, total = [], 0.0
        for item_id, qty in cart.items():
            r = conn.execute("""SELECT m.name, m.price, m.ingredient_id, i.quantity
                                FROM menu_items m LEFT JOIN ingredients i ON i.id = m.ingredient_id
                                WHERE m.id=?""", (item_id,)).fetchone()
            if r is None:
                raise ValueError("An item in your order no longer exists.")
            if r["ingredient_id"] is not None and r["quantity"] < qty:
                raise ValueError(f"Not enough stock for {r['name']}.")
            lines.append((item_id, r["name"], r["price"], qty, r["ingredient_id"]))
            total += r["price"] * qty
 
        cur = conn.execute("INSERT INTO orders (total, created_at) VALUES (?,?)",
                           (total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        order_id = cur.lastrowid
        for _, name, price, qty, ing_id in lines:
            conn.execute("INSERT INTO order_items (order_id, name, price, quantity) VALUES (?,?,?,?)",
                         (order_id, name, price, qty))
            if ing_id is not None:
                conn.execute("UPDATE ingredients SET quantity = quantity - ? WHERE id=?", (qty, ing_id))
        return order_id
 
 
def get_order(order_id):
    with connect() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        items = conn.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    return dict(order), [dict(i) for i in items]