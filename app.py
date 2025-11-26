
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from functools import wraps
from datetime import datetime, timedelta
import uuid

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

# ------------------ Auth ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "admin" and password == "123":
            session["user"] = {"username": "admin"}
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
    # Update stock
    for it in items:
        for p in INVENTORY:
            if p["id"] == it["id"]:
                p["stock"] = max(0, p["stock"] - int(it["qty"]))
    total = sum(float(it["price"]) * int(it["qty"]) for it in items)
    rid = str(uuid.uuid4())
    receipt = {
        "id": rid,
        "datetime": datetime.now().isoformat(),
        "items": [{"name": it["name"], "qty": int(it["qty"]), "price": float(it["price"]), "subtotal": float(it["price"])*int(it["qty"])} for it in items],
        "total": round(total, 2)
    }
    RECEIPTS.insert(0, receipt)
    return jsonify({"ok": True, "receipt_id": rid})

@app.get("/receipt/<rid>")
@login_required
def view_receipt(rid):
    for r in RECEIPTS:
        if r["id"] == rid:
            return render_template("receipt_print.html", r=r)
    abort(404)

# ------------------ Error handlers ------------------
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    # Run without the auto-reloader so the process stays in the same PID
    # (helps when starting the server programmatically during tests).
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
