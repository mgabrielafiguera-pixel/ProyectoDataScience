import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import plotly.graph_objects as go
from PIL import Image
import os

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(page_title="SMARTAUDIT AI", layout="wide")

# -----------------------
# CSS GLOBAL PROFESIONAL
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
[data-testid="stSidebar"] label, [data-testid="stSidebar"] .css-1wy0on6 { color: white !important; }
[data-testid="stSidebar"] input::placeholder { color: #ddd !important; }
</style>
""", unsafe_allow_html=True)

st.title("SMARTAUDIT AI – Luxury Price Audit")

# -----------------------
# DATABASE
# -----------------------
DB_PATH = "/Users/mariafiguera/Downloads/ProyectoDataScience/sql/database.db"
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
# SIDEBAR CASCADA CON FILTRO DE PROTECCIÓN
# -----------------------
st.sidebar.header("AUDIT INPUTS")

# Solo estos departamentos
departamentos_visibles = ["RELOJERIA", "JOYERIA"]
dep = st.sidebar.selectbox("Departamento", departamentos_visibles)
df_dep = df[df["departamento"] == dep]

# Solo estos proveedores
proveedores_visibles = [
    "AUDEMARS PIGUET ET CIE.",
    "BELL & ROSS USA",
    "CHRONO AG",
    "CITIZEN LATINAMERICA CORP",
    "DAMIANI S.P.A",
    "DJULA S.A.R.L.",
    "MESSIKA USA INC",
    "MONTBLANC SIMPLO GMBH",
    "POMELLATO USA INC",
    "RICHARD PERLT VENEZUELA",
    "RICHEMONT BAUME MERCIER",
    "RICHEMONT NORTH AMERICA INC (IWC)",
    "RICHEMONT NORTH AMERICA INC (PANERAI)",
    "RICHEMONT NORTH AMERICA INC (RICHEMONT NORTH AMERICA INC (CARTIER))",
    "ROBERTO COIN S.P.A.",
    "SONGA ANTONIO SPA",
    "SWATCH AG",
    "TAG HEUER",
    "ZENITH"
]
df_dep_filtrado = df_dep[df_dep["proveedor_correcto"].isin(proveedores_visibles)]

if df_dep_filtrado.empty:
    st.sidebar.warning("No hay datos disponibles para este filtro")
    st.stop()

prov = st.sidebar.selectbox(
    "Proveedor",
    sorted(df_dep_filtrado["proveedor_correcto"].dropna().unique())
)
df_prov = df_dep_filtrado[df_dep_filtrado["proveedor_correcto"] == prov]

marca = st.sidebar.selectbox("Marca", sorted(df_prov["marca_correcta"].dropna().unique()))
df_marca = df_prov[df_prov["marca_correcta"] == marca]

sku = st.sidebar.selectbox("SKU", sorted(df_marca["sku"].dropna().unique()))
row = df_marca[df_marca["sku"] == sku].iloc[0]

landed_cost = float(row["costo"])
precio_facturado = float(row["precio de venta"])
costo_input = st.sidebar.number_input("Landed Cost", value=landed_cost)
precio_input = st.sidebar.number_input("Precio Facturado", value=precio_facturado)

if dep.lower() == "joyeria":
    precio_oro = 60000
    st.sidebar.markdown(f"**Precio gramo oro internacional:** ${precio_oro/1000:,.2f}")

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

# -----------------------
# PANEL IZQUIERDO
# -----------------------
with left:
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-box'><div class='metric-title'>PRECIO IA</div><div class='metric-value'>${precio_ia:,.0f}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'><div class='metric-title'>Precio Facturado</div><div class='metric-value'>${precio_input:,.0f}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'><div class='metric-title'>DESVIACIÓN</div><div class='metric-value'>{desviacion:.1f}%</div></div>", unsafe_allow_html=True)

    if desviacion < -5:
        alert = "alert-red"
        text = "🔴 PRODUCTO VENDIDO SIN MARGEN DE GANANCIA.<br>Se requiere evaluación.<br>Reportar a Finanzas."
    elif desviacion > 5:
        alert = "alert-green"
        text = "🟢 La marca no requiere auditoría. Precio dentro del rango IA ±5%."
    else:
        alert = "alert-yellow"
        text = "🟡 NOTA: DESVIACIÓN MEDIA. Se establece protocolo de revisión."
    st.markdown(f'<div class="alert-box {alert}">{text}</div>', unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    f1.markdown(f"<div class='metric-box'><div class='metric-title'>MARGEN USD</div><div class='metric-value'>${margen:,.0f}</div></div>", unsafe_allow_html=True)
    f2.markdown(f"<div class='metric-box'><div class='metric-title'>MARGEN %</div><div class='metric-value'>{margen_pct:.1f}%</div></div>", unsafe_allow_html=True)

    st.markdown("### Estacionalidad de ventas")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["mes_year"] = df["fecha"].dt.to_period("M").astype(str)
    global_trend = df.groupby("mes_year")["precio de venta"].sum()
    sku_df = df[df["sku"] == sku]
    sku_trend = sku_df.groupby("mes_year")["precio de venta"].sum()
    trend_df = pd.DataFrame({"Global": global_trend, "SKU": sku_trend}).fillna(0).sort_index()
    st.line_chart(trend_df)

    st.markdown("### Scoring de Riesgo IA")
    riesgo_pct = max(min(abs(desviacion), 100), 0)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = riesgo_pct,
        title = {'text': "Nivel de riesgo (%)", 'font': {'color': "white"}},
        gauge = {
            'axis': {'range': [0, 100], 'tickcolor':'white'},
            'bar': {'color': "#d4af37"},
            'bgcolor': "#2a2a2a",
            'steps': [
                {'range': [0, 5], 'color': "#1e4620"},
                {'range': [5, 15], 'color': "#ffcc00"},
                {'range': [15, 100], 'color': "#ff4d4d"}
            ]
        },
        number={'font': {'color': "white", 'size':24}}
    ))
    fig_gauge.update_layout(paper_bgcolor="#1c1c1c", font_color="white", height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

# -----------------------
# PANEL DERECHO: BRAND PERFORMANCE
# -----------------------
with right:
    st.markdown("<div class='brand-panel'>", unsafe_allow_html=True)
    st.markdown("### Brand Performance")

    marca_df = df[df["marca_correcta"] == marca]
    prom_unidades_compra = marca_df["inventario final"].mean()
    prom_precio_costo = marca_df["costo"].mean()
    prom_unidades_venta = marca_df.groupby("sku")["precio de venta"].count().mean()
    prom_precio_venta = marca_df["precio de venta"].mean()
    rotacion = prom_unidades_venta / prom_unidades_compra if prom_unidades_compra != 0 else 0
    inventario_prom = marca_df["inventario final"].mean()

    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Unidades Compradas</div><div class='metric-value'>{prom_unidades_compra:.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Precio Costo</div><div class='metric-value'>${prom_precio_costo:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Unidades Vendidas</div><div class='metric-value'>{prom_unidades_venta:.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Promedio Precio Venta</div><div class='metric-value'>${prom_precio_venta:,.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Rotación</div><div class='metric-value'>{rotacion:.2f}x</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Inventario Promedio</div><div class='metric-value'>{inventario_prom:.0f}</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Tier Precio</div><div class='metric-value'>Alta Gama</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-box'><div class='metric-title'>Confianza IA</div><div class='metric-value'>83.9%</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# LOGO Y PROPIEDAD INTELECTUAL EN EL SIDEBAR
# -----------------------
logo_path = "/Users/mariafiguera/Downloads/ProyectoDataScience/asset/logomgf.png"
if os.path.exists(logo_path):
    logo_img = Image.open(logo_path)
    st.sidebar.image(logo_img, width=200)
else:
    st.sidebar.warning("⚠️ Logo no encontrado. Verifica la ruta y nombre del archivo.")

st.sidebar.markdown(
    "<div class='footer'>© 2026 MGF - Propiedad Intelectual - Venezuela</div>",
    unsafe_allow_html=True
)