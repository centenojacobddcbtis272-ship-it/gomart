from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

client = MongoClient(config.MONGO_URI)
db = client.gomart

# -------------------------------
# Helpers
# -------------------------------
def usuario_actual():
    if "user_id" in session:
        return db.usuarios.find_one({"_id": ObjectId(session["user_id"])})
    return None


# -------------------------------
# Rutas
# -------------------------------
@app.route("/")
def index():
    hero_title = "Pasa por lo que te falta, llévate lo que te encanta"
    hero_subtitle = "Todo para tu casa, sin dar tantas vueltas."
    hero_image = "https://grupoenconcreto.com/wp-content/uploads/2023/03/GOmart.png"

    sucursales = [
        {
            "nombre": "Sucursal Centro",
            "direccion": "Calle Principal 123, Centro",
            "horario": "Lun-Dom 8:00 - 22:00",
            "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQshAGGmsHmId6ciUV-3Dqyu_W3PtWv4Vl6Ww&s"
        },
        {
            "nombre": "Sucursal Norte",
            "direccion": "Av. Las Flores 456, Norte",
            "horario": "Lun-Sab 8:00 - 21:00",
            "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAk7yWTgJCYEPu2fYvuVqCZGv4s0jp61rfcg&s"
        },
        {
            "nombre": "Sucursal Sur",
            "direccion": "Blvd. GoMart 789, Sur",
            "horario": "Lun-Dom 9:00 - 20:00",
            "img": "https://gomart.com.mx/img/site/pages/services/gomart-cerca-de-mi-ubicacion.jpg"
        }
    ]

    return render_template(
        "index.html",
        hero_title=hero_title,
        hero_subtitle=hero_subtitle,
        hero_image=hero_image,
        sucursales=sucursales,
        user=usuario_actual()
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"].encode("utf-8")

        user = db.usuarios.find_one({"correo": correo})
        if user and bcrypt.checkpw(password, user["password"]):
            session["user_id"] = str(user["_id"])
            return redirect(url_for("index"))

        return render_template("login.html", error="Credenciales incorrectas")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        data = request.form

        if db.usuarios.find_one({"correo": data["correo"]}):
            return render_template(
                "register.html",
                error="El correo ya está registrado.",
                datos=data
            )

        hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

        db.usuarios.insert_one({
            "nombre_completo": data["nombre"],
            "username": data["usuario"],
            "correo": data["correo"],
            "rol": "Cliente",
            "password": hashed
        })

        return redirect(url_for("login"))

    return render_template("register.html")


# ===========================
# 🔥 PRODUCTOS
# ===========================
@app.route("/productos")
def productos():
    categoria = request.args.get("categoria")

    if categoria:
        productos = list(db.productos.find({"categoria": categoria}))
    else:
        productos = list(db.productos.find())

    return render_template(
        "productos.html",
        productos=productos,
        categoria=categoria,
        user=usuario_actual()
    )


# ===========================
# 🔥 CARRITO
# ===========================
@app.route("/carrito")
def carrito():
    if not usuario_actual():
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    carrito = db.carritos.find_one({"user_id": user_id})

    items = []
    total = 0

    if carrito:
        for item in carrito["items"]:
            prod = db.productos.find_one({"_id": item["producto_id"]})
            if prod:
                prod["cantidad"] = item["cantidad"]
                prod["subtotal"] = prod["precio"] * prod["cantidad"]
                total += prod["subtotal"]
                items.append(prod)

    return render_template("carrito.html",
                           items=items,
                           total=total,
                           user=usuario_actual())

@app.route("/pago", methods=["GET", "POST"])
def pago():
    if not usuario_actual():
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])

    # Obtener carrito actual
    carrito = db.carritos.find_one({"user_id": user_id})

    if request.method == "POST":
        # BORRAR CARRITO DESPUÉS DEL PAGO
        db.carritos.delete_one({"user_id": user_id})

        return render_template("pago_exitoso.html", user=usuario_actual())

    total = 0
    if carrito:
        for item in carrito["items"]:
            prod = db.productos.find_one({"_id": item["producto_id"]})
            if prod:
                total += prod["precio"] * item["cantidad"]

    return render_template("pago.html", total=total, user=usuario_actual())

# ===========================
# 🟢 AGREGAR AL CARRITO (DESDE PRODUCTOS)
# ===========================
@app.route("/api/add_cart", methods=["POST"])
def add_cart():
    if not usuario_actual():
        return jsonify({"ok": False, "msg": "Debe iniciar sesión"})

    data = request.json
    prod_id = ObjectId(data["id"])
    user_id = ObjectId(session["user_id"])

    carrito = db.carritos.find_one({"user_id": user_id})

    if not carrito:
        db.carritos.insert_one({
            "user_id": user_id,
            "items": [{"producto_id": prod_id, "cantidad": 1}]
        })
        return jsonify({"ok": True})

    found = False
    for item in carrito["items"]:
        if item["producto_id"] == prod_id:
            item["cantidad"] += 1
            found = True
            break

    if not found:
        carrito["items"].append({"producto_id": prod_id, "cantidad": 1})

    db.carritos.update_one(
        {"_id": carrito["_id"]},
        {"$set": {"items": carrito["items"]}}
    )

    return jsonify({"ok": True})


# ===========================
# 🟢 AGREGAR (SUMAR) DESDE EL CARRITO
# ===========================
@app.route("/api/cart/add", methods=["POST"])
def cart_add():
    if not usuario_actual():
        return jsonify({"ok": False})

    data = request.json
    prod_id = ObjectId(data["id"])
    user_id = ObjectId(session["user_id"])

    carrito = db.carritos.find_one({"user_id": user_id})

    if not carrito:
        return jsonify({"ok": False})

    for item in carrito["items"]:
        if item["producto_id"] == prod_id:
            item["cantidad"] += 1

    db.carritos.update_one({"_id": carrito["_id"]}, {"$set": {"items": carrito["items"]}})

    return jsonify({"ok": True})


# ===========================
# 🔵 RESTAR
# ===========================
@app.route("/api/cart/remove", methods=["POST"])
def cart_remove():
    if not usuario_actual():
        return jsonify({"ok": False})

    data = request.json
    prod_id = ObjectId(data["id"])
    user_id = ObjectId(session["user_id"])

    carrito = db.carritos.find_one({"user_id": user_id})

    for item in carrito["items"]:
        if item["producto_id"] == prod_id:
            item["cantidad"] -= 1
            if item["cantidad"] <= 0:
                carrito["items"].remove(item)

    db.carritos.update_one({"_id": carrito["_id"]}, {"$set": {"items": carrito["items"]}})

    return jsonify({"ok": True})


# ===========================
# 🔴 ELIMINAR
# ===========================
@app.route("/api/cart/delete", methods=["POST"])
def cart_delete():
    if not usuario_actual():
        return jsonify({"ok": False})

    data = request.json
    prod_id = ObjectId(data["id"])
    user_id = ObjectId(session["user_id"])

    carrito = db.carritos.find_one({"user_id": user_id})
    carrito["items"] = [item for item in carrito["items"] if item["producto_id"] != prod_id]

    db.carritos.update_one({"_id": carrito["_id"]}, {"$set": {"items": carrito["items"]}})

    return jsonify({"ok": True})


# ===========================
# 🟣 CONTADOR DEL CARRITO
# ===========================
@app.route("/api/cart/count")
def cart_count():
    if not usuario_actual():
        return jsonify({"total": 0})

    user_id = ObjectId(session["user_id"])
    carrito = db.carritos.find_one({"user_id": user_id})

    if not carrito:
        return jsonify({"total": 0})

    total_items = sum(item["cantidad"] for item in carrito["items"])

    return jsonify({"total": total_items})


if __name__ == "__main__":
    app.run(debug=True)
