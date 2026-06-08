"""scripts/build_maps.py — Costruisce le mappe coropletiche IDPT.

Output:
- ``output/visualizations/idpt_map.html`` — mappa principale interattiva
  con IDPT aggregato sui 107 territori provinciali. Popup ricco al click:
  codice ISTAT, nome AGID, IDPT aggregato + 3 componenti.
- ``output/visualizations/idpt_components.html`` — 4 mappe affiancate
  (3 componenti elementari + aggregato) per confronto visuale dei pattern.

Tecnologia: Folium (Leaflet HTML standalone). Scala colori a 5 quintili
giallo→rosso (YlOrRd). Sorgente IDPT: ``output/computed/cubo8_idpt_computed.ttl``
letto via rdflib. Sorgente geometrie: GeoJSON province italiane da
``data/limits_IT_provinces.geojson`` (scaricato automaticamente al primo
run da github.com/openpolis/geojson-italy se mancante).

Esecuzione:
    source .venv/bin/activate
    python scripts/build_maps.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))


CUBO8_TTL = PROJECT_ROOT / "output" / "computed" / "cubo8_idpt_computed.ttl"
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
GEOJSON_PATH = PROJECT_ROOT / "data" / "limits_IT_provinces.geojson"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/openpolis/geojson-italy/master/"
    "geojson/limits_IT_provinces.geojson"
)
OUTPUT_DIR = PROJECT_ROOT / "output" / "visualizations"


COMPONENT_LABELS = {
    "press-dem": "Pressione demografica",
    "peso-eco":  "Peso economico delle pensioni",
    "ered-st":   "Eredità storica delle riforme",
    "agg":       "IDPT aggregato",
}

# Mappa componente short → URI SKOS Concept idpt (per il filtro SPARQL)
COMPONENT_URI_SHORT = {
    "press-dem": "https://example.org/idpt/componente-pressione-demografica",
    "peso-eco":  "https://example.org/idpt/componente-peso-economico",
    "ered-st":   "https://example.org/idpt/componente-eredita-storica",
    "agg":       "https://example.org/idpt/idpt-aggregato",
}


def download_geojson_if_missing() -> None:
    """Scarica il GeoJSON province italiane se mancante."""
    if GEOJSON_PATH.exists():
        return
    print(f"GeoJSON province italiane non trovato in {GEOJSON_PATH}")
    print(f"Scaricando da {GEOJSON_URL} (~6 MB)...")
    import urllib.request
    GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(GEOJSON_URL, str(GEOJSON_PATH))
    size_mb = GEOJSON_PATH.stat().st_size / 1024 / 1024
    print(f"✓ GeoJSON scaricato ({size_mb:.1f} MB)")


def load_idpt_dataframe() -> pd.DataFrame:
    """Carica il cubo 8 e ritorna df pivot con 1 riga per provincia × 4 colonne."""
    from rdflib import Graph

    g = Graph()
    g.parse(str(CUBO8_TTL), format="turtle")
    g.parse(str(PROVINCES_TTL), format="turtle")

    rows = list(g.query("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?codice_istat ?nome ?componente_uri ?valore
    WHERE {
      ?obs qb:dataSet idpt:cubo-idpt-computed ;
           idpt:provincia ?p ;
           idpt:componenteIDPT ?c ;
           idpt:valoreIDPT ?valore .
      ?p skos:notation ?codice_istat ;
         skos:prefLabel ?nome .
      FILTER(LANG(?nome) = "it")
      BIND(STR(?c) AS ?componente_uri)
    }
    """))
    long_df = pd.DataFrame([
        {"codice_istat": str(r[0]), "nome": str(r[1]),
         "componente_uri": str(r[2]), "valore": float(r[3])}
        for r in rows
    ])
    # Map URI → componente short
    uri_to_short = {v: k for k, v in COMPONENT_URI_SHORT.items()}
    long_df["componente_short"] = long_df["componente_uri"].map(uri_to_short)

    # Pivot: 1 riga per provincia, 4 colonne misure (press-dem, peso-eco, ered-st, agg)
    pivot = long_df.pivot_table(
        index=["codice_istat", "nome"],
        columns="componente_short",
        values="valore",
    ).reset_index()
    return pivot


def build_main_map(df: pd.DataFrame) -> None:
    """Mappa principale interattiva: IDPT aggregato choropleth + popup ricco."""
    import folium

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Mappa centrata sull'Italia
    m = folium.Map(location=[42.5, 12.5], zoom_start=6, tiles="cartodbpositron")

    # Carica GeoJSON
    import json
    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    # Identifico il nome della property che contiene il codice ISTAT province
    # (openpolis usa "prov_istat_code_num" o "prov_istat_code")
    first_feat = geojson["features"][0]["properties"]
    if "prov_istat_code_num" in first_feat:
        code_prop = "prov_istat_code_num"
    elif "prov_istat_code" in first_feat:
        code_prop = "prov_istat_code"
    else:
        code_prop = list(first_feat.keys())[0]
        print(f"⚠ Property codice provincia non riconosciuta, uso '{code_prop}'")

    # Robustezza match: openpolis può usare int o stringa zero-padded.
    # Normalizzo il df allo stesso tipo del GeoJSON.
    sample_code = first_feat[code_prop]
    df = df.copy()
    if isinstance(sample_code, int):
        df["codice_istat_match"] = df["codice_istat"].astype(int)
    else:
        df["codice_istat_match"] = df["codice_istat"].astype(str)

    # Mappa codice_istat → riga df (per popup)
    df_idx = df.set_index("codice_istat")

    # Choropleth: scala quintili giallo→rosso su IDPT aggregato
    bins = list(df["agg"].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    folium.Choropleth(
        geo_data=geojson,
        data=df,
        columns=["codice_istat_match", "agg"],
        key_on=f"feature.properties.{code_prop}",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.4,
        line_color="white",
        legend_name="IDPT aggregato (5 quintili)",
        bins=bins,
        nan_fill_color="#cccccc",
        nan_fill_opacity=0.3,
    ).add_to(m)

    # Aggiungi popup per ogni provincia (overlay GeoJson invisibile sopra il choropleth)
    def style_function(_feat):
        return {"fillOpacity": 0, "weight": 0}

    def highlight_function(_feat):
        return {"fillColor": "#000000", "fillOpacity": 0.15, "weight": 2,
                "color": "#000000"}

    # Per il tooltip, devo iniettare le 4 misure IDPT nelle properties del GeoJSON
    for feat in geojson["features"]:
        code = str(feat["properties"][code_prop]).zfill(3)
        if code in df_idx.index:
            row = df_idx.loc[code]
            feat["properties"]["_nome"] = row["nome"]
            feat["properties"]["_idpt_agg"] = f"{row['agg']:.3f}"
            feat["properties"]["_d1"] = f"{row['press-dem']:.3f}"
            feat["properties"]["_d2"] = f"{row['peso-eco']:.3f}"
            feat["properties"]["_d3"] = f"{row['ered-st']:.3f}"
        else:
            feat["properties"]["_nome"] = "?"
            feat["properties"]["_idpt_agg"] = "?"

    folium.GeoJson(
        geojson,
        name="Province italiane",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["_nome", code_prop, "_idpt_agg", "_d1", "_d2", "_d3"],
            aliases=["Provincia:", "Codice ISTAT:", "IDPT aggregato:",
                     "D1 pressione demografica:", "D2 peso economico:",
                     "D3 eredità storica:"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    # Titolo HTML — centrato orizzontalmente in alto.
    title_html = """
    <div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
                z-index: 9999; background: white; padding: 10px 15px;
                border: 2px solid #555; border-radius: 6px;
                font-family: sans-serif; max-width: 520px; text-align: center;">
      <b>Atlante della dipendenza previdenziale italiana — IDPT 2026</b><br>
      <span style="font-size: 12px; color: #555;">
      Indice composito di 3 componenti elementari normalizzate min-max.
      Passa il mouse su una provincia per vedere il dettaglio.
      </span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Sidebar fluttuante con classifica completa delle 107 province
    sidebar_html = _build_sidebar_html(df, bins)
    m.get_root().html.add_child(folium.Element(sidebar_html))

    output = OUTPUT_DIR / "idpt_map.html"
    m.save(str(output))
    print(f"✓ Mappa principale salvata: {output}")


def _build_sidebar_html(df: pd.DataFrame, bins: list[float]) -> str:
    """Genera l'HTML della sidebar fluttuante con la classifica IDPT.

    La sidebar è ``position: fixed`` sulla sinistra del viewport e contiene
    una tabella scrollabile con tutte le 107 province ordinate dall'IDPT
    aggregato più alto al più basso. Ogni riga ha background colorato in
    base al quintile di IDPT (stessa palette giallo→rosso del choropleth
    della mappa), in modo da rendere visivamente coerente la classifica
    con la mappa di sfondo.

    Args:
        df: DataFrame con colonne codice_istat, nome, agg (+ 3 componenti).
        bins: I 5 quantili calcolati per il choropleth, riusati per
            assegnare il colore del background a ogni riga della classifica.

    Returns:
        Stringa HTML pronta per essere wrappata in folium.Element().
    """
    df_sorted = df.sort_values("agg", ascending=False).reset_index(drop=True)

    # Palette YlOrRd a 5 colori, coerente con la scala del choropleth Folium.
    quintile_colors = ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]
    # Colore del testo: invertito per i quintili più scuri (leggibilità).
    text_colors = ["#222222", "#222222", "#222222", "#ffffff", "#ffffff"]

    def color_pair_for_value(v: float) -> tuple[str, str]:
        # bins è lista di 6 elementi: [min, q20, q40, q60, q80, max].
        # Assegna il quintile in base a quale soglia il valore raggiunge.
        for i, threshold in enumerate(bins[1:], start=0):
            if v <= threshold:
                idx = min(i, 4)
                return quintile_colors[idx], text_colors[idx]
        return quintile_colors[4], text_colors[4]

    rows_html = []
    for i, row in df_sorted.iterrows():
        rank = i + 1
        bg, fg = color_pair_for_value(row["agg"])
        # data-name in lowercase per il filtraggio JS della ricerca
        name_lower = row["nome"].lower()
        rows_html.append(
            f'<tr data-name="{name_lower}" style="background-color: {bg}; color: {fg};">'
            f'<td style="text-align: right; padding: 3px 6px; font-weight: bold;">{rank}</td>'
            f'<td style="padding: 3px 6px;">{row["nome"]}</td>'
            f'<td style="text-align: right; padding: 3px 6px; '
            f'font-family: monospace;">{row["agg"]:.3f}</td>'
            f'</tr>'
        )
    rows_block = "".join(rows_html)

    # JavaScript inline per il filtraggio in tempo reale della classifica.
    # Definito come funzione globale e legato via oninput sull'<input>, in modo
    # da non dipendere dal load order degli script Folium.
    filter_script = """
    <script>
    function filterIdptRows(query) {
        var q = (query || '').toLowerCase().trim();
        var rows = document.querySelectorAll('#idpt-sidebar tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var name = rows[i].getAttribute('data-name') || '';
            rows[i].style.display = (q === '' || name.indexOf(q) !== -1) ? '' : 'none';
        }
    }
    </script>
    """

    # La sidebar è posizionata a top: 80px per non coprire i controlli zoom
    # di Leaflet (posizionati di default a top: 10px / left: 10px), e con
    # max-height calcolata per lasciare margine in basso.
    sidebar_html = f"""
    {filter_script}
    <div id="idpt-sidebar" style="
        position: fixed; top: 80px; left: 20px; z-index: 9998;
        width: 320px; max-height: calc(100vh - 110px);
        background: white; border: 2px solid #555; border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        font-family: sans-serif;
        display: flex; flex-direction: column;">
      <div style="padding: 10px 12px; border-bottom: 1px solid #ccc;
                  background: #f5f5f5; border-radius: 4px 4px 0 0;
                  flex-shrink: 0;">
        <b style="font-size: 14px;">Classifica IDPT 2026</b><br>
        <span style="font-size: 11px; color: #666;">
          107 province ordinate dall'IDPT più alto al più basso.
          Background colorato per quintile (giallo → rosso).
        </span>
        <div style="margin-top: 8px;">
          <input type="text"
                 placeholder="Cerca provincia..."
                 oninput="filterIdptRows(this.value)"
                 style="width: 100%; box-sizing: border-box; padding: 5px 8px;
                        border: 1px solid #bbb; border-radius: 4px;
                        font-size: 12px; font-family: sans-serif;"/>
        </div>
      </div>
      <div style="overflow-y: auto; flex: 1;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
          <thead style="position: sticky; top: 0; background: #fafafa;
                        border-bottom: 1px solid #ccc; z-index: 1;">
            <tr>
              <th style="padding: 6px; text-align: right; font-weight: 600;">#</th>
              <th style="padding: 6px; text-align: left; font-weight: 600;">Provincia</th>
              <th style="padding: 6px; text-align: right; font-weight: 600;">IDPT</th>
            </tr>
          </thead>
          <tbody>{rows_block}</tbody>
        </table>
      </div>
    </div>
    """
    return sidebar_html


def build_embed_map(df: pd.DataFrame) -> None:
    """Mappa minimale ottimizzata per iframe (no sidebar classifica, no title).

    Pensata per essere embeddata in ``docs/index.html`` dove l'iframe è
    di dimensioni ridotte (~500-700px altezza): rimuoviamo la sidebar
    fluttuante e il titolo, lasciamo solo il choropleth + tooltip + legenda
    Folium nativa (in basso a destra). Tutta la superficie va alla mappa.
    """
    import folium
    import json

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    m = folium.Map(location=[42.5, 12.5], zoom_start=6, tiles="cartodbpositron")

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    first_feat = geojson["features"][0]["properties"]
    if "prov_istat_code_num" in first_feat:
        code_prop = "prov_istat_code_num"
    elif "prov_istat_code" in first_feat:
        code_prop = "prov_istat_code"
    else:
        code_prop = list(first_feat.keys())[0]

    sample_code = first_feat[code_prop]
    df = df.copy()
    if isinstance(sample_code, int):
        df["codice_istat_match"] = df["codice_istat"].astype(int)
    else:
        df["codice_istat_match"] = df["codice_istat"].astype(str)
    df_idx = df.set_index("codice_istat")

    bins = list(df["agg"].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
    folium.Choropleth(
        geo_data=geojson,
        data=df,
        columns=["codice_istat_match", "agg"],
        key_on=f"feature.properties.{code_prop}",
        fill_color="YlOrRd",
        fill_opacity=0.78,
        line_opacity=0.4,
        line_color="white",
        legend_name="IDPT aggregato (5 quintili)",
        bins=bins,
        nan_fill_color="#cccccc",
        nan_fill_opacity=0.3,
    ).add_to(m)

    def style_function(_feat):
        return {"fillOpacity": 0, "weight": 0}

    def highlight_function(_feat):
        return {"fillColor": "#000000", "fillOpacity": 0.15, "weight": 2,
                "color": "#000000"}

    for feat in geojson["features"]:
        code = str(feat["properties"][code_prop]).zfill(3)
        if code in df_idx.index:
            row = df_idx.loc[code]
            feat["properties"]["_nome"] = row["nome"]
            feat["properties"]["_idpt_agg"] = f"{row['agg']:.3f}"
            feat["properties"]["_d1"] = f"{row['press-dem']:.3f}"
            feat["properties"]["_d2"] = f"{row['peso-eco']:.3f}"
            feat["properties"]["_d3"] = f"{row['ered-st']:.3f}"
        else:
            feat["properties"]["_nome"] = "?"
            feat["properties"]["_idpt_agg"] = "?"

    folium.GeoJson(
        geojson,
        name="Province italiane",
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["_nome", "_idpt_agg", "_d1", "_d2", "_d3"],
            aliases=["Provincia:", "IDPT aggregato:",
                     "D1 pressione:", "D2 peso eco:", "D3 eredità:"],
            localize=True,
            sticky=True,
        ),
    ).add_to(m)

    output = OUTPUT_DIR / "idpt_map_embed.html"
    m.save(str(output))
    print(f"✓ Mappa embed (per iframe) salvata: {output}")


def build_components_map(df: pd.DataFrame) -> None:
    """4 mini-mappe affiancate (3 componenti + aggregato).

    Approccio iframe: ogni mappa è salvata come file HTML isolato in
    ``output/visualizations/_partial/idpt_<comp>.html``, e la pagina principale
    ``idpt_components.html`` le embeda via <iframe>. Questo evita conflitti
    JavaScript/CSS di Leaflet quando si caricano 4 istanze nella stessa pagina,
    e garantisce piena interattività (zoom/pan/tooltip indipendenti per mappa).
    """
    import folium
    import json

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    partial_dir = OUTPUT_DIR / "_partial"
    partial_dir.mkdir(exist_ok=True)

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    first_feat = geojson["features"][0]["properties"]
    code_prop = ("prov_istat_code_num" if "prov_istat_code_num" in first_feat
                 else "prov_istat_code")

    # Stesso fix di robustezza match int/str della mappa principale
    sample_code = first_feat[code_prop]
    df = df.copy()
    if isinstance(sample_code, int):
        df["codice_istat_match"] = df["codice_istat"].astype(int)
    else:
        df["codice_istat_match"] = df["codice_istat"].astype(str)
    df_idx = df.set_index("codice_istat")

    # Inietto i valori delle 4 misure nelle properties del GeoJSON (1 sola volta,
    # riusato per le 4 mappe).
    for feat in geojson["features"]:
        code = str(feat["properties"][code_prop]).zfill(3)
        if code in df_idx.index:
            row = df_idx.loc[code]
            feat["properties"]["_nome"] = row["nome"]
            feat["properties"]["_d1"] = f"{row['press-dem']:.3f}"
            feat["properties"]["_d2"] = f"{row['peso-eco']:.3f}"
            feat["properties"]["_d3"] = f"{row['ered-st']:.3f}"
            feat["properties"]["_agg"] = f"{row['agg']:.3f}"
        else:
            for k in ("_nome", "_d1", "_d2", "_d3", "_agg"):
                feat["properties"][k] = "?"

    components_order = ["press-dem", "peso-eco", "ered-st", "agg"]
    value_field_map = {
        "press-dem": "_d1",
        "peso-eco":  "_d2",
        "ered-st":   "_d3",
        "agg":       "_agg",
    }

    for comp in components_order:
        m = folium.Map(location=[42.5, 12.5], zoom_start=5, tiles="cartodbpositron")
        bins = list(df[comp].quantile([0, 0.2, 0.4, 0.6, 0.8, 1.0]))
        folium.Choropleth(
            geo_data=geojson,
            data=df,
            columns=["codice_istat_match", comp],
            key_on=f"feature.properties.{code_prop}",
            fill_color="YlOrRd",
            fill_opacity=0.8,
            line_opacity=0.3,
            line_color="white",
            legend_name=COMPONENT_LABELS[comp],
            bins=bins,
            nan_fill_color="#cccccc",
            nan_fill_opacity=0.3,
        ).add_to(m)

        # Overlay tooltip al passaggio mouse
        def style_function(_feat):
            return {"fillOpacity": 0, "weight": 0}
        def highlight_function(_feat):
            return {"fillColor": "#000000", "fillOpacity": 0.15,
                    "weight": 2, "color": "#000000"}
        folium.GeoJson(
            geojson,
            style_function=style_function,
            highlight_function=highlight_function,
            tooltip=folium.GeoJsonTooltip(
                fields=["_nome", code_prop,
                        value_field_map[comp],
                        "_d1", "_d2", "_d3", "_agg"],
                aliases=["Provincia:", "Codice ISTAT:",
                         f"{COMPONENT_LABELS[comp]}:",
                         "D1 pressione:", "D2 peso eco:",
                         "D3 eredità:", "IDPT aggregato:"],
                localize=True,
                sticky=True,
            ),
        ).add_to(m)

        partial_file = partial_dir / f"idpt_{comp}.html"
        m.save(str(partial_file))

    # Pagina principale con 4 iframe in CSS grid 2×2
    page = f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8"/>
  <title>IDPT 2026 — Confronto componenti</title>
  <style>
    body {{ margin: 0; font-family: sans-serif; background: #f5f5f5; }}
    h1 {{ text-align: center; padding: 15px; margin: 0; background: white;
         border-bottom: 1px solid #ccc; font-size: 18px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 10px; }}
    .panel {{ background: white; border: 1px solid #ccc; border-radius: 4px;
              padding: 8px; display: flex; flex-direction: column; }}
    .panel h3 {{ margin: 4px 0 8px 4px; font-size: 14px; color: #333; }}
    .panel iframe {{ width: 100%; height: 480px; border: 0; }}
    @media (max-width: 900px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <h1>Atlante della dipendenza previdenziale italiana — 4 componenti IDPT 2026</h1>
  <div class="grid">
    <div class="panel">
      <h3>D1 — {COMPONENT_LABELS['press-dem']}</h3>
      <iframe src="_partial/idpt_press-dem.html"></iframe>
    </div>
    <div class="panel">
      <h3>D2 — {COMPONENT_LABELS['peso-eco']}</h3>
      <iframe src="_partial/idpt_peso-eco.html"></iframe>
    </div>
    <div class="panel">
      <h3>D3 — {COMPONENT_LABELS['ered-st']}</h3>
      <iframe src="_partial/idpt_ered-st.html"></iframe>
    </div>
    <div class="panel">
      <h3>IDPT aggregato</h3>
      <iframe src="_partial/idpt_agg.html"></iframe>
    </div>
  </div>
</body>
</html>"""
    output = OUTPUT_DIR / "idpt_components.html"
    output.write_text(page, encoding="utf-8")
    print(f"✓ Mappa 4 componenti salvata: {output}")
    print(f"  + 4 mappe parziali in {partial_dir}")


def main() -> int:
    print("=== Build mappe coropletiche IDPT ===")
    print()

    if not CUBO8_TTL.exists():
        print(f"✗ Cubo 8 IDPT non trovato: {CUBO8_TTL}")
        print("  Esegui prima: python scripts/recipes/cubo8_idpt_computed.py")
        return 1

    download_geojson_if_missing()

    print()
    print("Carico cubo 8 IDPT computed via rdflib...")
    df = load_idpt_dataframe()
    print(f"✓ Dataframe IDPT: {df.shape[0]} province × {df.shape[1]} colonne")
    print(f"  Colonne: {list(df.columns)}")
    print()
    print("Top 5 province per IDPT aggregato:")
    print(df.nlargest(5, "agg")[["codice_istat", "nome", "agg"]].to_string(index=False))

    print()
    print("Genero mappa principale...")
    build_main_map(df)

    print()
    print("Genero mappa embed compatta (per iframe in docs/index.html)...")
    build_embed_map(df)

    print()
    print("Genero mappa 4 componenti affiancate...")
    build_components_map(df)

    print()
    print("=== Mappe pronte in output/visualizations/ ===")
    print(f"  → {OUTPUT_DIR / 'idpt_map.html'}")
    print(f"  → {OUTPUT_DIR / 'idpt_components.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
