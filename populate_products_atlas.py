from pymongo import MongoClient
from config import MONGO_URI
import sys

if not MONGO_URI:
    print("❌ ERROR: No existe MONGO_URI en config.py")
    sys.exit()

client = MongoClient(MONGO_URI)
db = client["gomart"]
productos = db["productos"]

items = [

    # BEBIDAS
    {"nombre": "Pepsi 600ml", "precio": 18.5, "categoria": "Bebidas",
     "imagen": "/static/img/productos/pepsi600ml.webp"},
    {"nombre": "Coca Cola 600ml", "precio": 19.0, "categoria": "Bebidas",
     "imagen": "/static/img/productos/coca600ml.webp"},
    {"nombre": "Agua Bonafont 1L", "precio": 14.0, "categoria": "Bebidas",
     "imagen": "/static/img/productos/bonafont1l.webp"},

    # SNACKS
    {"nombre": "Sabritas Chips 500g", "precio": 50,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/chips500g.webp"},
    {"nombre": "Doritos Nacho 62g", "precio": 17,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/Botana_Dorito_Nachos_82g.webp"},
    {"nombre": "Cheetos Torciditos 150g", "precio": 33,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/chetostorciditos.webp"},

    # DULCES
    {"nombre": "Chocolate Hershey 40g", "precio": 15,
     "categoria": "Dulces",
     "imagen": "/static/img/productos/chocolatehersheys.webp"},
    {"nombre": "M&M's 49g", "precio": 25,
     "categoria": "Dulces",
     "imagen": "/static/img/productos/MandMs.webp"},

    # LIMPIEZA
    {"nombre": "Cloro Cloralex 1L", "precio": 22,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/cloroCloralex.webp"},
    {"nombre": "Jabón Zote Rosa 400g", "precio": 12,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/ZOTE400G.webp"},
    {"nombre": "Pinol 1L", "precio": 30.0,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/pinol.webp"},   # ← CORRECTO

    # HIGIENE PERSONAL
    {"nombre": "Shampoo Head & Shoulders 375ml", "precio": 55.0,
     "categoria": "Higiene personal",
     "imagen": "/static/img/productos/head.webp"},  # ← CORRECTO
    {"nombre": "Jabón Dove 135g", "precio": 22.0,
     "categoria": "Higiene personal",
     "imagen": "/static/img/productos/dove.webp"}, # ← CORRECTO

    # ABARROTES
    {"nombre": "Arroz Verde Valle 1kg", "precio": 32,
     "categoria": "Abarrotes",
     "imagen": "/static/img/productos/arroz_verde.webp"},
    {"nombre": "Frijol Peruano 1kg", "precio": 38,
     "categoria": "Abarrotes",
     "imagen": "/static/img/productos/arrozperuano.webp"},
]

insertados = 0

for item in items:
    existe = productos.find_one({"nombre": item["nombre"]})
    if existe:
        print(f"⚠️ Ya existe: {item['nombre']}")
        productos.update_one({"nombre": item["nombre"]}, {"$set": item})  # ← ACTUALIZA IMAGEN
        print(f"🔄 Actualizado: {item['nombre']}")
    else:
        productos.insert_one(item)
        print(f"✔ Insertado: {item['nombre']}")
        insertados += 1

print("\n=========================================")
print(f"✔ Insertados nuevos: {insertados}")
print("=========================================\n")
