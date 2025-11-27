from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from pymongo import MongoClient
from bson import ObjectId
import bcrypt
import config
import os
from werkzeug.utils import secure_filename
from datetime import datetime   # <-- IMPORTANTE

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# === SUBIDA DE FOTOS DE PERFIL ===
UPLOAD_FOLDER = "static/img/perfiles"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# === CONEXIÓN A MONGO ===
MONGO_URI = os.getenv("MONGO_URI")

if MONGO_URI:
    print("✔ Conectado a MongoDB Atlas")
else:
    print("❌ ERROR: No se encontró la variable MONGO_URI")
    raise Exception("Agrega MONGO_URI en Render")

client = MongoClient(MONGO_URI)
db = client["gomart"]


# ============================================================
# Helpers
# ============================================================
def usuario_actual():
    if "user_id" in session:
        return db.usuarios.find_one({"_id": ObjectId(session["user_id"])})
    return None


# ============================================================
# HOME
# ============================================================
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

    return render_template("index.html",
                           hero_title=hero_title,
                           hero_subtitle=hero_subtitle,
                           hero_image=hero_image,
                           sucursales=sucursales,
                           user=usuario_actual())


# ============================================================
# LOGIN
# ============================================================
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


# ============================================================
# REGISTRO
# ============================================================
@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        data = request.form

        if db.usuarios.find_one({"correo": data["correo"]}):
            return render_template("register.html",
                                   error="El correo ya está registrado.",
                                   datos=data)

        hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())

        db.usuarios.insert_one({
            "nombre_completo": data["nombre"],
            "username": data["usuario"],
            "correo": data["correo"],
            "rol": "Cliente",
            "password": hashed,
            "foto": "/static/img/perfiles/default.png"
        })

        return redirect(url_for("login"))

    return render_template("register.html")


# ============================================================
# PRODUCTOS
# ============================================================
@app.route("/productos")
def productos():
    categoria = request.args.get("categoria")

    if categoria:
        productos = list(db.productos.find({"categoria": categoria}))
    else:
        productos = list(db.productos.find())

    return render_template("productos.html",
                           productos=productos,
                           categoria=categoria,
                           user=usuario_actual())


# ============================================================
# CARRITO
# ============================================================
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


# ============================================================
# PAGO (CORREGIDO Y COMPLETO)
# ============================================================
@app.route("/pago", methods=["GET", "POST"])
def pago():
    if not usuario_actual():
        return redirect(url_for("login"))

    user_id = ObjectId(session["user_id"])
    carrito = db.carritos.find_one({"user_id": user_id})

    # -----------------------------
    # PROCESAR COMPRA (POST)
    # -----------------------------
    if request.method == "POST":
        items_compra = []
        total = 0

        # convertir carrito a historial de compras
        if carrito:
            for item in carrito["items"]:
                prod = db.productos.find_one({"_id": item["producto_id"]})
                if prod:
                    subtotal = prod["precio"] * item["cantidad"]
                    total += subtotal

                    items_compra.append({
                        "nombre": prod["nombre"],
                        "precio": prod["precio"],
                        "cantidad": item["cantidad"],
                        "subtotal": subtotal
                    })

        # guardar compra
        db.compras.insert_one({
            "user_id": user_id,
            "items": items_compra,
            "total": total,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # limpiar carrito
        db.carritos.delete_one({"user_id": user_id})

        return render_template("pago_exitoso.html", user=usuario_actual())

    # -----------------------------
    # MOSTRAR TOTAL (GET)
    # -----------------------------
    total = 0
    if carrito:
        for item in carrito["items"]:
            prod = db.productos.find_one({"_id": item["producto_id"]})
            if prod:
                total += prod["precio"] * item["cantidad"]

    return render_template("pago.html", total=total, user=usuario_actual())


# ============================================================
# API CARRITO
# ============================================================
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

    db.carritos.update_one(
        {"_id": carrito["_id"]},
        {"$set": {"items": carrito["items"]}}
    )

    return jsonify({"ok": True})


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

    db.carritos.update_one(
        {"_id": carrito["_id"]},
        {"$set": {"items": carrito["items"]}}
    )

    return jsonify({"ok": True})


@app.route("/api/cart/delete", methods=["POST"])
def cart_delete():
    if not usuario_actual():
        return jsonify({"ok": False})

    data = request.json
    prod_id = ObjectId(data["id"])
    user_id = ObjectId(session["user_id"])

    carrito = db.carritos.find_one({"user_id": user_id})
    carrito["items"] = [
        item for item in carrito["items"] if item["producto_id"] != prod_id
    ]

    db.carritos.update_one(
        {"_id": carrito["_id"]},
        {"$set": {"items": carrito["items"]}}
    )

    return jsonify({"ok": True})


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


# ============================================================
# PERFIL DEL USUARIO
# ============================================================
@app.route("/perfil")
def perfil():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    return render_template("perfil.html", user=user)


@app.route("/perfil/editar", methods=["GET", "POST"])
def editar_perfil():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        nuevo_nombre = request.form["nombre"]

        db.usuarios.update_one(
            {"_id": user["_id"]},
            {"$set": {"nombre_completo": nuevo_nombre}}
        )

        return redirect(url_for("perfil"))

    return render_template("editar_perfil.html", user=user)


@app.route("/perfil/password", methods=["GET", "POST"])
def cambiar_password():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        actual = request.form["actual"].encode("utf-8")
        nueva = request.form["nueva"].encode("utf-8")

        if not bcrypt.checkpw(actual, user["password"]):
            return render_template("cambiar_password.html",
                                   user=user,
                                   error="La contraseña actual es incorrecta")

        hashed = bcrypt.hashpw(nueva, bcrypt.gensalt())

        db.usuarios.update_one(
            {"_id": user["_id"]},
            {"$set": {"password": hashed}}
        )

        return redirect(url_for("perfil"))

    return render_template("cambiar_password.html", user=user)


@app.route("/perfil/foto", methods=["GET", "POST"])
def cambiar_foto():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "foto" not in request.files:
            return render_template("cambiar_foto.html",
                                   user=user,
                                   error="No seleccionaste un archivo")

        file = request.files["foto"]

        if file.filename == "":
            return render_template("cambiar_foto.html",
                                   user=user,
                                   error="Archivo vacío")

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        db.usuarios.update_one(
            {"_id": user["_id"]},
            {"$set": {"foto": f"/static/img/perfiles/{filename}"}}
        )

        return redirect(url_for("perfil"))

    return render_template("cambiar_foto.html", user=user)


# ============================================================
# HISTORIAL DE COMPRAS
# ============================================================
@app.route("/historial")
def historial():
    user = usuario_actual()
    if not user:
        return redirect(url_for("login"))

    compras = list(db.compras.find({"user_id": user["_id"]}))

    return render_template("historial.html",
                           user=user,
                           compras=compras)


# ============================================================
# RUN APP
# ============================================================
if __name__ == "__main__":
    app.run(debug=True)
