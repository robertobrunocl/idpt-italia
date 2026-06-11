"""scripts/recipes/cubo8_idpt_computed.py — Recipe cubo 8 IDPT computed.

Il cuore narrativo del progetto: l'Indice di Dipendenza Previdenziale
Territoriale (IDPT), materializzato in grafo nominato separato
``graph:idpt-computed`` (file ``output/computed/cubo8_idpt_computed.ttl``).

L'IDPT ha 3 componenti elementari + 1 aggregato per ognuna delle 107
province italiane × 1 anno (2026) = **428 obs**.

Formule (decisioni Fase 6 Roberto):
- D1 pressione demografica  = pensioni_vigenti / occupati × 1000
- D2 peso economico         = monte_pensioni (€) / monte_redditi_da_lavoro (€)
- D3 eredità storica        = (pensioni_retributivo_cubo2 + cubo9) / totale_pensioni_con_regime
- Normalizzazione: min-max sui 107 valori per ogni componente
- Aggregato finale          = media aritmetica delle 3 componenti normalizzate

Sardegna 1:N (CA + Sud Sardegna): D3 replicato (entrambe ricevono valore della
sede aggregata) — decisione (a) della Fase 6, con rdfs:comment esplicativo.

Tutte le 428 obs hanno:
- ``sdmx-attribute:obsStatus sdmx-code:obsStatus-E`` (Estimated)
- ``prov:wasDerivedFrom`` verso le obs primarie usate nel calcolo

Esecuzione:
    source .venv/bin/activate
    python scripts/recipes/cubo8_idpt_computed.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "macrorefine" / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "recipes"))

from macrorefine import Dataset  # noqa: E402
from macrorefine.steps.lod import EmitQbObservations  # noqa: E402

import idpt_vocab as V  # noqa: E402

def _q(template: str) -> str:
    # Sostituisce il namespace idpt placeholder con quello attuale di V.IDPT_NS.
    # Permette di tenere i template SPARQL leggibili (con namespace placeholder
    # `https://example.org/idpt/`) ma di eseguirli correttamente anche dopo che
    # `scripts/finalize_namespace.py` ha aggiornato V.IDPT_NS al deploy GitHub
    # Pages. Senza questa funzione le query non troverebbero nulla nei TTL
    # emessi dopo il rename del namespace.
    return template.replace(
        "PREFIX idpt: <https://example.org/idpt/>",
        f"PREFIX idpt: <{V.IDPT_NS}>",
    )



OUTPUT_TTL = PROJECT_ROOT / "output" / "computed" / "cubo8_idpt_computed.ttl"

INPUT_TTLS = [
    PROJECT_ROOT / "output" / "observations" / "cubo1_vigenti_residenza.ttl",
    PROJECT_ROOT / "output" / "observations" / "cubo5_occupati_istat.ttl",
    PROJECT_ROOT / "output" / "observations" / "cubo7_redditi_mef.ttl",
    PROJECT_ROOT / "output" / "observations" / "cubo2_regime_sede.ttl",
    PROJECT_ROOT / "output" / "observations" / "cubo9_plan_b_gdp_projected.ttl",
    PROJECT_ROOT / "output" / "vocabularies" / "code_lists.ttl",
    PROJECT_ROOT / "output" / "mappings" / "inps_to_agid.ttl",
    PROJECT_ROOT / "data" / "provinces.ttl",
]

COMPONENT_URIS = {
    "press-dem": V.COMP_PRESSIONE_DEMOGRAFICA,
    "peso-eco":  V.COMP_PESO_ECONOMICO,
    "ered-st":   V.COMP_EREDITA_STORICA,
    "agg":       V.IDPT_AGGREGATO,
}


def _load_grafo():
    """Carica tutti i TTL necessari in un grafo rdflib in-memory."""
    from rdflib import Graph
    g = Graph()
    for ttl in INPUT_TTLS:
        g.parse(str(ttl), format="turtle")
    return g


def _compute_raw_components(g) -> pd.DataFrame:
    """Calcola D1, D2, D3 grezzi + tutte le obs sorgenti per ogni provincia.

    Returns:
        DataFrame con 107 righe e colonne: codice_istat, uri_agid, d1, d2, d3,
        prov_uris_d1, prov_uris_d2, prov_uris_d3 (liste di URI obs sorgenti).
    """
    # ---- D1: pensioni vigenti TOTALI / occupati × 1000 ----
    rows_d1 = list(g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?istat ?p ?obs_pens ?obs_occ ?n_pens ?n_occ_k WHERE {
      ?obs_pens qb:dataSet idpt:cubo-pensioni-vigenti-residenza ;
                idpt:provincia ?p ;
                idpt:tipoGestione idpt:gestione-totale ;
                idpt:numeroPensioni ?n_pens .
      ?obs_occ qb:dataSet idpt:cubo-occupati-istat ;
               idpt:provincia ?p ;
               idpt:numeroOccupati ?n_occ_k .
      ?p skos:notation ?istat .
    }
    """)))
    df = pd.DataFrame([
        {
            "istat":      str(r[0]),
            "uri_agid":   str(r[1]),
            "obs_pens_tot": str(r[2]),
            "obs_occ":    str(r[3]),
            "n_pens":     int(r[4]),
            "n_occ":      float(r[5]) * 1000,
        } for r in rows_d1
    ])
    df["d1"] = df["n_pens"] / df["n_occ"]
    df["prov_uris_d1"] = df.apply(
        lambda r: [r["obs_pens_tot"], r["obs_occ"]], axis=1
    )

    # ---- D2: monte pensioni € / monte redditi € ----
    monte_pens_df = pd.DataFrame([
        {"istat": str(r[0]), "uri_agid": str(r[1]), "obs_pens_ann": str(r[2]),
         "monte_pens_mln": float(r[3])}
        for r in g.query(_q("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX idpt: <https://example.org/idpt/>
        SELECT ?istat ?p ?obs ?monte_pens_mln WHERE {
          ?obs qb:dataSet idpt:cubo-pensioni-vigenti-residenza ;
               idpt:provincia ?p ;
               idpt:tipoGestione idpt:gestione-totale ;
               idpt:importoAnnuoComplessivo ?monte_pens_mln .
          ?p skos:notation ?istat .
        }
        """))
    ])

    # Per il monte redditi: somma 5 voci v2/v4/v5/v6/v7 + lista delle 5 obs sorgenti per provincia
    monte_redd_df_rows = []
    obs_redd_per_prov: dict[str, list[str]] = {}
    for r in g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?istat ?obs ?amm WHERE {
      ?obs qb:dataSet idpt:cubo-redditi-mef ;
           idpt:provincia ?p ;
           idpt:ammontareTotale ?amm .
      ?p skos:notation ?istat .
    }
    """)):
        istat, obs, amm = str(r[0]), str(r[1]), float(r[2])
        monte_redd_df_rows.append({"istat": istat, "amm": amm})
        obs_redd_per_prov.setdefault(istat, []).append(obs)
    monte_redd_df = (
        pd.DataFrame(monte_redd_df_rows)
        .groupby("istat", as_index=False)["amm"].sum()
        .rename(columns={"amm": "monte_redd"})
    )

    df = df.merge(monte_pens_df[["istat", "obs_pens_ann", "monte_pens_mln"]], on="istat")
    df = df.merge(monte_redd_df, on="istat")
    df["monte_pens"] = df["monte_pens_mln"] * 1_000_000
    df["d2"] = df["monte_pens"] / df["monte_redd"]
    df["prov_uris_d2"] = df.apply(
        lambda r: [r["obs_pens_ann"]] + obs_redd_per_prov.get(r["istat"], []), axis=1
    )

    # ---- D3: pensioni retributivo / totale con regime ----
    # Cubo 2 retributivo per sede (via correspondsToProvinceAGID 1:1)
    rows_d3_2 = list(g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?istat ?obs ?n WHERE {
      ?sede idpt:correspondsToProvinceAGID ?p .
      ?obs qb:dataSet idpt:cubo-pensioni-regime-sede ;
           idpt:sedeINPS ?sede ;
           idpt:regimeLiquidazione idpt:regime-retributivo ;
           idpt:numeroPensioni ?n .
      ?p skos:notation ?istat .
    }
    """)))
    d3_2 = {str(r[0]): (str(r[1]), int(r[2])) for r in rows_d3_2}

    # Cubo 2 retributivo per sede aggregata "CAGLIARI E SUD SARDEGNA" — decisione (a):
    # replica l'intero valore su entrambe le province aggregate (092 + 111)
    rows_d3_2_agg = list(g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?obs ?n WHERE {
      ?sede idpt:aggregatesProvince ?p ;
            idpt:aggregatesProvince ?p2 .
      FILTER(?p != ?p2)
      ?obs qb:dataSet idpt:cubo-pensioni-regime-sede ;
           idpt:sedeINPS ?sede ;
           idpt:regimeLiquidazione idpt:regime-retributivo ;
           idpt:numeroPensioni ?n .
    } LIMIT 1
    """)))
    if rows_d3_2_agg:
        sede_agg_obs, n_agg = str(rows_d3_2_agg[0][0]), int(rows_d3_2_agg[0][1])
        for istat in ("092", "111"):  # Cagliari + Sud Sardegna
            d3_2[istat] = (sede_agg_obs, n_agg)

    # Cubo 9 retributivo (Plan B Pubblici) per provincia
    rows_d3_9 = list(g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?istat ?obs ?n WHERE {
      ?obs qb:dataSet idpt:cubo-plan-b-gdp-projected ;
           idpt:provincia ?p ;
           idpt:regimeLiquidazione idpt:regime-retributivo ;
           idpt:numeroPensioni ?n .
      ?p skos:notation ?istat .
    }
    """)))
    d3_9 = {str(r[0]): (str(r[1]), float(r[2])) for r in rows_d3_9}

    # Denominatore: PRIV+PUB+AUTO da cubo 1 per provincia (escludo Assistenziali, no regime)
    denom_rows: dict[str, list] = {}
    for r in g.query(_q("""
    PREFIX qb: <http://purl.org/linked-data/cube#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX idpt: <https://example.org/idpt/>
    SELECT ?istat ?obs ?n WHERE {
      ?obs qb:dataSet idpt:cubo-pensioni-vigenti-residenza ;
           idpt:provincia ?p ;
           idpt:tipoGestione ?g ;
           idpt:numeroPensioni ?n .
      FILTER(?g IN (idpt:gestione-privati, idpt:gestione-pubblici, idpt:gestione-autonomi-parasub))
      ?p skos:notation ?istat .
    }
    """)):
        denom_rows.setdefault(str(r[0]), []).append((str(r[1]), int(r[2])))

    d3_data = []
    for istat, items in denom_rows.items():
        denom = sum(n for _, n in items)
        denom_obs = [obs for obs, _ in items]
        retr2_obs, retr2_n = d3_2.get(istat, (None, 0))
        retr9_obs, retr9_n = d3_9.get(istat, (None, 0))
        d3_value = (retr2_n + retr9_n) / denom if denom > 0 else 0.0
        prov_uris = [u for u in denom_obs + [retr2_obs, retr9_obs] if u]
        d3_data.append({"istat": istat, "d3": d3_value, "prov_uris_d3": prov_uris})
    d3_df = pd.DataFrame(d3_data)
    df = df.merge(d3_df, on="istat")

    return df[["istat", "uri_agid", "d1", "d2", "d3",
               "prov_uris_d1", "prov_uris_d2", "prov_uris_d3"]]


def _min_max_normalize(s: pd.Series) -> pd.Series:
    """(s - min) / (max - min) in [0,1]."""
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - lo) / (hi - lo)


def _build_idpt_long_df(raw: pd.DataFrame) -> pd.DataFrame:
    """Espande il df 107 → 428 righe (107 × 4 componenti) con valori normalizzati."""
    raw = raw.copy()
    raw["d1_norm"] = _min_max_normalize(raw["d1"])
    raw["d2_norm"] = _min_max_normalize(raw["d2"])
    raw["d3_norm"] = _min_max_normalize(raw["d3"])
    raw["idpt_agg"] = (raw["d1_norm"] + raw["d2_norm"] + raw["d3_norm"]) / 3

    long_rows = []
    for _, r in raw.iterrows():
        # Componenti elementari: valore_idpt = normalizzato, valore_grezzo = grezzo
        for comp_slug, comp_uri, val_norm, val_raw, prov_uris in (
            ("press-dem", COMPONENT_URIS["press-dem"], r["d1_norm"], r["d1"], r["prov_uris_d1"]),
            ("peso-eco",  COMPONENT_URIS["peso-eco"],  r["d2_norm"], r["d2"], r["prov_uris_d2"]),
            ("ered-st",   COMPONENT_URIS["ered-st"],   r["d3_norm"], r["d3"], r["prov_uris_d3"]),
        ):
            long_rows.append({
                "codice_istat":      r["istat"],
                "uri_agid":          r["uri_agid"],
                "componente_short":  comp_slug,
                "componente_uri":    comp_uri,
                "valore_idpt":       round(val_norm, 6),
                "valore_grezzo":     round(val_raw, 6),
                "prov_derived_uris": prov_uris,
            })
        # Aggregato finale: derivato dalle 3 componenti elementari della stessa provincia.
        # valore_grezzo = NaN → EmitQbObservations skippa la triple (l'aggregato è media
        # di valori già normalizzati, non ha un grezzo significativo).
        agg_prov_uris = [
            V.IDPT_NS + f"obs-idpt-{r['istat']}-press-dem-2026",
            V.IDPT_NS + f"obs-idpt-{r['istat']}-peso-eco-2026",
            V.IDPT_NS + f"obs-idpt-{r['istat']}-ered-st-2026",
        ]
        long_rows.append({
            "codice_istat":      r["istat"],
            "uri_agid":          r["uri_agid"],
            "componente_short":  "agg",
            "componente_uri":    COMPONENT_URIS["agg"],
            "valore_idpt":       round(r["idpt_agg"], 6),
            "valore_grezzo":     float("nan"),
            "prov_derived_uris": agg_prov_uris,
        })
    return pd.DataFrame(long_rows)


def main() -> int:
    print(f"=== Recipe Cubo 8 — IDPT computed ===")
    print(f"Output: {OUTPUT_TTL}")
    print()

    print("Carico i 5 cubi primari + vocabolari + AGID...")
    g = _load_grafo()
    print(f"✓ Grafo caricato: {len(g):,} triple")

    print()
    print("Calcolo D1, D2, D3 grezzi per 107 province...")
    raw = _compute_raw_components(g)
    print(f"✓ Componenti grezze calcolate: {len(raw)} province")
    print(f"  D1 range: [{raw['d1'].min():.3f}, {raw['d1'].max():.3f}]  media {raw['d1'].mean():.3f}")
    print(f"  D2 range: [{raw['d2'].min():.3f}, {raw['d2'].max():.3f}]  media {raw['d2'].mean():.3f}")
    print(f"  D3 range: [{raw['d3'].min():.3f}, {raw['d3'].max():.3f}]  media {raw['d3'].mean():.3f}")

    print()
    print("Normalizzazione min-max + aggregazione media aritmetica...")
    long_df = _build_idpt_long_df(raw)
    print(f"✓ Df long: {len(long_df)} righe (atteso 107 × 4 = 428)")

    # Sample province di interesse
    print()
    print("Sample IDPT aggregato per province di interesse:")
    samples = {"001": "Torino", "015": "Milano", "058": "Roma",
               "085": "Caltanissetta", "021": "Bolzano",
               "080": "Reggio Calabria", "092": "Cagliari", "111": "Sud Sardegna"}
    for istat, name in samples.items():
        row = long_df[(long_df["codice_istat"] == istat) & (long_df["componente_short"] == "agg")]
        if len(row):
            print(f"  {istat} {name:18s} IDPT = {row.iloc[0]['valore_idpt']:.3f}")

    print()
    print("Top 5 province per IDPT aggregato (più dipendenti):")
    top = long_df[long_df["componente_short"] == "agg"].nlargest(5, "valore_idpt")[
        ["codice_istat", "valore_idpt"]
    ]
    for _, r in top.iterrows():
        print(f"  {r['codice_istat']}: {r['valore_idpt']:.3f}")

    print()
    print("Bottom 5 province per IDPT aggregato (meno dipendenti):")
    bot = long_df[long_df["componente_short"] == "agg"].nsmallest(5, "valore_idpt")[
        ["codice_istat", "valore_idpt"]
    ]
    for _, r in bot.iterrows():
        print(f"  {r['codice_istat']}: {r['valore_idpt']:.3f}")

    # Emit (tutto E + prov:wasDerivedFrom per ogni obs)
    long_df["obs_status_uri"] = V.SDMX_CODE_OBS_STATUS_E

    print()
    print("Emit qb:Observation...")
    emit_ds = EmitQbObservations(
        dataset_uri=V.CUBE_IDPT_COMPUTED,
        dsd_uri=V.DSD_IDPT_COMPUTED,
        obs_uri_template=(
            V.IDPT_NS + "obs-idpt-{codice_istat}-{componente_short}-2026"
        ),
        dimensions={
            "uri_agid":       V.PROVINCIA,
            "componente_uri": V.COMPONENTE_IDPT,
        },
        constant_dimensions={
            V.ANNO_RIFERIMENTO: '"2026"^^xsd:gYear',
        },
        measures={
            "valore_idpt":   V.VALORE_IDPT,
            "valore_grezzo": V.VALORE_GREZZO_IDPT,
        },
        obs_status_column="obs_status_uri",
        prov_derived_from_column="prov_derived_uris",
        # Attributo a livello DataSet: documenta il metodo di normalizzazione
        # applicato per produrre i valoreIDPT a partire dai valoreGrezzoIDPT.
        dataset_attributes={
            V.METODO_NORMALIZZAZIONE: '"min-max"@it',
        },
        dataset_metadata={
            "title": "Indice di Dipendenza Previdenziale Territoriale (IDPT), 2026",
            "description": (
                "Indice composito calcolato per ognuna delle 107 province italiane "
                "al 1.1.2026, con 3 componenti elementari (D1 pressione demografica "
                "= pensioni vigenti / occupati; D2 peso economico = monte pensioni / "
                "monte redditi da lavoro; D3 eredità storica = intensità stimata di "
                "pensioni in regime retributivo) normalizzate min-max sui 107 valori "
                "e aggregate via media aritmetica. Per ognuna delle 321 obs componenti "
                "(D1/D2/D3) viene pubblicato anche il valore grezzo pre-normalizzazione "
                "via idpt:valoreGrezzoIDPT, per permettere ricomposizione con pesi "
                "alternativi. Tutte le 428 obs derivate da cubi primari (1, 5, 7, 2, "
                "9) e marcate obsStatus=E + prov:wasDerivedFrom esplicito verso "
                "le obs sorgenti del calcolo. Materializzato in grafo nominato "
                "separato graph:idpt-computed per distribuzione separabile via "
                "DCAT-AP_IT. Per Cagliari (092) e Sud Sardegna (111), D3 condivide "
                "il valore della sede INPS aggregata 'CAGLIARI E SUD SARDEGNA' "
                "(replica intero valore su entrambe le province, decisione "
                "metodologica Fase 6)."
            ),
            "issued": "2026-05-29",
            "source": "https://example.org/idpt/",
            "license": V.LICENSE_CC_BY_4_0,
            "rights": (
                "Indice derivato. Formula documentata in PROGETTO_CONTESTO.md "
                "sez. 3 e nel report finale del progetto."
            ),
        },
        output_path=OUTPUT_TTL,
    ).apply(Dataset(long_df))

    print()
    rec = emit_ds.history[-1]
    print(f"  EmitQbObservations:")
    for k, v in rec.metrics.items():
        if isinstance(v, (list, dict)) and len(str(v)) > 80:
            print(f"        {k}: {type(v).__name__} ({len(v)} items)")
        else:
            print(f"        {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
