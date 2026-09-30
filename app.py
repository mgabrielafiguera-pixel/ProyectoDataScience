import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import r2_score
import plotly.graph_objects as go
from PIL import Image
import os
import gdown

# -----------------------
# RUTAS Y DESCARGA DE LA BASE DE DATOS
# -----------------------
# Versión reducida de la base de datos (solo lo que muestra la app): los datos completos son confidenciales.
ID_DATABASE_DRIVE = "1QBJNi7SIULQKNE1rBz_aX63__spKcHfm"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sql", "database.db")
LOGO_PATH = os.path.join(BASE_DIR, "asset", "logomgf.png")

st.set_page_config(page_title="SMARTAUDIT AI", layout="wide")

@st.cache_resource(show_spinner="Descargando la base de datos, solo la primera vez...")
def descargar_base_datos():
    # Una sola descarga por servidor aunque haya varias sesiones abiertas.
    # Se baja a un archivo temporal y solo se renombra si llegó completa: Drive a veces corta
    # la conexión y un archivo a medias (o vacío) haría fallar la app en todos los arranques.
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        return True
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    temporal = DB_PATH + ".descarga"
    for _ in range(3):
        try:
            gdown.download(f"https://drive.google.com/uc?id={ID_DATABASE_DRIVE}", temporal, quiet=True, resume=True)
            if os.path.getsize(temporal) > 0:
                os.replace(temporal, DB_PATH)
                return True
        except Exception:
            pass
    return False

if not descargar_base_datos():
    descargar_base_datos.clear()
    st.error("No se pudo descargar la base de datos desde Google Drive. Recarga la página para reintentar.")
    st.stop()

# -----------------------
# ESTILOS
# -----------------------

st.markdown("""
<style>
body, .main, .block-container { background-color: #1c1c1c !important; color: white; }
h1, h2, h3 { color: white; font-weight: bold; }
.metric-box { background-color: #2a2a2a; border: 3px solid #d4af37; border-radius: 12px; padding: 25px; text-align: center; color: white; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
.metric-title { font-size: 14px; color: #d4af37; font-weight: bold; }
.metric-value { font-size: 28px; font-weight: bold; color: #ffffff; }
.alert-box { padding: 20px; border-radius: 12px; text-align: center; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 25px; }
.alert-green { background:#1e4620; color:#00ff88; border: 3px solid #00ff88; }
.alert-yellow { background:#4a3f1c; color:#ffcc00; border: 3px solid #ffcc00; }
.alert-red { background:#3a0000; color:#ff4d4d; border: 3px solid #ff1a1a; }
.brand-panel { background-color: #2a2a2a; padding: 10px; border-radius: 12px; margin-top: 0px; }
.footer { color:#888; font-size:12px; text-align:center; margin-top:20px; }
[data-testid="stSidebar"] { background-color: #1c1c1c; }
[data-testid="stSidebar"] label { color: white !important; }
</style>
""", unsafe_allow_html=True)

st.title("SMARTAUDIT AI – Luxury Price Audit")

def metric_box(col, titulo, valor):
    col.markdown(f"<div class='metric-box'><div class='metric-title'>{titulo}</div><div class='metric-value'>{valor}</div></div>", unsafe_allow_html=True)

# -----------------------
# CARGA DE DATOS
# -----------------------
engine = create_engine(f"sqlite:///{DB_PATH}")

DEPARTAMENTOS_VISIBLES = ["RELOJERIA", "JOYERIA"]
PROVEEDORES_VISIBLES = ["AUDEMARS PIGUET ET CIE.", "BELL & ROSS USA", "CHRONO AG", "CITIZEN LATINAMERICA CORP", "DAMIANI S.P.A", "DJULA S.A.R.L.", "MESSIKA USA INC", "MONTBLANC SIMPLO GMBH", "POMELLATO USA INC", "RICHARD PERLT VENEZUELA", "RICHEMONT BAUME MERCIER", "RICHEMONT NORTH AMERICA INC (IWC)", "RICHEMONT NORTH AMERICA INC (PANERAI)", "RICHEMONT NORTH AMERICA INC (RICHEMONT NORTH AMERICA INC (CARTIER))", "ROBERTO COIN S.P.A.", "SONGA ANTONIO SPA", "SWATCH AG", "TAG HEUER", "ZENITH"]

@st.cache_data
def load_data():
    try:
        inv = pd.read_sql("SELECT * FROM inventario", engine)
        mensual = pd.read_sql("SELECT sku, mes, compras_mes, ventas_mes, inventario_final FROM inventario_mensual_final", engine)
        oro = pd.read_sql("SELECT fecha, precio_onza_usd, precio_gramo_usd FROM precio_oro ORDER BY fecha DESC LIMIT 1", engine)
    except Exception as e:
        st.error(f"Error al cargar la base de datos: {e}")
        st.stop()
    inv.columns = inv.columns.str.lower()
    inv = inv.dropna(subset=["sku", "costo", "precio de venta"])
    inv = inv[(inv["costo"] > 0) & (inv["precio de venta"] > 0)]
    inv = inv[inv["departamento"].isin(DEPARTAMENTOS_VISIBLES)].copy()
    inv["sku"] = inv["sku"].str.strip()
    return inv, mensual, oro

df, df_mensual, df_oro = load_data()

# -----------------------
# MODELO ML
# -----------------------
# Hiperparámetros elegidos con GridSearchCV en notebooks/explore.ipynb
# (n_estimators=100, max_depth=None, min_samples_split=2).
FEATURES_CAT = ["departamento", "marca_correcta", "familia"]

def codificar(data, categorias):
    X = data[["costo"]].copy()
    for c in FEATURES_CAT:
        X[c] = pd.Categorical(data[c], categories=categorias[c]).codes
    return X

@st.cache_resource
def train_model(data):
    categorias = {c: data[c].dropna().unique() for c in FEATURES_CAT}
    X = codificar(data, categorias)
    y = data["precio de venta"]

    # Evaluación separando por SKU: el mismo producto aparece en varios meses del inventario
    # y no debe estar a la vez en entrenamiento y en prueba.
    train_idx, test_idx = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42).split(X, y, groups=data["sku"]))
    params = dict(n_estimators=100, max_depth=None, min_samples_split=2, random_state=42, n_jobs=-1)
    modelo_eval = RandomForestRegressor(**params).fit(X.iloc[train_idx], y.iloc[train_idx])
    r2 = r2_score(y.iloc[test_idx], modelo_eval.predict(X.iloc[test_idx]))

    modelo = RandomForestRegressor(**params).fit(X, y)
    return modelo, categorias, r2

model, categorias, r2_modelo = train_model(df)

# -----------------------
# SIDEBAR
# -----------------------
st.sidebar.header("AUDIT INPUTS")

if os.path.exists(LOGO_PATH):
    st.sidebar.image(Image.open(LOGO_PATH), width=200)

dep = st.sidebar.selectbox("Departamento", DEPARTAMENTOS_VISIBLES)
df_dep = df[df["departamento"] == dep]
df_dep_filtrado = df_dep[df_dep["proveedor_correcto"].isin(PROVEEDORES_VISIBLES)]

if df_dep_filtrado.empty:
    st.sidebar.warning("No hay datos disponibles")
    st.stop()

prov = st.sidebar.selectbox("Proveedor", sorted(df_dep_filtrado["proveedor_correcto"].dropna().unique()))
df_prov = df_dep_filtrado[df_dep_filtrado["proveedor_correcto"] == prov]
marca = st.sidebar.selectbox("Marca", sorted(df_prov["marca_correcta"].dropna().unique()))
df_marca = df_prov[df_prov["marca_correcta"] == marca]
sku = st.sidebar.selectbox("SKU", sorted(df_marca["sku"].dropna().unique()))
row = df_marca[df_marca["sku"] == sku].sort_values("fecha").iloc[-1]

costo_input = st.sidebar.number_input("Landed Cost", value=float(row["costo"]))
precio_input = st.sidebar.number_input("Precio Facturado", value=float(row["precio de venta"]))

if not df_oro.empty:
    oro = df_oro.iloc[0]
    st.sidebar.markdown("**Precio internacional del oro**")
    st.sidebar.write(f"${oro['precio_onza_usd']:,.2f} / onza · ${oro['precio_gramo_usd']:,.2f} / gramo")
    st.sidebar.caption(f"Cierre del {pd.to_datetime(oro['fecha']).date()}")

# -----------------------
# CÁLCULOS
# -----------------------
entrada = row[FEATURES_CAT].to_frame().T.assign(costo=costo_input)
precio_ia = model.predict(codificar(entrada, categorias))[0]
desviacion = (precio_input - precio_ia) / precio_ia * 100
margen = precio_input - costo_input
margen_pct = margen / precio_input * 100 if precio_input else 0

# -----------------------
# LAYOUT PRINCIPAL
# -----------------------
left, right = st.columns([2,1])

with left:
    c1, c2, c3 = st.columns(3)
    metric_box(c1, "PRECIO IA", f"${precio_ia:,.0f}")
    metric_box(c2, "Precio Facturado", f"${precio_input:,.0f}")
    metric_box(c3, "DESVIACIÓN", f"{desviacion:.1f}%")

    # Verde: ±5 % · Amarillo: 5–15 % · Rojo: > 15 % o < −5 % (sin margen)
    if desviacion < -5:
        alert, text = "alert-red", "🔴 PRODUCTO VENDIDO POR DEBAJO DEL PRECIO IA.<br>Reportar a Finanzas."
    elif desviacion > 15:
        alert, text = "alert-red", "🔴 DESVIACIÓN ALTA SOBRE EL PRECIO IA.<br>Se requiere evaluación."
    elif desviacion > 5:
        alert, text = "alert-yellow", "🟡 NOTA: DESVIACIÓN MEDIA. Se establece protocolo de revisión."
    else:
        alert, text = "alert-green", "🟢 Precio dentro del rango IA ±5%. No requiere auditoría."
    st.markdown(f'<div class="alert-box {alert}">{text}</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    metric_box(f1, "MARGEN USD", f"${margen:,.0f}")
    metric_box(f2, "MARGEN %", f"{margen_pct:.1f}%")

    # Movimientos mensuales de los SKU de la marca
    mov_marca = df_mensual[df_mensual["sku"].isin(df[df["marca_correcta"] == marca]["sku"].unique())]

    st.markdown(f"### Estacionalidad de ventas – {marca}")
    if mov_marca.empty:
        st.info("No hay movimientos mensuales registrados para esta marca.")
    else:
        st.bar_chart(mov_marca.groupby("mes")["ventas_mes"].sum().rename("Unidades vendidas"))

    st.markdown("### Scoring de Riesgo IA")
    riesgo_pct = max(min(abs(desviacion), 100), 0)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = riesgo_pct,
        title = {'text': "Nivel de riesgo (%)", 'font': {'color': "white"}},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#d4af37"}, 'bgcolor': "#2a2a2a", 'steps': [{'range': [0, 5], 'color': "#1e4620"}, {'range': [5, 15], 'color': "#ffcc00"}, {'range': [15, 100], 'color': "#ff4d4d"}]}
    ))
    fig_gauge.update_layout(paper_bgcolor="#1c1c1c", font_color="white", height=300)
    st.plotly_chart(fig_gauge, width="stretch")

with right:
    st.markdown("<div class='brand-panel'>", unsafe_allow_html=True)
    st.markdown("### Brand Performance")
    marca_df = df[df["marca_correcta"] == marca]
    n_meses = df_mensual["mes"].nunique()
    compras_mes = mov_marca["compras_mes"].sum() / n_meses
    ventas_mes = mov_marca["ventas_mes"].sum() / n_meses
    # El inventario negativo son errores de registro: se cuenta como 0
    inv_promedio = mov_marca["inventario_final"].clip(lower=0).groupby(mov_marca["mes"]).sum().mean() if not mov_marca.empty else 0
    rot = ventas_mes * n_meses / inv_promedio if inv_promedio > 0 else 0

    metric_box(st, "Unidades Compradas / mes", f"{compras_mes:.1f}")
    metric_box(st, "Promedio Precio Costo", f"${marca_df['costo'].mean():,.0f}")
    metric_box(st, "Unidades Vendidas / mes", f"{ventas_mes:.1f}")
    metric_box(st, "Promedio Precio Venta", f"${marca_df['precio de venta'].mean():,.0f}")
    metric_box(st, "Inventario Promedio", f"{inv_promedio:,.0f} und")
    metric_box(st, f"Rotación ({n_meses} meses)", f"{rot:.2f}x")
    metric_box(st, "Confianza IA (R²)", f"{r2_modelo * 100:.1f}%")
    st.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='footer'>© 2026 MGF - Propiedad Intelectual - Venezuela</div>", unsafe_allow_html=True)
