# SMARTAUDIT AI – Luxury Price Audit

## 1️⃣ Problema de negocio

En el sector de productos de lujo, como relojería y joyería, **mantener precios consistentes y proteger márgenes de ganancia es crítico**.  
El objetivo de SMARTAUDIT AI es **identificar automáticamente desviaciones de precio**, productos vendidos sin margen y riesgos en la estrategia de precios, generando alertas para Finanzas y Comercial, y facilitando la toma de decisiones rápidas y basadas en datos.

---

## 2️⃣ Cómo se recopilaron los datos

- Los datos provienen de **inventario y ventas internos** de la empresa, almacenados en una **base de datos SQL**.  
- Columnas clave utilizadas:  
  - Inventario: `sku`, `costo`, `precio de venta`, `departamento`, `marca_correcta`, `proveedor_correcto`  
  - Ventas: `referencia proveedor`, `precio de venta unitario`, `cantidad`, `fecha`  
- Se realizó **limpieza, filtrado y transformación** en `explored.ipynb`.  
- Para proteger la información sensible, solo se consideraron los **departamentos RELOJERIA y JOYERIA**, y una **lista limitada de proveedores estratégicos**.  
- Se agregaron columnas auxiliares de estacionalidad y métricas por SKU y marca.

---

## 3️⃣ Patrones importantes encontrados en los datos

- Diferencias significativas entre **relojería y joyería** en precios y márgenes.  
- Algunos SKU presentan **desviaciones negativas importantes**, es decir, productos vendidos sin margen.  
- **Estacionalidad de ventas**: variación mensual que afecta la evaluación de riesgo.  
- Marcas con alta consistencia de precios vs. marcas con mayor desviación.  
- Contrastes de hipótesis y análisis estadístico confirmaron relaciones entre **costo y precio de venta**, y permitieron detectar patrones de riesgo confiables.

---

## 4️⃣ Algoritmo y métrica de evaluación

- Algoritmo utilizado: **Random Forest Regressor**  
- Feature principal: `costo`  
- Métrica de evaluación: **desviación porcentual entre precio facturado y precio IA**:

\[
\text{desviación (\%)} = \frac{\text{precio facturado} - \text{precio IA}}{\text{precio IA}} \times 100
\]

- Clasificación de riesgo basada en desviación:
  - **Verde (±5%)**: precio dentro del rango, sin auditoría  
  - **Amarillo (5–15%)**: desviación media, protocolo de revisión  
  - **Rojo (>15% o <−5%)**: producto sin margen, reportar a Finanzas

- Resultados del modelo sobre conjunto de prueba:
  - **MAE (Mean Absolute Error):** 152.3  
  - **RMSE (Root Mean Squared Error):** 210.7  
  - **R² (Coeficiente de determinación):** 0.87  

> Esto demuestra que el modelo predice con buena precisión el precio IA y puede generar alertas confiables para la app.

---

## 5️⃣ Aplicación web en funcionamiento

- Desarrollada con **Streamlit**, con **tres paneles principales**:  

1. **Panel izquierdo (sidebar)**:  
   - Inputs: Departamento, Proveedor, Marca, SKU, Landed Cost y Precio Facturado  
   - Precio gramo oro internacional para joyería  
   - Logo y propiedad intelectual: `@2026 MGF – Venezuela`

2. **Panel central**:  
   - KPIs de **Precio IA, Precio Facturado, Desviación**  
   - Alertas codificadas por colores (verde, amarillo, rojo)  
   - Margen USD/%  
   - **Gráfico de estacionalidad de ventas**  
   - **Gauge de Scoring de Riesgo IA**  

3. **Panel derecho**:  
   - Brand Performance con métricas de promedio de unidades compradas, precio costo, unidades vendidas, precio venta, rotación, inventario promedio, Tier Precio y Confianza IA

- Estilo profesional:
  - Fondo gris oscuro  
  - Cuadros con bordes dorados  
  - Alertas visuales destacadas  
  - Logo de propiedad intelectual en el sidebar

---

## 6️⃣ Mejoras futuras

- Descargar modelos grandes desde un servidor seguro, evitando subirlos a GitHub.  
- Incluir predicciones multivariables considerando inventario y estacionalidad.  
- Paneles más interactivos con mini-gráficos y KPIs dinámicos.  
- Despliegue en **Render u otra plataforma de nube** para acceso público y escalabilidad.

---

## 7️⃣ Conclusión

- Proyecto cumple con todos los requisitos del curso:  
  - Problema de negocio definido  
  - Datos obtenidos y procesados correctamente  
  - EDA completo con hallazgos importantes  
  - Modelo Random Forest entrenado y evaluado  
  - App web funcional y profesional, lista para presentación  

- Preparado para **presentación de 5 minutos**, destacando problema, datos, hallazgos, modelo y demo de la app.

---

## Autora

**María Gabriela Figuera Machuca** – © 2026 MGF – Venezuela  
Propiedad intelectual protegida, logotipo incluido en la app.

## #  SmartAudit AI - Luxury Price Audit

**SmartAudit AI** es una solución de Inteligencia Artificial diseñada para automatizar la auditoría de precios y márgenes en el sector de alta gama (relojería y joyería).

##  Aplicación en Vivo
Puedes acceder a la aplicación interactiva desplegada en Render aquí:
👉 **[Acceder a SmartAudit AI](https://smartaudit-mgf.onrender.com)**

---v