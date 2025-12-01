from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from functools import wraps
from datetime import datetime, timedelta
import uuid
import random
import string

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

# ------------------ Demo Data Stores (in-memory) ------------------
INVENTORY = [
    {"id": "1", "name": "Paracetamol 500mg", "sku": "750100010001", "stock": 120, "price": 5.50, "expiry": "2026-01-15", "category": "Analgésico"},
    {"id": "2", "name": "Amoxicilina 250mg", "sku": "750100010002", "stock": 42, "price": 8.75, "expiry": "2025-09-10", "category": "Antibiótico"},
    {"id": "3", "name": "Omeprazol 20mg", "sku": "750100010003", "stock": 12, "price": 7.20, "expiry": "2025-12-01", "category": "Antiácido"},
    {"id": "4", "name": "Loratadina 10mg", "sku": "750100010004", "stock": 0, "price": 6.80, "expiry": "2027-02-01", "category": "Antialérgico"},
    {"id": "5", "name": "Ibuprofeno 400mg", "sku": "750100010005", "stock": 50, "price": 4.50, "expiry": "2026-05-20", "category": "Analgésico"},
]

RECEIPTS = []  # each receipt: {id, datetime, items: [{name, qty, price, subtotal}], total}

# ------------------ Usuarios Demo ------------------
USERS = [
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
        
        # Verificar en la lista de usuarios
        user = next((u for u in USERS if u["username"] == username and u["status"] == "active"), None)
        
        if user and user.get("password") == password:
            session["user"] = {
                "username": user["username"],
                "full_name": user["full_name"],
                "email": user["email"],
                "role": user["role"]
            }
            # Actualizar última conexión
            user["last_login"] = datetime.now().isoformat()
            return redirect(url_for("dashboard"))
        else:
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
    total_items = sum(p["stock"] for p in INVENTORY)
    low_stock = len([p for p in INVENTORY if p["stock"] <= 10])
    today_sales = sum(r["total"] for r in RECEIPTS if datetime.fromisoformat(r["datetime"]).date() == datetime.today().date())
    receipts_count = len(RECEIPTS)
    return render_template("dashboard.html", total_items=total_items, low_stock=low_stock, today_sales=today_sales, receipts_count=receipts_count)

@app.route("/inventory")
@login_required
def inventory():
    return render_template("inventory.html", products=INVENTORY)

@app.route("/sales")
@login_required
def sales():
    return render_template("sales.html", products=INVENTORY)

@app.route("/receipts")
@login_required
def receipts():
    return render_template("receipts.html", receipts=RECEIPTS)

@app.route("/reports")
@login_required
def reports():
    # Aggregate simple metrics for charts
    last7 = {}
    for r in RECEIPTS:
        d = datetime.fromisoformat(r["datetime"]).date()
        last7.setdefault(d.isoformat(), 0)
        last7[d.isoformat()] += r["total"]
    # ensure last 7 days keys exist
    for i in range(6, -1, -1):
        d = (datetime.now().date() - timedelta(days=i)).isoformat()
        last7.setdefault(d, 0)
    labels = list(sorted(last7.keys()))
    values = [last7[k] for k in labels]

    top_products = {}
    for r in RECEIPTS:
        for it in r["items"]:
            top_products[it["name"]] = top_products.get(it["name"], 0) + it["qty"]
    top = sorted(top_products.items(), key=lambda x: x[1], reverse=True)[:5]
    top_labels = [t[0] for t in top]
    top_values = [t[1] for t in top]

    return render_template("reports.html", labels=labels, values=values, top_labels=top_labels, top_values=top_values)

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/barcodes")
@login_required
def barcodes():
    return render_template("barcodes.html", products=INVENTORY)

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
    # No enviar las contraseñas en la respuesta
    safe_users = []
    for user in USERS:
        safe_user = user.copy()
        safe_user.pop('password', None)
        safe_users.append(safe_user)
    return jsonify(safe_users)

@app.post("/api/users")
@login_required
@admin_required
def api_add_user():
    data = request.json or {}
    
    # Validaciones
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    role = data.get("role", "").strip()
    password = data.get("password", "").strip()
    status = data.get("status", "active")
    
    # Validar campos requeridos
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
    
    # Validar unicidad
    if any(u["username"] == username for u in USERS):
        return jsonify({"ok": False, "error": "El nombre de usuario ya existe"}), 400
    
    if any(u["email"] == email for u in USERS):
        return jsonify({"ok": False, "error": "El email ya está registrado"}), 400
    
    # Crear nuevo usuario
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
    
    USERS.append(new_user)
    
    # Devolver usuario sin contraseña
    safe_user = new_user.copy()
    safe_user.pop('password', None)
    
    return jsonify({"ok": True, "user": safe_user})

@app.put("/api/users/<user_id>")
@login_required
@admin_required
def api_update_user(user_id):
    data = request.json or {}
    
    for user in USERS:
        if user["id"] == user_id:
            # Validar que el nuevo username no exista
            new_username = data.get("username", user["username"]).strip()
            if new_username != user["username"] and any(u["username"] == new_username for u in USERS if u["id"] != user_id):
                return jsonify({"ok": False, "error": "El nombre de usuario ya existe"}), 400
            
            # Validar que el nuevo email no exista
            new_email = data.get("email", user["email"]).strip()
            if new_email != user["email"] and any(u["email"] == new_email for u in USERS if u["id"] != user_id):
                return jsonify({"ok": False, "error": "El email ya está registrado"}), 400
            
            # Si se proporciona nueva contraseña, actualizarla
            new_password = data.get("password", "").strip()
            if new_password:
                if len(new_password) < 6:
                    return jsonify({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"}), 400
                user["password"] = new_password
            
            # Actualizar otros campos
            user.update({
                "full_name": data.get("full_name", user["full_name"]).strip(),
                "username": new_username,
                "email": new_email,
                "role": data.get("role", user["role"]).strip(),
                "status": data.get("status", user["status"]),
                "can_manage_users": bool(data.get("can_manage_users", user["can_manage_users"])),
                "can_manage_inventory": bool(data.get("can_manage_inventory", user["can_manage_inventory"])),
                "can_view_reports": bool(data.get("can_view_reports", user["can_view_reports"])),
                "can_export_data": bool(data.get("can_export_data", user["can_export_data"]))
            })
            
            # Devolver usuario sin contraseña
            safe_user = user.copy()
            safe_user.pop('password', None)
            
            return jsonify({"ok": True, "user": safe_user})
    
    abort(404)

@app.delete("/api/users/<user_id>")
@login_required
@admin_required
def api_delete_user(user_id):
    global USERS
    # No permitir eliminar al usuario admin principal
    if user_id == "1":
        return jsonify({"ok": False, "error": "No se puede eliminar el administrador principal"}), 400
    
    before = len(USERS)
    USERS = [u for u in USERS if u["id"] != user_id]
    return jsonify({"ok": True, "deleted": before - len(USERS)})

@app.put("/api/users/<user_id>/toggle-status")
@login_required
@admin_required
def api_toggle_user_status(user_id):
    for user in USERS:
        if user["id"] == user_id:
            # No permitir desactivar al administrador principal
            if user_id == "1":
                return jsonify({"ok": False, "error": "No se puede desactivar el administrador principal"}), 400
            
            user["status"] = "active" if user["status"] == "inactive" else "inactive"
            
            # Devolver usuario sin contraseña
            safe_user = user.copy()
            safe_user.pop('password', None)
            
            return jsonify({"ok": True, "user": safe_user})
    
    abort(404)

@app.post("/api/users/<user_id>/reset-password")
@login_required
@admin_required
def api_reset_password(user_id):
    user = next((u for u in USERS if u["id"] == user_id), None)
    if not user:
        abort(404)
    
    # Generar nueva contraseña aleatoria
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    # Actualizar contraseña
    user["password"] = new_password
    
    email = request.json.get("email", user["email"]) if request.json else user["email"]
    
    return jsonify({
        "ok": True, 
        "message": f"Se ha generado una nueva contraseña. En producción se enviaría al email: {email}",
        "debug_password": new_password  # Solo para debug
    })

# ------------------ API-ish endpoints for demo CRUD ------------------
@app.get("/api/inventory")
@login_required
def api_get_inventory():
    return jsonify(INVENTORY)

@app.post("/api/inventory")
@login_required
def api_add_product():
    data = request.json or {}
    item = {
        "id": str(uuid.uuid4()),
        "name": data.get("name", "Nuevo producto"),
        "sku": data.get("sku", ""),
        "stock": int(data.get("stock", 0)),
        "price": float(data.get("price", 0.0)),
        "expiry": data.get("expiry", ""),
        "category": data.get("category", ""),
    }
    INVENTORY.append(item)
    return jsonify({"ok": True, "item": item})

@app.put("/api/inventory/<pid>")
@login_required
def api_update_product(pid):
    data = request.json or {}
    for p in INVENTORY:
        if p["id"] == pid:
            p.update({
                "name": data.get("name", p["name"]),
                "sku": data.get("sku", p["sku"]),
                "stock": int(data.get("stock", p["stock"])),
                "price": float(data.get("price", p["price"])),
                "expiry": data.get("expiry", p["expiry"]),
                "category": data.get("category", p["category"]),
            })
            return jsonify({"ok": True, "item": p})
    abort(404)

@app.delete("/api/inventory/<pid>")
@login_required
def api_delete_product(pid):
    global INVENTORY
    before = len(INVENTORY)
    INVENTORY = [p for p in INVENTORY if p["id"] != pid]
    return jsonify({"ok": True, "deleted": before - len(INVENTORY)})

@app.post("/api/checkout")
@login_required
def api_checkout():
    data = request.json or {}
    items = data.get("items", [])
    
    # Validar que haya items
    if not items:
        return jsonify({"ok": False, "error": "El carrito está vacío"}), 400
    
    # Actualizar stock
    for it in items:
        for p in INVENTORY:
            if p["id"] == it["id"]:
                qty_to_subtract = int(it["qty"])
                if p["stock"] < qty_to_subtract:
                    return jsonify({"ok": False, "error": f"Stock insuficiente de {it['name']}. Disponible: {p['stock']}"}), 400
                p["stock"] = max(0, p["stock"] - qty_to_subtract)
    
    # Calcular total (sin IVA primero)
    subtotal = sum(float(it["price"]) * int(it["qty"]) for it in items)
    iva = round(subtotal * 0.16, 2)
    total = round(subtotal + iva, 2)
    
    # Crear recibo
    rid = str(uuid.uuid4())
    receipt = {
        "id": rid,
        "datetime": datetime.now().isoformat(),
        "customer": data.get("customer", ""),
        "payment_method": data.get("payment_method", "cash"),
        "items": [
            {
                "name": it["name"], 
                "qty": int(it["qty"]), 
                "price": float(it["price"]), 
                "subtotal": round(float(it["price"]) * int(it["qty"]), 2)
            } 
            for it in items
        ],
        "subtotal": subtotal,
        "iva": iva,
        "total": total
    }
    
    # Guardar recibo al inicio de la lista (más recientes primero)
    RECEIPTS.insert(0, receipt)
    
    return jsonify({
        "ok": True, 
        "receipt_id": rid,
        "total": total,
        "message": "Venta procesada exitosamente"
    })

@app.get("/receipt/<rid>")
@login_required
def view_receipt(rid):
    for r in RECEIPTS:
        if r["id"] == rid:
            return render_template("receipt_print.html", r=r)
    abort(404)

# ------------------ Error handlers ------------------
@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)