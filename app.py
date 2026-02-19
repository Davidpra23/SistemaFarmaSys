from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort, g
from functools import wraps
from datetime import datetime, timedelta
import uuid
import random
import string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

DB_PATH = os.path.join(os.path.dirname(__file__), "farmasys.db")

SEED_INVENTORY = [
    {"id": "1", "name": "Paracetamol 500mg", "sku": "750100010001", "stock": 120, "price": 5.50, "expiry": "2026-01-15", "category": "Analgésico"},
    {"id": "2", "name": "Amoxicilina 250mg", "sku": "750100010002", "stock": 42, "price": 8.75, "expiry": "2025-09-10", "category": "Antibiótico"},
    {"id": "3", "name": "Omeprazol 20mg", "sku": "750100010003", "stock": 12, "price": 7.20, "expiry": "2025-12-01", "category": "Antiácido"},
    {"id": "4", "name": "Loratadina 10mg", "sku": "750100010004", "stock": 0, "price": 6.80, "expiry": "2027-02-01", "category": "Antialérgico"},
    {"id": "5", "name": "Ibuprofeno 400mg", "sku": "750100010005", "stock": 50, "price": 4.50, "expiry": "2026-05-20", "category": "Analgésico"},
]

SEED_USERS = [
    {
        "id": "1",
        "full_name": "Administrador Principal",
        "username": "admin",
        "email": "admin@farmacia.com",
        "role": "admin",
        "status": "active",
        "password": "123",
        "last_login": datetime.now().isoformat(),
        "can_manage_users": True,
        "can_manage_inventory": True,
        "can_view_reports": True,
        "can_export_data": True,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "2",
        "full_name": "María González",
        "username": "maria.gonzalez",
        "email": "maria@farmacia.com",
        "role": "farmacia",
        "status": "active",
        "password": "123",
        "last_login": (datetime.now() - timedelta(days=1)).isoformat(),
        "can_manage_users": False,
        "can_manage_inventory": True,
        "can_view_reports": True,
        "can_export_data": False,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "3",
        "full_name": "Carlos Rodríguez",
        "username": "carlos.rodriguez",
        "email": "carlos@farmacia.com",
        "role": "ventas",
        "status": "active",
        "password": "123",
        "last_login": (datetime.now() - timedelta(days=2)).isoformat(),
        "can_manage_users": False,
        "can_manage_inventory": False,
        "can_view_reports": True,
        "can_export_data": True,
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "4",
        "full_name": "Laura Martínez",
        "username": "laura.martinez",
        "email": "laura@farmacia.com",
        "role": "inventario",
        "status": "inactive",
        "password": "123",
        "last_login": (datetime.now() - timedelta(days=5)).isoformat(),
        "can_manage_users": False,
        "can_manage_inventory": True,
        "can_view_reports": False,
        "can_export_data": False,
        "created_at": datetime.now().isoformat()
    }
]


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            password TEXT NOT NULL,
            last_login TEXT,
            can_manage_users INTEGER NOT NULL DEFAULT 0,
            can_manage_inventory INTEGER NOT NULL DEFAULT 0,
            can_view_reports INTEGER NOT NULL DEFAULT 0,
            can_export_data INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            sku TEXT NOT NULL UNIQUE,
            stock INTEGER NOT NULL DEFAULT 0,
            price REAL NOT NULL DEFAULT 0,
            expiry TEXT,
            category TEXT
        );
        CREATE TABLE IF NOT EXISTS receipts (
            id TEXT PRIMARY KEY,
            datetime TEXT NOT NULL,
            customer TEXT,
            payment_method TEXT,
            subtotal REAL NOT NULL DEFAULT 0,
            iva REAL NOT NULL DEFAULT 0,
            total REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS receipt_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_id TEXT NOT NULL,
            name TEXT NOT NULL,
            qty INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
        );
        """
    )

    users_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if users_count == 0:
        conn.executemany(
            """
            INSERT INTO users (
                id, full_name, username, email, role, status, password,
                last_login, can_manage_users, can_manage_inventory,
                can_view_reports, can_export_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    u["id"], u["full_name"], u["username"], u["email"], u["role"], u["status"],
                    u["password"], u["last_login"], int(u["can_manage_users"]), int(u["can_manage_inventory"]),
                    int(u["can_view_reports"]), int(u["can_export_data"]), u["created_at"]
                )
                for u in SEED_USERS
            ]
        )

    inventory_count = conn.execute("SELECT COUNT(*) AS c FROM inventory").fetchone()["c"]
    if inventory_count == 0:
        conn.executemany(
            """
            INSERT INTO inventory (
                id, name, sku, stock, price, expiry, category
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    p["id"], p["name"], p["sku"], int(p["stock"]), float(p["price"]),
                    p["expiry"], p["category"]
                )
                for p in SEED_INVENTORY
            ]
        )

    conn.commit()
    conn.close()


def get_receipts_with_items(conn):
    receipts = [dict(r) for r in conn.execute("SELECT * FROM receipts ORDER BY datetime DESC").fetchall()]
    if not receipts:
        return []

    receipt_ids = [r["id"] for r in receipts]
    placeholders = ",".join("?" for _ in receipt_ids)
    items_rows = conn.execute(
        f"SELECT receipt_id, name, qty, price, subtotal FROM receipt_items WHERE receipt_id IN ({placeholders}) ORDER BY id",
        receipt_ids
    ).fetchall()

    items_by_receipt = {}
    for it in items_rows:
        items_by_receipt.setdefault(it["receipt_id"], []).append(dict(it))

    for r in receipts:
        r["items"] = items_by_receipt.get(r["id"], [])

    return receipts

# ------------------ Auth ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = session.get("user", {})
        if not user:
            return redirect(url_for("login", next=request.path))
        if user.get("role") != "admin":
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? AND status = 'active'",
            (username,)
        ).fetchone()

        if row and row["password"] == password:
            session["user"] = {
                "username": row["username"],
                "full_name": row["full_name"],
                "email": row["email"],
                "role": row["role"]
            }
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), row["id"])
            )
            conn.commit()
            return redirect(url_for("dashboard"))

        error = "Credenciales inválidas. Usa admin / 123 para probar."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ------------------ Pages ------------------
@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    total_items = conn.execute("SELECT COALESCE(SUM(stock), 0) AS total FROM inventory").fetchone()["total"]
    low_stock = conn.execute("SELECT COUNT(*) AS c FROM inventory WHERE stock <= 10").fetchone()["c"]
    today = datetime.now().date().isoformat()
    today_sales = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS total FROM receipts WHERE substr(datetime, 1, 10) = ?",
        (today,)
    ).fetchone()["total"]
    receipts_count = conn.execute("SELECT COUNT(*) AS c FROM receipts").fetchone()["c"]
    return render_template(
        "dashboard.html",
        total_items=total_items,
        low_stock=low_stock,
        today_sales=today_sales,
        receipts_count=receipts_count
    )

@app.route("/inventory")
@login_required
def inventory():
    return render_template("inventory.html")

@app.route("/sales")
@login_required
def sales():
    conn = get_db()
    products = [dict(p) for p in conn.execute("SELECT * FROM inventory ORDER BY name").fetchall()]
    return render_template("sales.html", products=products)

@app.route("/receipts")
@login_required
def receipts():
    conn = get_db()
    receipts_list = get_receipts_with_items(conn)
    return render_template("receipts.html", receipts=receipts_list)

@app.route("/reports")
@login_required
def reports():
    conn = get_db()

    last7 = {}
    for i in range(6, -1, -1):
        d = (datetime.now().date() - timedelta(days=i)).isoformat()
        last7.setdefault(d, 0)

    start_date = (datetime.now().date() - timedelta(days=6)).isoformat()
    rows = conn.execute(
        """
        SELECT substr(datetime, 1, 10) AS d, SUM(total) AS total
        FROM receipts
        WHERE datetime >= ?
        GROUP BY d
        """,
        (start_date,)
    ).fetchall()

    for row in rows:
        last7[row["d"]] = row["total"] or 0

    labels = list(sorted(last7.keys()))
    values = [last7[k] for k in labels]

    top_rows = conn.execute(
        """
        SELECT name, SUM(qty) AS qty
        FROM receipt_items
        GROUP BY name
        ORDER BY qty DESC
        LIMIT 5
        """
    ).fetchall()

    top_labels = [r["name"] for r in top_rows]
    top_values = [r["qty"] for r in top_rows]

    return render_template(
        "reports.html",
        labels=labels,
        values=values,
        top_labels=top_labels,
        top_values=top_values
    )

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/barcodes")
@login_required
def barcodes():
    conn = get_db()
    products = [dict(p) for p in conn.execute("SELECT * FROM inventory ORDER BY name").fetchall()]
    return render_template("barcodes.html", products=products)

# ------------------ Gestión de Usuarios ------------------
@app.route("/users")
@login_required
@admin_required
def users():
    return render_template("users.html")

# ------------------ API para Gestión de Usuarios ------------------
@app.get("/api/users")
@login_required
@admin_required
def api_get_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    safe_users = []
    for row in rows:
        user = dict(row)
        user.pop("password", None)
        user["can_manage_users"] = bool(user["can_manage_users"])
        user["can_manage_inventory"] = bool(user["can_manage_inventory"])
        user["can_view_reports"] = bool(user["can_view_reports"])
        user["can_export_data"] = bool(user["can_export_data"])
        safe_users.append(user)
    return jsonify(safe_users)

@app.post("/api/users")
@login_required
@admin_required
def api_add_user():
    data = request.json or {}

    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    role = data.get("role", "").strip()
    password = data.get("password", "").strip()
    status = data.get("status", "active")

    if not full_name or len(full_name) < 3:
        return jsonify({"ok": False, "error": "El nombre completo debe tener al menos 3 caracteres"}), 400

    if not username or len(username) < 3:
        return jsonify({"ok": False, "error": "El nombre de usuario debe tener al menos 3 caracteres"}), 400

    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Email inválido"}), 400

    if not role:
        return jsonify({"ok": False, "error": "Debe seleccionar un rol"}), 400

    if not password or len(password) < 6:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

    conn = get_db()
    if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        return jsonify({"ok": False, "error": "El nombre de usuario ya existe"}), 400

    if conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        return jsonify({"ok": False, "error": "El email ya está registrado"}), 400

    new_user = {
        "id": str(uuid.uuid4()),
        "full_name": full_name,
        "username": username,
        "email": email,
        "role": role,
        "status": status,
        "password": password,
        "last_login": None,
        "can_manage_users": bool(data.get("can_manage_users", False)),
        "can_manage_inventory": bool(data.get("can_manage_inventory", False)),
        "can_view_reports": bool(data.get("can_view_reports", False)),
        "can_export_data": bool(data.get("can_export_data", False)),
        "created_at": datetime.now().isoformat()
    }

    conn.execute(
        """
        INSERT INTO users (
            id, full_name, username, email, role, status, password,
            last_login, can_manage_users, can_manage_inventory,
            can_view_reports, can_export_data, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_user["id"], new_user["full_name"], new_user["username"], new_user["email"], new_user["role"],
            new_user["status"], new_user["password"], new_user["last_login"], int(new_user["can_manage_users"]),
            int(new_user["can_manage_inventory"]), int(new_user["can_view_reports"]),
            int(new_user["can_export_data"]), new_user["created_at"]
        )
    )
    conn.commit()

    safe_user = new_user.copy()
    safe_user.pop("password", None)

    return jsonify({"ok": True, "user": safe_user})

@app.put("/api/users/<user_id>")
@login_required
@admin_required
def api_update_user(user_id):
    data = request.json or {}
    conn = get_db()

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        abort(404)

    new_username = data.get("username", user["username"]).strip()
    if new_username != user["username"] and conn.execute(
        "SELECT 1 FROM users WHERE username = ? AND id != ?",
        (new_username, user_id)
    ).fetchone():
        return jsonify({"ok": False, "error": "El nombre de usuario ya existe"}), 400

    new_email = data.get("email", user["email"]).strip()
    if new_email != user["email"] and conn.execute(
        "SELECT 1 FROM users WHERE email = ? AND id != ?",
        (new_email, user_id)
    ).fetchone():
        return jsonify({"ok": False, "error": "El email ya está registrado"}), 400

    new_password = data.get("password", "").strip()
    if new_password and len(new_password) < 6:
        return jsonify({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400

    conn.execute(
        """
        UPDATE users
        SET full_name = ?, username = ?, email = ?, role = ?, status = ?,
            can_manage_users = ?, can_manage_inventory = ?, can_view_reports = ?,
            can_export_data = ?
            {password_clause}
        WHERE id = ?
        """.format(password_clause=", password = ?" if new_password else ""),
        (
            data.get("full_name", user["full_name"]).strip(),
            new_username,
            new_email,
            data.get("role", user["role"]).strip(),
            data.get("status", user["status"]),
            int(bool(data.get("can_manage_users", user["can_manage_users"]))),
            int(bool(data.get("can_manage_inventory", user["can_manage_inventory"]))),
            int(bool(data.get("can_view_reports", user["can_view_reports"]))),
            int(bool(data.get("can_export_data", user["can_export_data"]))),
            *( [new_password] if new_password else [] ),
            user_id
        )
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    safe_user = dict(updated)
    safe_user.pop("password", None)
    safe_user["can_manage_users"] = bool(safe_user["can_manage_users"])
    safe_user["can_manage_inventory"] = bool(safe_user["can_manage_inventory"])
    safe_user["can_view_reports"] = bool(safe_user["can_view_reports"])
    safe_user["can_export_data"] = bool(safe_user["can_export_data"])

    return jsonify({"ok": True, "user": safe_user})

@app.delete("/api/users/<user_id>")
@login_required
@admin_required
def api_delete_user(user_id):
    if user_id == "1":
        return jsonify({"ok": False, "error": "No se puede eliminar el administrador principal"}), 400

    conn = get_db()
    res = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return jsonify({"ok": True, "deleted": res.rowcount})

@app.put("/api/users/<user_id>/toggle-status")
@login_required
@admin_required
def api_toggle_user_status(user_id):
    if user_id == "1":
        return jsonify({"ok": False, "error": "No se puede desactivar el administrador principal"}), 400

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        abort(404)

    new_status = "active" if user["status"] == "inactive" else "inactive"
    conn.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    conn.commit()

    updated = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    safe_user = dict(updated)
    safe_user.pop("password", None)
    safe_user["can_manage_users"] = bool(safe_user["can_manage_users"])
    safe_user["can_manage_inventory"] = bool(safe_user["can_manage_inventory"])
    safe_user["can_view_reports"] = bool(safe_user["can_view_reports"])
    safe_user["can_export_data"] = bool(safe_user["can_export_data"])

    return jsonify({"ok": True, "user": safe_user})

@app.post("/api/users/<user_id>/reset-password")
@login_required
@admin_required
def api_reset_password(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        abort(404)

    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    conn.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()

    email = request.json.get("email", user["email"]) if request.json else user["email"]

    return jsonify({
        "ok": True,
        "message": f"Se ha generado una nueva contraseña. En producción se enviaría al email: {email}",
        "debug_password": new_password
    })

# ------------------ API-ish endpoints for demo CRUD ------------------
@app.get("/api/inventory")
@login_required
def api_get_inventory():
    conn = get_db()
    rows = conn.execute("SELECT * FROM inventory ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/inventory")
@login_required
def api_add_product():
    data = request.json or {}
    sku = data.get("sku", "").strip()
    name = data.get("name", "Nuevo producto").strip()

    conn = get_db()
    if sku and conn.execute("SELECT 1 FROM inventory WHERE sku = ?", (sku,)).fetchone():
        return jsonify({"ok": False, "error": "El SKU ya existe"}), 400

    item = {
        "id": str(uuid.uuid4()),
        "name": name,
        "sku": sku,
        "stock": int(data.get("stock", 0)),
        "price": float(data.get("price", 0.0)),
        "expiry": data.get("expiry", ""),
        "category": data.get("category", ""),
    }

    conn.execute(
        """
        INSERT INTO inventory (id, name, sku, stock, price, expiry, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["id"], item["name"], item["sku"], item["stock"], item["price"],
            item["expiry"], item["category"]
        )
    )
    conn.commit()

    return jsonify({"ok": True, "item": item})

@app.put("/api/inventory/<pid>")
@login_required
def api_update_product(pid):
    data = request.json or {}
    conn = get_db()

    existing = conn.execute("SELECT * FROM inventory WHERE id = ?", (pid,)).fetchone()
    if not existing:
        abort(404)

    new_sku = data.get("sku", existing["sku"]).strip()
    if new_sku != existing["sku"] and conn.execute(
        "SELECT 1 FROM inventory WHERE sku = ? AND id != ?",
        (new_sku, pid)
    ).fetchone():
        return jsonify({"ok": False, "error": "El SKU ya existe"}), 400

    conn.execute(
        """
        UPDATE inventory
        SET name = ?, sku = ?, stock = ?, price = ?, expiry = ?, category = ?
        WHERE id = ?
        """,
        (
            data.get("name", existing["name"]),
            new_sku,
            int(data.get("stock", existing["stock"])),
            float(data.get("price", existing["price"])),
            data.get("expiry", existing["expiry"]),
            data.get("category", existing["category"]),
            pid
        )
    )
    conn.commit()

    updated = conn.execute("SELECT * FROM inventory WHERE id = ?", (pid,)).fetchone()
    return jsonify({"ok": True, "item": dict(updated)})

@app.delete("/api/inventory/<pid>")
@login_required
def api_delete_product(pid):
    conn = get_db()
    res = conn.execute("DELETE FROM inventory WHERE id = ?", (pid,))
    conn.commit()
    return jsonify({"ok": True, "deleted": res.rowcount})

@app.post("/api/checkout")
@login_required
def api_checkout():
    data = request.json or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"ok": False, "error": "El carrito está vacío"}), 400

    qty_by_id = {}
    for it in items:
        pid = str(it.get("id", "")).strip()
        if not pid:
            continue
        try:
            qty = int(it.get("qty", 0))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "Cantidad inválida"}), 400
        if qty <= 0:
            return jsonify({"ok": False, "error": "Cantidad inválida"}), 400
        qty_by_id[pid] = qty_by_id.get(pid, 0) + qty

    if not qty_by_id:
        return jsonify({"ok": False, "error": "El carrito está vacío"}), 400

    conn = get_db()
    placeholders = ",".join("?" for _ in qty_by_id)
    products = conn.execute(
        f"SELECT id, name, stock, price FROM inventory WHERE id IN ({placeholders})",
        list(qty_by_id.keys())
    ).fetchall()

    if len(products) != len(qty_by_id):
        return jsonify({"ok": False, "error": "Producto no encontrado"}), 400

    products_by_id = {p["id"]: p for p in products}

    for pid, qty in qty_by_id.items():
        product = products_by_id[pid]
        if product["stock"] < qty:
            return jsonify({
                "ok": False,
                "error": f"Stock insuficiente de {product['name']}. Disponible: {product['stock']}"
            }), 400

    receipt_items = []
    subtotal = 0.0
    for pid, qty in qty_by_id.items():
        product = products_by_id[pid]
        price = float(product["price"])
        line_total = round(price * qty, 2)
        subtotal += line_total
        receipt_items.append({
            "name": product["name"],
            "qty": qty,
            "price": price,
            "subtotal": line_total
        })

    iva = round(subtotal * 0.16, 2)
    total = round(subtotal + iva, 2)
    rid = str(uuid.uuid4())

    try:
        conn.execute("BEGIN")
        for pid, qty in qty_by_id.items():
            conn.execute(
                "UPDATE inventory SET stock = stock - ? WHERE id = ?",
                (qty, pid)
            )

        conn.execute(
            """
            INSERT INTO receipts (id, datetime, customer, payment_method, subtotal, iva, total)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rid,
                datetime.now().isoformat(),
                data.get("customer", ""),
                data.get("payment_method", "cash"),
                subtotal,
                iva,
                total
            )
        )

        conn.executemany(
            """
            INSERT INTO receipt_items (receipt_id, name, qty, price, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (rid, it["name"], it["qty"], it["price"], it["subtotal"])
                for it in receipt_items
            ]
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return jsonify({
        "ok": True,
        "receipt_id": rid,
        "total": total,
        "message": "Venta procesada exitosamente"
    })

@app.get("/receipt/<rid>")
@login_required
def view_receipt(rid):
    conn = get_db()
    receipt = conn.execute("SELECT * FROM receipts WHERE id = ?", (rid,)).fetchone()
    if not receipt:
        abort(404)

    items = conn.execute(
        "SELECT name, qty, price, subtotal FROM receipt_items WHERE receipt_id = ? ORDER BY id",
        (rid,)
    ).fetchall()

    receipt_dict = dict(receipt)
    receipt_dict["items"] = [dict(it) for it in items]
    return render_template("receipt_print.html", r=receipt_dict)

# ------------------ Error handlers ------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)