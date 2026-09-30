"""Scraping de precios de mercado de relojes de lujo (mercado secundario).

Fuente: European Watch Company (https://www.europeanwatch.com). Su robots.txt permite
rastrear las páginas de marca (Allow: /). Cada página de marca incluye los relojes
en stock como datos estructurados schema.org (ItemList -> Product -> Offer), de donde
se extraen nombre, referencia, precio en USD y estado.

Uso:
    python scripts/scraping_relojes.py

Resultado: data/external/precios_mercado_relojes.csv
"""
import json
import re
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "data" / "external" / "precios_mercado_relojes.csv"

URL_MARCA = "https://www.europeanwatch.com/brand/{slug}"
MARCAS = {
    "Rolex": "rolex",
    "Patek Philippe": "patek-philippe",
    "Audemars Piguet": "audemars-piguet",
    "Omega": "omega",
    "Cartier": "cartier",
    "Hublot": "hublot",
    "IWC": "iwc",
    "Panerai": "panerai",
    "TAG Heuer": "tag-heuer",
    "Zenith": "zenith",
}
PAUSA_SEGUNDOS = 10  # pausa entre peticiones para no sobrecargar la web
HEADERS = {"User-Agent": "Mozilla/5.0 (proyecto academico 4Geeks - SmartAudit)"}

# Material a partir del nombre (abreviaturas o palabras). El orden importa: bicolor primero.
MATERIALES = [
    (r"\bSS/(YG|RG|WG)\b|\bTT\b|Two[- ]Tone|Rolesor|Steel (and|&) (Yellow |Rose |White )?Gold", "Acero y oro"),
    (r"\bPT\b|Platinum", "Platino"),
    (r"\bWG\b|White Gold", "Oro blanco"),
    (r"\bRG\b|Rose Gold|Everose|Sedna|King Gold|Red Gold|Goldtech|Pink Gold", "Oro rosa"),
    (r"\bYG\b|Yellow Gold", "Oro amarillo"),
    (r"\bTI\b|Titanium|Titanio|Ceratanium", "Titanio"),
    (r"\bCER\b|Ceramic|Ceramica|Cermet", "Cerámica"),
    (r"Carbon|Carbotech", "Carbono"),
    (r"Bronz", "Bronce"),
    (r"\bSS\b|Steel|Acciaio|Oystersteel", "Acero"),
    (r"\bGold\b|18K", "Oro"),
]


def descargar_pagina(slug):
    respuesta = requests.get(URL_MARCA.format(slug=slug), headers=HEADERS, timeout=30)
    respuesta.raise_for_status()
    return respuesta.text


def extraer_relojes(html, marca):
    """Lee el bloque ItemList de schema.org y devuelve una fila por reloj."""
    sopa = BeautifulSoup(html, "html.parser")
    filas = []
    for script in sopa.find_all("script", type="application/ld+json"):
        datos = json.loads(script.string)
        if datos.get("@type") != "ItemList":
            continue
        for elemento in datos["itemListElement"]:
            producto = elemento["item"]
            oferta = producto.get("offers", {})
            nombre = producto["name"]
            modelo = nombre[len(marca):].strip() if nombre.lower().startswith(marca.lower()) else nombre
            anio = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", nombre)
            material = next((m for patron, m in MATERIALES if re.search(patron, nombre, re.IGNORECASE)), "Otro")
            primera = modelo.split()[0] if modelo else ""
            filas.append({
                "marca": marca,
                "nombre": nombre,
                "referencia": primera if re.search(r"\d", primera) else None,  # solo si parece una referencia
                "material": material,
                "anio": int(anio.group(1)) if anio else None,
                "precio_usd": oferta.get("price"),
                "moneda": oferta.get("priceCurrency"),
                "estado": str(oferta.get("itemCondition", "")).rsplit("/", 1)[-1].replace("Condition", ""),
                "id_fuente": producto.get("sku"),
                "url": producto.get("url"),
            })
    return filas


def main():
    todas = []
    for i, (marca, slug) in enumerate(MARCAS.items()):
        if i > 0:
            time.sleep(PAUSA_SEGUNDOS)
        try:
            filas = extraer_relojes(descargar_pagina(slug), marca)
        except requests.RequestException as e:
            print(f"✗ {marca}: {e}")
            continue
        print(f"✔ {marca}: {len(filas)} relojes")
        todas.extend(filas)

    df = pd.DataFrame(todas)
    df["precio_usd"] = pd.to_numeric(df["precio_usd"], errors="coerce")
    df = df.dropna(subset=["precio_usd"]).drop_duplicates(subset="id_fuente")
    df["fecha_scraping"] = date.today().isoformat()

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(SALIDA, index=False)
    print(f"\nGuardado: {SALIDA.relative_to(ROOT)} ({len(df)} relojes, {df['marca'].nunique()} marcas)")


if __name__ == "__main__":
    main()
