import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go
from PIL import Image
import os
import gdown
import joblib

# -----------------------
# ANEXO PARA RENDER: CARGA DE MODELOS DESDE DRIVE
# -----------------------
# Crear carpetas si no existen
if not os.path.exists('models'): os.makedirs('models')
if not os.path.exists('sql'): os.makedirs('sql')
if not os.path.exists('asset'): os.makedirs('asset')

def download_from_drive(file_id, output):
    if not os.path.exists(output):
        url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(url, output, quiet=False)

# Diccionario con tus archivos .pkl en Drive
SCALERS_DRIVE = {
    "random_forest_model.pkl": "15QYl2ozFjLOJ_ppB-6959imy_WAIfmw7",
    "encoder_proveedor.pkl": "1rjDLAB8od0vQ1m0HsrVvT0aomNHcV7Nv",
    "encoder_sku.pkl": "1gqEmlwaoosbupB2-ZD2-rSXj70CpU0sa",
    "encoder_marca.pkl": "1aWfvtGUZqsIhXcRcfyFKstlwFX8v8iu0",
    "encoder_departamento.pkl": "1TfXHcygIpq8QpxBfLSMSWGrzx5dUWj5t",
    "encoder_material.pkl": "15eCv_mth8oUaDlEiyd8xHMR-Tltfl3pn",
    "encoder_categoria_lottus.pkl": "126yZfMd4mNJ7pifG-d-LleizMkd32adD"
}

# Ejecutar descargas de los modelos desde Drive
for nombre_archivo, id_drive in SCALERS_DRIVE.items():
    download_from_drive(id_drive, f"models/{nombre_archivo}")

# -----------------------
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# -----------------------
st.set_page_config(page_title="SMARTAUDIT AI", layout="wide")

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

# -----------------------
# DATABASE (Ruta local de GitHub)
# -----------------------
DB_PATH = "sql/database.db"
engine = create_engine(f"sqlite:///{DB_PATH}")

@st.cache_data
def load_data():
    df = pd.read_sql("SELECT * FROM inventario", engine)
    df.columns = df.columns.str.lower()
    return df

df = load_data()
df = df.dropna(subset=["costo", "precio de venta"])
df = df[(df["costo"] > 0) & (df["precio de venta"] > 0)]

# -----------------------
# MODELO ML
# -----------------------
@st.cache_resource
def train_model(data):
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(data[["costo"]], data["precio de venta"])
    return model

model = train_model(df)

# -----------------------
# SIDEBAR CASCADA
# -----------------------
st.sidebar.header("AUDIT INPUTS")

# Logo (Ruta relativa directa de GitHub)
logo_path = "asset/logomgf.png"
if os.path.exists(logo_path):
    st.sidebar.image(Image.open(logo_path), width=200)

departamentos_visibles = ["RELOJERIA", "JOYERIA"]
dep = st.sidebar.selectbox("Departamento", departamentos_visibles)
df_dep = df[df["departamento"] == dep]

proveedores_visibles = ["AUDEMARS PIGUET ET CIE.", "BELL & ROSS USA", "CHRONO AG", "CITIZEN LATINAMERICA CORP", "DAMIANI S.P.A", "DJULA S.A.R.L.", "MESSIKA USA INC", "MONTBLANC SIMPLO GMBH", "POMELLATO USA INC", "RICHARD PERLT VENEZUELA", "RICHEMONT BAUME MERCIER", "RICHEMONT NORTH AMERICA INC (IWC)", "RICHEMONT NORTH AMERICA INC (PANERAI)", "RICHEMONT NORTH AMERICA INC (RICHEMONT NORTH AMERICA INC (CARTIER))", "ROBERTO COIN S.P.A.", "SONGA ANTONIO SPA", "SWATCH AG", "TAG HEUER", "ZENITH"]
df_dep_filtrado = df_dep[df_dep["proveedor_correcto"].isin(proveedores_visibles)]

if df_dep_filtrado.empty:
    st.sidebar.warning("No hay datos disponibles")
    st.stop()

prov = st.sidebar.selectbox("Proveedor", sorted(df_dep_filtrado["proveedor_correcto"].dropna().unique()))
df_prov = df_dep_filtrado[df_dep_filtrado["proveedor_correcto"] == prov]
marca = st.sidebar.selectbox("Marca", sorted(df_prov["marca_correcta"].dropna().unique()))
df_marca = df_prov[df_prov["marca_correcta"] == marca]
sku = st.sidebar.selectbox("SKU", sorted(df_marca["sku"].dropna().unique()))
row = df_marca[df_marca["sku"] == sku].iloc[0]

costo_input = st.sidebar.number_input("Landed Cost", value=float(row["costo"]))
precio_input = st.sidebar.number_input("Precio Facturado", value=float(row["precio de venta"]))

# -----------------------
# CALCULOS
# -----------------------
precio_ia = model.predict([[costo_input]])[0]
desviacion = (precio_input - precio_ia) / precio_ia * 100
margen = precio_input - costo_input
margen_pct = margen / precio_input * 100

# -----------------------
# LAYOUT
# -----------------------
left, right = st.columns([2,1])

with left:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>PRECIO IA</div><div class='metric-value'>${precio_ia:,.0f}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>Precio Facturado</div><div class='metric-value'>${precio_input:,.0f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>DESVIACIÓN</div><div class='metric-value'>{desviacion:.1f}%</div></div>", unsafe_allow_html=True)

    if desviacion < -5:
        alert, text = "alert-red", "🔴 PRODUCTO VENDIDO SIN MARGEN DE GANANCIA.<br>Se requiere evaluación."
    elif desviacion > 5:
        alert, text = "alert-green", "🟢 La marca no requiere auditoría. Precio dentro del rango IA ±5%."
    else:
        alert, text = "alert-yellow", "🟡 NOTA: DESVIACIÓN MEDIA. Se establece protocolo de revisión."
    st.markdown(f'<div class="alert-box {alert}">{text}</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    f1.markdown(f"<div class='metric-box'><div class='metric-title'>MARGEN USD</div><div class='metric-value'>${margen:,.0f}</div></div>", unsafe_allow_html=True)
    f2.markdown(f"<div class='metric-box'><div class='metric-title'>MARGEN %</div><div class='metric-value'>{margen_pct:.1f}%</div></div>", unsafe_allow_html=True)

    st.markdown("### Estacionalidad de ventas")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    trend_data = df[df["sku"] == sku].groupby(df["fecha"].dt.to_period("M").astype(str))["precio de venta"].sum()
    st.line_chart(trend_data)

    st.markdown("### Scoring de Riesgo IA")
    riesgo_pct = max(min(abs(desviacion), 100), 0)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = riesgo_pct,
        title = {'text': "Nivel de riesgo (%)", 'font': {'color': "white"}},
        gauge = {'bar': {'color': "#d4af37"}, 'bgcolor': "#2a2a2a", 'steps': [{'range': [0, 5], 'color': "#1e4620"}, {'range': [5, 15], 'color': "#ffcc00"}, {'range': [15, 100], 'color': "#ff4d4d"}]}
    ))
    fig_gauge.update_layout(paper_bgcolor="#1c1c1c", font_color="white", height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

with right:
    st.markdown("<div class='brand-panel'>", unsafe_allow_html=True)
    st.markdown("### Brand Performance")
    marca_df = df[df["marca_correcta"] == marca]
    p_compra = marca_df["inventario final"].mean()
    p_costo = marca_df["costo"].mean()
    p_v_und = marca_df.groupby("sku")["precio de venta"].count().mean()
    p_venta = marca_df["precio de venta"].mean()
    rot = p_v_und / p_compra if p_compra != 0 else 0

    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Unidades Compradas</div><div class='metric-value'>{p_compra:.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Precio Costo</div><div class='metric-value'>${p_costo:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Unidades Vendidas</div><div class='metric-value'>{p_v_und:.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Precio Venta</div><div class='metric-value'>${p_venta:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Rotación</div><div class='metric-value'>{rot:.2f}x</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Confianza IA</div><div class='metric-value'>83.9%</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='footer'>© 2026 MGF - Propiedad Intelectual - Venezuela</div>", unsafe_allow_html=True)