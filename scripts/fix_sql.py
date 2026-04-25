import sqlite3

RUTA_DB = "/Users/mariafiguera/Downloads/ProyectoDataScience/sql/database.db"

conn = sqlite3.connect(RUTA_DB)
cur = conn.cursor()

print("Eliminando tabla catalogo_auditoria si existe...")
cur.execute("DROP TABLE IF EXISTS catalogo_auditoria;")

print("Creando tabla catalogo_auditoria con columnas reales...")

cur.execute("""
CREATE TABLE catalogo_auditoria AS

-- INVENTARIO
SELECT
    TRIM(sku) AS sku,
    TRIM(Marca) AS marca,
    TRIM(Departamento) AS departamento,
    TRIM(Familia) AS familia,
    TRIM(Especifico) AS material,
    costo AS costo_nacionalizado,
    "precio de venta" AS precio_venta,
    CATAGORIA_LOTTUS AS categoria_lottus
FROM inventario

UNION ALL

-- VENTAS
SELECT
    TRIM("Referencia Proveedor") AS sku,
    TRIM(MARCA) AS marca,
    TRIM(DEPARTAMENTO) AS departamento,
    TRIM(Familia) AS familia,
    TRIM("Categoría Específica") AS material,
    "Costo Unitario" AS costo_nacionalizado,
    "Precio de Venta Unitario" AS precio_venta,
    CATAGORIA_LOTTUS AS categoria_lottus
FROM ventas

UNION ALL

-- COMPRAS
SELECT
    TRIM(SKU) AS sku,
    TRIM(MARCA) AS marca,
    TRIM(DEPARTAMENTO) AS departamento,
    TRIM("FAMILIA ") AS familia,
    TRIM(ESPECIFICO) AS material,
    "precio costo (nacionalizado)" AS costo_nacionalizado,
    NULL AS precio_venta,
    CATAGORIA_LOTTUS AS categoria_lottus
FROM compras;
""")

conn.commit()
conn.close()

print("Tabla catalogo_auditoria creada correctamente.")