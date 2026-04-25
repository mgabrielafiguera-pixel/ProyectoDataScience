import sqlite3

RUTA_DB = "/Users/mariafiguera/Downloads/ProyectoDataScience/sql/database.db"

conn = sqlite3.connect(RUTA_DB)
cur = conn.cursor()

tablas = ["inventario", "ventas", "compras"]

for t in tablas:
    print(f"\n--- Columnas de {t} ---")
    cur.execute(f"PRAGMA table_info({t});")
    for col in cur.fetchall():
        print(col[1])

conn.close()