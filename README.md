# SmartAudit AI – Luxury Price Audit

Solución de Inteligencia Artificial que automatiza la auditoría de precios y márgenes en productos de alta gama (relojería y joyería).

👉 **[Ver la aplicación en vivo (Render)](https://smartaudit-mgf.onrender.com)**

**Stack:** Python · pandas · scikit-learn · SQL (SQLite / SQLAlchemy) · Streamlit · Render

---

## 1. Problema de negocio

En el sector de lujo, **mantener precios consistentes y proteger los márgenes es crítico**. SmartAudit AI **identifica automáticamente desviaciones de precio**, productos vendidos sin margen y riesgos en la estrategia de precios, y genera alertas para Finanzas y Comercial.

## 2. Datos

- Origen: **inventario, ventas y compras internos** almacenados en una base de datos SQL (~148.000 filas combinadas, 78 variables).
- Fuentes externas: precio internacional del oro (yfinance) y tendencias de búsqueda (Google Trends).
- Columnas clave:
  - Inventario: `sku`, `costo`, `precio de venta`, `departamento`, `marca`, `proveedor`
  - Ventas: `referencia proveedor`, `precio de venta unitario`, `cantidad`, `fecha`
- Limpieza, filtrado y transformación en [`notebooks/explore.ipynb`](notebooks/explore.ipynb).
- Para proteger información sensible, solo se usaron los departamentos **RELOJERÍA y JOYERÍA** y una lista limitada de proveedores estratégicos.

## 3. Hallazgos del EDA

- Diferencias significativas entre relojería y joyería en precios y márgenes.
- Algunos SKU presentan **desviaciones negativas importantes** (productos vendidos sin margen).
- **Estacionalidad** mensual de ventas que afecta la evaluación de riesgo.
- Marcas con alta consistencia de precios frente a marcas con mayor desviación.
- Los contrastes de hipótesis confirmaron la relación entre **costo y precio de venta**.

## 4. Modelo y resultados

- Modelos comparados: Regresión Lineal, Random Forest y Gradient Boosting.
- Modelo final: **Random Forest Regressor** optimizado con `GridSearchCV`
  (`n_estimators=100`, `max_depth=None`, `min_samples_split=2`).
- Features: `costo` + departamento, marca, SKU, familia, material y categoría Lottus.
- Resultados en el conjunto de prueba del notebook (precio escalado con RobustScaler):

| Métrica | Valor |
|---|---|
| R² | **0.75** |
| MAE | 0.43 |
| RMSE | 3.94 |

**Modelo en la app:** el modelo del notebook pesa demasiado para GitHub, así que la app entrena al arrancar un Random Forest con los mismos hiperparámetros sobre `costo`, departamento, marca y familia (relojería y joyería). Su precisión se mide separando los SKU de entrenamiento y de prueba (el mismo producto aparece en varios meses del inventario) y se muestra en vivo como **Confianza IA (R²)**, ~96 %.

### Clasificación de riesgo

Desviación (%) = (precio facturado − precio IA) / precio IA × 100

| Alerta | Rango | Acción |
|---|---|---|
| 🟢 Verde | ±5 % | Precio dentro del rango |
| 🟡 Amarillo | 5 – 15 % | Protocolo de revisión |
| 🔴 Rojo | > 15 % o < −5 % | Producto sin margen: reportar a Finanzas |

## 5. Aplicación web

Desarrollada con **Streamlit**, con tres paneles:

1. **Sidebar:** departamento, proveedor, marca, SKU, landed cost, precio facturado y último precio internacional del oro.
2. **Panel central:** KPIs de precio IA, precio facturado y desviación; alertas por color; margen USD/%; unidades vendidas por mes de la marca (estacionalidad) y gauge de riesgo.
3. **Panel derecho:** *Brand Performance* (unidades compradas y vendidas por mes, precio promedio de costo y venta, inventario promedio, rotación y Confianza IA).

## 6. Estructura del repositorio

```
├── app.py                  # Aplicación Streamlit
├── notebooks/explore.ipynb # EDA, modelado y evaluación
├── scripts/                # Utilidades para inspeccionar y corregir la base SQL
├── asset/                  # Logo
└── requirements.txt
```

### Datos y modelos (no incluidos en el repositorio)

Los datos son información interna de la empresa y la base de datos pesa ~200 MB (GitHub no admite archivos de más de 100 MB), por eso `data/`, `sql/` y `models/` están en `.gitignore`.

- **Para la app:** no hay que hacer nada; `app.py` descarga `sql/database.db` desde Google Drive la primera vez que se ejecuta.
- **Para el notebook:** los Excel originales de `data/raw/` se piden a la autora. Con la base descargada por la app se pueden ejecutar las celdas que leen de SQL.

## 7. Cómo ejecutarlo

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 8. Próximos pasos

- Guardar el modelo completo del notebook en almacenamiento externo y cargarlo en la app en lugar de reentrenar.
- Predicciones multivariables que incluyan inventario y estacionalidad.
- Paneles más interactivos con mini-gráficos y KPIs dinámicos.

---

**María Gabriela Figuera Machuca** · © 2026 MGF – Venezuela
