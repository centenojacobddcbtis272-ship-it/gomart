from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["gomart"]
productos = db["productos"]

productos.delete_many({})
print("🗑 Todos los productos eliminados.")

items = [
    {"nombre": "Pepsi 600ml", "precio": 18.5, "categoria": "Bebidas",
     "imagen": "/static/img/productos/pepsi600ml.webp"},

    {"nombre": "Coca Cola 600ml", "precio": 19.0, "categoria": "Bebidas",
     "imagen": "/static/img/productos/coca600ml.webp"},

    {"nombre": "Agua Bonafont 1L", "precio": 14.0, "categoria": "Bebidas",
     "imagen": "/static/img/productos/bonafont1l.webp"},

    {"nombre": "Sabritas Chips 500g", "precio": 50,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/chips500g.webp"},

    {"nombre": "Doritos Nacho 62g", "precio": 17,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/Botana_Dorito_Nachos_82g.webp"},

    {"nombre": "Cheetos Torciditos 150g", "precio": 33,
     "categoria": "Snacks",
     "imagen": "/static/img/productos/chetostorciditos.webp"},

    {"nombre": "Chocolate Hershey 40g", "precio": 15,
     "categoria": "Dulces",
     "imagen": "/static/img/productos/chocolatehershey´s.webp"},

    {"nombre": "M&M's 49g", "precio": 25,
     "categoria": "Dulces",
     "imagen": "/static/img/productos/M&M´s.webp"},

    {"nombre": "Cloro Cloralex 1L", "precio": 22,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/cloro_cloralex.webp"},

    {"nombre": "Jabón Zote Rosa 400g", "precio": 12,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/ZOTE400G.webp"},

    {"nombre": "Pinol 1L", "precio": 30.0,
     "categoria": "Limpieza",
     "imagen": "/static/img/productos/pinol.webp"},

    {"nombre": "Shampoo Head & Shoulders 375ml", "precio": 55.0,
     "categoria": "Higiene personal",
     "imagen": "/static/img/productos/head.webp"},

    {"nombre": "Jabón Dove 135g", "precio": 22.0,
     "categoria": "Higiene personal",
     "imagen": "/static/img/productos/dove.webp"},

    {"nombre": "Arroz Verde Valle 1kg", "precio": 32,
     "categoria": "Abarrotes",
     "imagen": "/static/img/productos/arroz_verde.webp"},

    {"nombre": "Frijol Peruano 1kg", "precio": 38,
     "categoria": "Abarrotes",
     "imagen": "/static/img/productos/arrozperuano.webp"},
]

productos.insert_many(items)
print("✔ Productos reiniciados e insertados correctamente.")
