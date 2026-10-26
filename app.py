from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)
app.secret_key = "kirana-demo-change-this"
DB_PATH = Path(__file__).with_name("kirana.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'General',
            price REAL NOT NULL CHECK(price >= 0),
            quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
            low_stock_limit INTEGER NOT NULL DEFAULT 5 CHECK(low_stock_limit >= 0),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total REAL NOT NULL,
            sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
        );
        """)
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO products(name, category, price, quantity, low_stock_limit) VALUES(?,?,?,?,?)",
                [
                    ("Rice 1 kg", "Grains", 62, 30, 8),
                    ("Sugar 1 kg", "Essentials", 45, 18, 5),
                    ("Cooking Oil 1 L", "Oil", 145, 12, 4),
                    ("Tea Powder 250 g", "Beverages", 95, 4, 5),
                    ("Bath Soap", "Personal Care", 35, 22, 6),
                    ("Biscuits", "Snacks", 10, 3, 8),
                ],
            )

@app.route("/")
def dashboard():
    with db() as conn:
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        low_stock = conn.execute("SELECT COUNT(*) FROM products WHERE quantity <= low_stock_limit").fetchone()[0]
        inventory_value = conn.execute("SELECT COALESCE(SUM(price * quantity), 0) FROM products").fetchone()[0]
        today_sales = conn.execute("SELECT COALESCE(SUM(total), 0) FROM sales WHERE date(sold_at)=date('now','localtime')").fetchone()[0]
        recent_sales = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 6").fetchall()
        low_products = conn.execute("SELECT * FROM products WHERE quantity <= low_stock_limit ORDER BY quantity ASC LIMIT 6").fetchall()
    return render_template("dashboard.html", product_count=product_count, low_stock=low_stock,
                           inventory_value=inventory_value, today_sales=today_sales,
                           recent_sales=recent_sales, low_products=low_products)

@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    with db() as conn:
        rows = conn.execute("""SELECT * FROM products
            WHERE name LIKE ? OR category LIKE ? ORDER BY name""", (f"%{q}%", f"%{q}%")).fetchall()
    return render_template("products.html", products=rows, q=q)

@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        try:
            price = float(request.form.get("price", "0"))
            quantity = int(request.form.get("quantity", "0"))
            limit = int(request.form.get("low_stock_limit", "5"))
            if not name or price < 0 or quantity < 0 or limit < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a product name and valid non-negative numbers.", "error")
            return render_template("product_form.html", product=None)
        with db() as conn:
            conn.execute("INSERT INTO products(name,category,price,quantity,low_stock_limit) VALUES(?,?,?,?,?)",
                         (name, category, price, quantity, limit))
        flash("Product added successfully.", "success")
        return redirect(url_for("products"))
    return render_template("product_form.html", product=None)

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    with db() as conn:
        product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "General").strip() or "General"
        try:
            price = float(request.form.get("price", "0"))
            quantity = int(request.form.get("quantity", "0"))
            limit = int(request.form.get("low_stock_limit", "5"))
            if not name or price < 0 or quantity < 0 or limit < 0:
                raise ValueError
        except ValueError:
            flash("Please enter a product name and valid non-negative numbers.", "error")
            return render_template("product_form.html", product=product)
        with db() as conn:
            conn.execute("""UPDATE products SET name=?,category=?,price=?,quantity=?,low_stock_limit=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                         (name, category, price, quantity, limit, product_id))
        flash("Product updated.", "success")
        return redirect(url_for("products"))
    return render_template("product_form.html", product=product)

@app.post("/products/<int:product_id>/delete")
def delete_product(product_id):
    with db() as conn:
        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    flash("Product deleted.", "success")
    return redirect(url_for("products"))

@app.route("/sales", methods=["GET", "POST"])
def sales():
    if request.method == "POST":
        try:
            product_id = int(request.form.get("product_id", "0"))
            quantity = int(request.form.get("quantity", "0"))
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Enter a valid quantity.", "error")
            return redirect(url_for("sales"))
        with db() as conn:
            product = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if product is None:
                flash("Select a valid product.", "error")
            elif product["quantity"] < quantity:
                flash(f"Not enough stock. Available quantity: {product['quantity']}.", "error")
            else:
                total = round(product["price"] * quantity, 2)
                conn.execute("UPDATE products SET quantity=quantity-?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                             (quantity, product_id))
                conn.execute("INSERT INTO sales(product_id,product_name,quantity,unit_price,total) VALUES(?,?,?,?,?)",
                             (product_id, product["name"], quantity, product["price"], total))
                flash(f"Sale recorded: ₹{total:.2f}. Stock updated.", "success")
        return redirect(url_for("sales"))
    with db() as conn:
        products_list = conn.execute("SELECT * FROM products WHERE quantity > 0 ORDER BY name").fetchall()
        sales_list = conn.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("sales.html", products=products_list, sales=sales_list)

@app.route("/about")
def about():
    return render_template("about.html")

init_db()

if __name__ == "__main__":
    app.run(debug=True)
