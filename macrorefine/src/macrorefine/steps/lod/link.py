"""LinkProvinceToAGID_* + LinkSedeINPS — linking territoriale al vocabolario AGID.

Quattro step di linking, ciascuno per una "chiave" diversa che troviamo nei
CSV pubblici italiani:

- ``LinkProvinceToAGID_byNUTS`` — ISTAT (REF_AREA = codice NUTS-3 o fake-NUTS)
- ``LinkProvinceToAGID_bySigla`` — MEF (Sigla Provincia, 2 caratteri)
- ``LinkProvinceToAGID_byName`` — INPS vigenti residenza (nome provincia con
  anomalie tipografiche, risolte via normalizzazione + dizionario manuale
  + fuzzy fallback)
- ``LinkSedeINPS`` — INPS regime sede + serie storica (106 sedi INPS, asse
  territoriale distinto dalle province AGID). Riconcilia ciascuna sede a 1 o N
  province AGID via ``idpt:correspondsToProvinceAGID`` o ``idpt:aggregatesProvince``.

I primi 3 condividono lo stesso "output shape": 4 colonne aggiunte al df
(``uri_agid``, ``codice_istat``, ``sigla``, ``uri_regione_agid``), rinominabili
via ``output_columns``. ``LinkSedeINPS`` aggiunge invece 5 colonne specifiche
delle sedi (``uri_sede_inps``, ``slug_sede``, ``correspondsto_codice_istat``,
``aggregates_codici_istat``, ``uri_provincia_agid_principale``).

Tutti gli step registrano metriche di matched/unmatched in StepRecord.
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING, Any

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    import pandas as pd

    from macrorefine.dataset import Dataset


# =============================================================================
# Query SPARQL condivise
# =============================================================================

QUERY_PROVINCES_META = """
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>

SELECT DISTINCT ?prov ?prefLabel ?codiceIstat ?sigla ?regione
WHERE {
  ?prov a clv:Province ;
        skos:prefLabel ?prefLabel ;
        skos:notation  ?codiceIstat ;
        clv:acronym    ?sigla ;
        clv:situatedWithin ?regione .
  FILTER(LANG(?prefLabel) = "it")
}
"""

QUERY_NUTS_LINKS = """
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?prov ?nuts
WHERE {
  ?prov a clv:Province ;
        owl:sameAs+ ?nuts .
  FILTER(STRSTARTS(STR(?nuts), "http://nuts.geovocab.org/id/"))
}
"""

QUERY_FAKE_NUTS_LINKS = """
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

SELECT DISTINCT ?prov ?fakeNuts
WHERE {
  ?fakeNuts skos:exactMatch ?prov .
  ?prov a clv:Province .
  FILTER(STRSTARTS(STR(?fakeNuts), "http://nuts.geovocab.org/id/"))
}
"""

# Default output column names (LOD-canoniche per le 4 colonne aggiunte).
_DEFAULT_OUTPUT_COLUMNS: dict[str, str] = {
    "uri_agid": "uri_agid",
    "codice_istat": "codice_istat",
    "sigla": "sigla",
    "uri_regione_agid": "uri_regione_agid",
}


# =============================================================================
# Helper module-level
# =============================================================================

def _resolve_output_columns(
    user_override: dict[str, str] | None,
) -> dict[str, str]:
    """Merge utente + default, mantenendo i 4 chiavi attese."""
    if user_override is None:
        return dict(_DEFAULT_OUTPUT_COLUMNS)
    return {**_DEFAULT_OUTPUT_COLUMNS, **user_override}


def _load_province_metadata(
    provinces_ttl: Path,
    extra_ttl: Path | None = None,
) -> tuple[Any, dict[str, dict[str, Any]]]:
    """Carica il TTL AGID (+ eventuale sidecar) e ritorna (graph, meta_by_uri).

    Args:
        provinces_ttl: path a data/provinces.ttl.
        extra_ttl: path a un sidecar opzionale da caricare nello stesso grafo
            (es. nuts_aliases.ttl).

    Returns:
        Tupla (rdflib.Graph, dict {uri_prov: meta_dict}).
        meta_dict contiene: uri_agid, codice_istat, sigla, uri_regione_agid,
        _prefLabel (interno, non esposto di default).
    """
    from rdflib import Graph

    g = Graph()
    g.parse(str(provinces_ttl), format="turtle")
    if extra_ttl is not None and extra_ttl.exists():
        g.parse(str(extra_ttl), format="turtle")

    meta_by_uri: dict[str, dict[str, Any]] = {}
    for prov, label, istat, sigla, regione in g.query(QUERY_PROVINCES_META):
        meta_by_uri[str(prov)] = {
            "uri_agid": str(prov),
            "codice_istat": str(istat),
            "sigla": str(sigla),
            "uri_regione_agid": str(regione),
            "_prefLabel": str(label),
        }
    return g, meta_by_uri


def _populate_output_columns(
    df: "pd.DataFrame",
    key_series: "pd.Series",
    index: dict[str, dict[str, Any]],
    output_columns: dict[str, str],
) -> tuple["pd.Series", "pd.Series"]:
    """Aggiunge le 4 colonne di output al df, ritorna (matched_mask, key_series).

    Modifica df in-place (è una copia del caller).
    """
    matched_mask = key_series.isin(index)
    for key in ("uri_agid", "codice_istat", "sigla", "uri_regione_agid"):
        target_name = output_columns[key]
        df[target_name] = key_series.map(
            lambda v, k=key: index.get(v, {}).get(k) if index else None
        )
    return matched_mask, key_series


# =============================================================================
# Step 1 — LinkProvinceToAGID_byNUTS (esistente, refactorizzato)
# =============================================================================

class LinkProvinceToAGID_byNUTS(PipelineStep):
    """Arricchisce il df con metadata AGID usando il codice NUTS.

    Gestisce: NUTS-3 standard, NUTS storici multipli (via owl:sameAs+), alias
    NUTS-2/NUTS-3 per le PA (via sidecar nuts_aliases.ttl), fake-NUTS
    proprietari ISTAT IT108-IT111 (via skos:exactMatch nel sidecar).

    Vedi PROGETTO_CONTESTO.md sez. 4 + sez. 9 per il razionale.
    """

    def __init__(
        self,
        nuts_column: str,
        provinces_ttl: str | Path,
        nuts_aliases_ttl: str | Path | None = None,
        output_columns: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.nuts_column = nuts_column
        self.provinces_ttl = Path(provinces_ttl)
        self.nuts_aliases_ttl = (
            Path(nuts_aliases_ttl) if nuts_aliases_ttl is not None else None
        )
        self.output_columns = _resolve_output_columns(output_columns)
        self._index: dict[str, dict[str, Any]] | None = None

    def _build_index(self) -> dict[str, dict[str, Any]]:
        g, meta_by_uri = _load_province_metadata(
            self.provinces_ttl, extra_ttl=self.nuts_aliases_ttl
        )

        # Caso NUTS condivisi fra più province (scoperta Fase 4 cubo 5).
        # Esistono almeno 4 casi nel TTL AGID:
        #   - ITC43 (Bergamo 016 / Lecco 097) — Lecco nata 1992 dalla scissione
        #     di Como e Bergamo, ha ereditato ITC43 e gli è rimasto come "suo"
        #   - ITG27 (Cagliari 092 / Sud Sardegna 111) — Sud Sardegna nata 2016
        #   - ITG28 (Oristano 095 / Sud Sardegna 111) — idem
        #   - ITG2A (Nuoro 091 / Sud Sardegna 111) — idem
        #
        # Regola di risoluzione: **vince la provincia con MENO NUTS associati**.
        # Razionale: se una provincia ha solo quel NUTS (1) e un'altra ne ha
        # diversi (2+), allora quel NUTS è "il suo identificatore principale"
        # per la prima, mentre per la seconda è solo uno storico fra tanti.
        # I CSV ISTAT moderni usano i NUTS come identificatori principali della
        # provincia attuale, quindi questa regola allinea correttamente.
        # Tiebreaker (stesso numero di NUTS): codice ISTAT minore.
        # Step 1: raccolgo `prov_to_nuts_count` (quanti NUTS ha ciascuna prov)
        # e `nuts_candidates` (quali province dichiarano sameAs ogni NUTS).
        prov_to_nuts_count: dict[str, int] = {}
        nuts_to_provs: dict[str, set[str]] = {}
        for prov, nuts in g.query(QUERY_NUTS_LINKS):
            nuts_code = str(nuts).rsplit("/", 1)[-1]
            if not nuts_code or nuts_code == "-":
                continue
            prov_uri = str(prov)
            prov_to_nuts_count[prov_uri] = prov_to_nuts_count.get(prov_uri, 0) + 1
            nuts_to_provs.setdefault(nuts_code, set()).add(prov_uri)
        for prov, fake_nuts in g.query(QUERY_FAKE_NUTS_LINKS):
            nuts_code = str(fake_nuts).rsplit("/", 1)[-1]
            if not nuts_code or nuts_code == "-":
                continue
            prov_uri = str(prov)
            prov_to_nuts_count[prov_uri] = prov_to_nuts_count.get(prov_uri, 0) + 1
            nuts_to_provs.setdefault(nuts_code, set()).add(prov_uri)

        # Step 2: risoluzione. Per ogni NUTS:
        #   - 1 sola provincia candidata → assegno direttamente
        #   - più candidate → ordino per (count_nuts_della_prov asc, codice_istat asc)
        #     e prendo la prima.
        nuts_to_uri: dict[str, str] = {}
        for nuts_code, prov_uris in nuts_to_provs.items():
            if len(prov_uris) == 1:
                nuts_to_uri[nuts_code] = next(iter(prov_uris))
                continue
            scored: list[tuple[int, str, str]] = []
            for prov_uri in prov_uris:
                meta = meta_by_uri.get(prov_uri)
                if meta is None:
                    continue
                scored.append((
                    prov_to_nuts_count[prov_uri],
                    meta["codice_istat"],
                    prov_uri,
                ))
            scored.sort()  # asc su (count, codice_istat, uri)
            if scored:
                nuts_to_uri[nuts_code] = scored[0][2]

        index: dict[str, dict[str, Any]] = {}
        for nuts_code, prov_uri in nuts_to_uri.items():
            meta = meta_by_uri.get(prov_uri)
            if meta is None:
                continue
            index[nuts_code] = meta
        return index

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.nuts_column not in df.columns:
            raise KeyError(
                f"LinkProvinceToAGID_byNUTS: colonna NUTS '{self.nuts_column}' "
                f"non presente. Disponibili: {list(df.columns)}"
            )
        if self._index is None:
            self._index = self._build_index()

        key = df[self.nuts_column].astype(str)
        matched_mask, _ = _populate_output_columns(
            df, key, self._index, self.output_columns
        )
        unmatched = sorted(set(key[~matched_mask].tolist()))

        record = StepRecord(
            name=self.name,
            params={
                "nuts_column": self.nuts_column,
                "provinces_ttl": str(self.provinces_ttl),
                "nuts_aliases_ttl": (
                    str(self.nuts_aliases_ttl) if self.nuts_aliases_ttl else None
                ),
                "output_columns": dict(self.output_columns),
            },
            metrics={
                "input_rows": int(len(df)),
                "matched_rows": int(matched_mask.sum()),
                "unmatched_rows": int((~matched_mask).sum()),
                "unmatched_codes": unmatched,
                "index_size": len(self._index),
            },
        )
        return dataset.with_data(df, step_record=record)


# =============================================================================
# Step 2 — LinkProvinceToAGID_bySigla
# =============================================================================

class LinkProvinceToAGID_bySigla(PipelineStep):
    """Arricchisce il df con metadata AGID usando la sigla 2-char della provincia.

    Pattern di match esatto via `clv:acronym`. È la chiave nativa del CSV MEF
    (colonna `Sigla Provincia`). Niente fuzzy né alias: 107 sigle pure, 1:1
    con le province AGID attuali.

    Args:
        sigla_column: nome colonna con la sigla 2-char (es. "Sigla Provincia").
        provinces_ttl: path a data/provinces.ttl.
        output_columns: rinomina facoltativa delle 4 colonne di output.
        case_insensitive: se True (default), il match è case-insensitive — utile
            per CSV MEF che ha sigle uppercase. Le sigle AGID sono già uppercase,
            quindi la normalizzazione è solo lato input.

    Edge case noti del CSV MEF (vedi PROGETTO_CONTESTO.md sez. 9):
    - 92 comuni di Napoli hanno `Sigla Provincia` letta come NaN da pandas
      perché "NA" è interpretato come missing value. Risolvere in lettura CSV
      con `keep_default_na=False` o `na_values=[""]`.
    - 1 riga sentinella `Codice Istat=0`, `Sigla=0`, `Regione=Mancante/errata`
      da escludere prima dell'aggregazione.
    """

    def __init__(
        self,
        sigla_column: str,
        provinces_ttl: str | Path,
        output_columns: dict[str, str] | None = None,
        case_insensitive: bool = True,
    ) -> None:
        super().__init__()
        self.sigla_column = sigla_column
        self.provinces_ttl = Path(provinces_ttl)
        self.output_columns = _resolve_output_columns(output_columns)
        self.case_insensitive = case_insensitive
        self._index: dict[str, dict[str, Any]] | None = None

    def _build_index(self) -> dict[str, dict[str, Any]]:
        _, meta_by_uri = _load_province_metadata(self.provinces_ttl)
        index: dict[str, dict[str, Any]] = {}
        for meta in meta_by_uri.values():
            key = meta["sigla"]
            if self.case_insensitive:
                key = key.upper()
            index[key] = meta
        return index

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.sigla_column not in df.columns:
            raise KeyError(
                f"LinkProvinceToAGID_bySigla: colonna sigla '{self.sigla_column}' "
                f"non presente. Disponibili: {list(df.columns)}"
            )
        if self._index is None:
            self._index = self._build_index()

        key = df[self.sigla_column].astype(str)
        if self.case_insensitive:
            key = key.str.upper()
        # Lo .str.upper() trasforma NaN → "NAN" che è uppercase di "nan".
        # Per non matchare "NAN" a niente, le 107 sigle AGID sono comunque 2-char
        # alfabetiche; "NAN" non esiste tra loro. Robusto by design.

        matched_mask, _ = _populate_output_columns(
            df, key, self._index, self.output_columns
        )
        unmatched = sorted(set(key[~matched_mask].tolist()))

        record = StepRecord(
            name=self.name,
            params={
                "sigla_column": self.sigla_column,
                "provinces_ttl": str(self.provinces_ttl),
                "output_columns": dict(self.output_columns),
                "case_insensitive": self.case_insensitive,
            },
            metrics={
                "input_rows": int(len(df)),
                "matched_rows": int(matched_mask.sum()),
                "unmatched_rows": int((~matched_mask).sum()),
                "unmatched_codes": unmatched,
                "index_size": len(self._index),
            },
        )
        return dataset.with_data(df, step_record=record)


# =============================================================================
# Step 3 — LinkProvinceToAGID_byName
# =============================================================================

# Anomalie strutturali identificate puntualmente in Fase 1 blocco 2 dal confronto
# CSV INPS (vigenti residenza 110 entry + regime sede 106 entry) vs nomi AGID.
# Chiavi: nome normalizzato (lower, NFD, fix spazio-trattino, strip). Valori:
# codice ISTAT della provincia AGID di destinazione.
#
# NB: le ex-province sarde (Carbonia-Iglesias, Medio Campidano, Olbia-Tempio,
# Ogliastra) NON vengono dirottate qui — vanno aggregate da
# AggregateSardiniaProvinces PRIMA che parta byName, in modo che il df arrivi
# qui con solo i 5 nomi sardi canonici (Cagliari, Nuoro, Oristano, Sassari,
# Sud Sardegna).
#
# NB2: "CAGLIARI E SUD SARDEGNA" (sede INPS aggregata, presente in regime sede
# e serie storica) NON è una provincia singola e quindi NON viene risolta qui —
# verrà gestita da LinkSedeINPS nel blocco 3.
SETTLED_ALIASES: dict[str, str] = {
    # 9 anomalie strutturali nominali (CSV vigenti residenza)
    "aosta":                                "007",   # → Valle d'Aosta/Vallée d'Aoste
    "barletta-andria-trani":                "110",   # spazio già fixato dalla normalize
    "forli'-cesena":                        "040",   # → Forlì-Cesena (apostrofo INPS)
    "forli-cesena":                         "040",   # variante senza apostrofo
    "massa-carrara":                        "045",   # già fixato dalla normalize
    "provincia autonoma di bolzano/bozen":  "021",
    "bolzano/bozen":                        "021",
    "bolzano":                              "021",
    "provincia autonoma di trento":         "022",
    "trento":                               "022",
    "reggio calabria":                      "080",   # → Reggio di Calabria
    "reggio emilia":                        "035",   # → Reggio nell'Emilia
    "verbano-cusio-ossola":                 "103",
    # 2 anomalie UPPERCASE-only del CSV regime sede + serie storica
    "verbania":                             "103",   # nome sintetico INPS per VB
    "forli":                                "040",   # senza accento (UPPERCASE del CSV)
    # Anomalia scoperta in Fase 1 blocco 3 sul CSV regime sede:
    # AGID label "Pesaro e Urbino" (con " e "), INPS sede "PESARO -URBINO"
    # (con trattino). Normalize li rende "pesaro e urbino" vs "pesaro-urbino",
    # mismatch a livello di stringa. Risolto via alias esplicito.
    "pesaro-urbino":                        "041",
}


def _normalize_province_name(name: str) -> str:
    """Normalizza il nome provincia per il match.

    Pipeline:
    1. cast a str + strip whitespace esterno
    2. lowercase
    3. NFKD + drop diacritici (rimuove accenti)
    4. fix spazi attorno ai trattini: " -" → "-", "- " → "-"
    5. collassa whitespace multipli in singolo spazio
    """
    s = str(name).strip().lower()
    # NFKD: scompone "à" in "a" + combining accent, poi droppa il combining
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Fix spazi attorno ai trattini (INPS scrive "PESARO -URBINO")
    s = re.sub(r"\s*-\s*", "-", s)
    # Collassa whitespace multipli
    s = re.sub(r"\s+", " ", s)
    return s.strip()


class LinkProvinceToAGID_byName(PipelineStep):
    """Arricchisce il df con metadata AGID usando il nome della provincia.

    Pipeline interna (in ordine):
    1. **Normalizzazione**: lower, NFKD diacritici drop, fix spazi-trattini.
    2. **Match diretto**: lookup sul nome AGID normalizzato.
    3. **Dizionario manuale** (SETTLED_ALIASES + manual_aliases utente): per
       anomalie strutturali (PA, Reggio C/E, Aosta = Valle d'Aosta, ecc.).
    4. **Fuzzy match** via rapidfuzz come fallback (soglia min_fuzzy_score).

    Args:
        name_column: nome della colonna con il nome provincia.
        provinces_ttl: path a data/provinces.ttl.
        manual_aliases: dizionario extra {nome_normalizzato: codice_istat}
            che si merge con SETTLED_ALIASES (override permesso).
        min_fuzzy_score: soglia di match fuzzy (0-100, default 90).
        raise_on_unmatched: se True, solleva ValueError invece di lasciare NaN.
        output_columns: rinomina facoltativa delle 4 colonne di output.

    Metriche StepRecord: input_rows, matched_rows (totale), matched_via_direct,
    matched_via_alias, matched_via_fuzzy, unmatched_rows, unmatched_names.

    Esempio:
        step = LinkProvinceToAGID_byName(
            name_column="provincia",
            provinces_ttl="data/provinces.ttl",
        )
        clean = step.apply(dataset)
    """

    def __init__(
        self,
        name_column: str,
        provinces_ttl: str | Path,
        manual_aliases: dict[str, str] | None = None,
        min_fuzzy_score: int = 90,
        raise_on_unmatched: bool = False,
        output_columns: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        if not 0 <= min_fuzzy_score <= 100:
            raise ValueError(
                f"min_fuzzy_score deve essere 0-100 (ricevuto {min_fuzzy_score})"
            )
        self.name_column = name_column
        self.provinces_ttl = Path(provinces_ttl)
        self.aliases: dict[str, str] = {**SETTLED_ALIASES}
        if manual_aliases:
            self.aliases.update(
                {_normalize_province_name(k): v for k, v in manual_aliases.items()}
            )
        self.min_fuzzy_score = min_fuzzy_score
        self.raise_on_unmatched = raise_on_unmatched
        self.output_columns = _resolve_output_columns(output_columns)

        # Caches lazy
        self._name_index: dict[str, dict[str, Any]] | None = None     # nome normalizzato → meta
        self._istat_index: dict[str, dict[str, Any]] | None = None    # codice ISTAT → meta
        self._name_keys: list[str] | None = None                       # per rapidfuzz

    def _build_indices(self) -> None:
        """Costruisce due index complementari: per nome canonico e per codice ISTAT."""
        _, meta_by_uri = _load_province_metadata(self.provinces_ttl)
        self._name_index = {}
        self._istat_index = {}
        for meta in meta_by_uri.values():
            norm_label = _normalize_province_name(meta["_prefLabel"])
            self._name_index[norm_label] = meta
            self._istat_index[meta["codice_istat"]] = meta
        self._name_keys = list(self._name_index.keys())

    def _match_one(self, raw_name: str) -> tuple[dict[str, Any] | None, str]:
        """Ritorna (meta_dict | None, source) dove source ∈ {'direct', 'alias', 'fuzzy', 'unmatched'}."""
        norm = _normalize_province_name(raw_name)
        # 1. Match diretto
        if self._name_index is not None and norm in self._name_index:
            return self._name_index[norm], "direct"
        # 2. Match via dizionario manuale (codice ISTAT → meta)
        if norm in self.aliases:
            code = self.aliases[norm]
            if self._istat_index is not None and code in self._istat_index:
                return self._istat_index[code], "alias"
        # 3. Fuzzy match
        if self._name_keys:
            from rapidfuzz import process, fuzz
            match = process.extractOne(
                norm, self._name_keys, scorer=fuzz.ratio,
                score_cutoff=self.min_fuzzy_score,
            )
            if match is not None:
                matched_name = match[0]
                return self._name_index[matched_name], "fuzzy"
        return None, "unmatched"

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()
        if self.name_column not in df.columns:
            raise KeyError(
                f"LinkProvinceToAGID_byName: colonna nome '{self.name_column}' "
                f"non presente. Disponibili: {list(df.columns)}"
            )
        if self._name_index is None:
            self._build_indices()

        # Aggiungo colonne placeholder + popolo riga per riga (mantiene metriche per-source)
        for key in ("uri_agid", "codice_istat", "sigla", "uri_regione_agid"):
            df[self.output_columns[key]] = None

        counts = {"direct": 0, "alias": 0, "fuzzy": 0, "unmatched": 0}
        unmatched_names: list[str] = []
        for idx, raw in df[self.name_column].items():
            meta, source = self._match_one(raw)
            counts[source] += 1
            if meta is not None:
                for key in ("uri_agid", "codice_istat", "sigla", "uri_regione_agid"):
                    df.at[idx, self.output_columns[key]] = meta[key]
            else:
                unmatched_names.append(str(raw))

        if self.raise_on_unmatched and counts["unmatched"] > 0:
            raise ValueError(
                f"LinkProvinceToAGID_byName: {counts['unmatched']} nomi non "
                f"risolvibili. Esempi: {sorted(set(unmatched_names))[:10]}"
            )

        record = StepRecord(
            name=self.name,
            params={
                "name_column": self.name_column,
                "provinces_ttl": str(self.provinces_ttl),
                "min_fuzzy_score": self.min_fuzzy_score,
                "raise_on_unmatched": self.raise_on_unmatched,
                "manual_aliases_count": len(self.aliases),
                "output_columns": dict(self.output_columns),
            },
            metrics={
                "input_rows": int(len(df)),
                "matched_rows": counts["direct"] + counts["alias"] + counts["fuzzy"],
                "matched_via_direct": counts["direct"],
                "matched_via_alias": counts["alias"],
                "matched_via_fuzzy": counts["fuzzy"],
                "unmatched_rows": counts["unmatched"],
                "unmatched_names": sorted(set(unmatched_names)),
                "index_size": len(self._name_index) if self._name_index else 0,
            },
        )
        return dataset.with_data(df, step_record=record)


# =============================================================================
# Step 4 — LinkSedeINPS
# =============================================================================

# AGID provinces base URI per la costruzione delle URI nel sidecar
_AGIDP_BASE = (
    "https://w3id.org/italia/controlled-vocabulary/"
    "territorial-classifications/provinces/"
)
# Default namespace per le sedi INPS (placeholder fino al deploy GitHub Pages,
# decisione δ+β del Blocco B di check-point ontologico, sez. 4)
_IDPT_BASE = "https://example.org/idpt/"

# Casi speciali del CSV regime sede / serie storica.
# La sede aggregata `CAGLIARI E SUD SARDEGNA` mappa 1:N su 2 province AGID.
# Tutte le altre 105 sedi mappano 1:1 e si risolvono tramite la stessa
# logica di `LinkProvinceToAGID_byName` (normalize + SETTLED_ALIASES + fuzzy).
SEDE_INPS_1_TO_N: dict[str, list[str]] = {
    # nome normalizzato → lista codici ISTAT delle province AGID aggregate
    "cagliari e sud sardegna": ["092", "111"],
}


def _slugify_inps(name: str) -> str:
    """Genera uno slug URL-safe dal nome di una sede INPS.

    Pipeline: lower → drop diacritici → unifica separatori (spazi, trattini,
    slash, apostrofi) come '-' → rimuovi caratteri non-alfanumerici → strip
    dei trattini esterni.

    Esempi:
        "TORINO" → "torino"
        "CAGLIARI E SUD SARDEGNA" → "cagliari-e-sud-sardegna"
        "PESARO -URBINO" → "pesaro-urbino"
        "BARLETTA -ANDRIA-TRANI" → "barletta-andria-trani"
        "Provincia Autonoma di Bolzano/Bozen" → "provincia-autonoma-di-bolzano-bozen"
    """
    s = unicodedata.normalize("NFKD", name.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[\s\-/'’]+", "-", s)
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def emit_inps_to_agid_sidecar(
    output_path: Path,
    meta_by_uri: dict[str, dict[str, Any]],
    sede_records: list[dict[str, Any]],
    provinces_inps_labels: dict[str, str] | None = None,
) -> None:
    """Scrive ``output/mappings/inps_to_agid.ttl`` con il pattern documentato in sez. 10.13.

    Args:
        output_path: dove salvare il TTL.
        meta_by_uri: mapping URI provincia AGID → metadata (uri_agid,
            codice_istat, sigla, prefLabel).
        sede_records: lista di dict con keys ``slug_sede``, ``pref_label_inps``,
            ``correspondsto_codice_istat`` (str | None), ``aggregates_codici_istat``
            (list[str] | None), ``notation``. Una entry per ognuna delle 106 sedi.
        provinces_inps_labels: opzionale, mapping codice_istat → nome INPS
            originale (forma vigenti residenza) per emettere ``skos:altLabel
            "..."@it-x-inps``. Se None, le altLabel non vengono emesse.
    """
    from rdflib import Graph, Literal, Namespace, URIRef
    from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

    idpt = Namespace(_IDPT_BASE)
    agidp = Namespace(_AGIDP_BASE)

    g = Graph()
    g.bind("idpt", idpt)
    g.bind("agidp", agidp)
    g.bind("skos", SKOS)
    g.bind("rdfs", RDFS)
    g.bind("dcterms", DCTERMS)
    g.bind("owl", OWL)

    # Header del file (prov:Entity → metadata di provenance del sidecar)
    sidecar_uri = idpt["inps-to-agid-graph"]
    g.add((sidecar_uri, RDF.type, DCTERMS.Standard))
    g.add((sidecar_uri, DCTERMS.title,
           Literal("Sidecar linking INPS ↔ AGID province + sedi", lang="it")))
    g.add((sidecar_uri, DCTERMS.description, Literal(
        "Riconciliazione fra nomi INPS (CSV vigenti residenza + regime sede + serie "
        "storica) e URI AGID delle province italiane. Contiene: (a) skos:altLabel "
        "@it-x-inps con le forme nominali del CSV INPS vigenti residenza, (b) "
        "106 istanze idpt:SedeINPS con prefLabel + notation + correspondsTo o "
        "aggregatesProvince verso le province AGID.",
        lang="it"
    )))
    g.add((sidecar_uri, DCTERMS.source,
           URIRef("https://www.inps.it/osservatorio")))
    g.add((sidecar_uri, DCTERMS.license,
           URIRef("https://creativecommons.org/licenses/by/4.0/")))

    # ---- Pattern 1: skos:altLabel "..."@it-x-inps sulle 107 province AGID ----
    # Solo se l'utente passa il mapping provinces_inps_labels.
    if provinces_inps_labels:
        for codice_istat, inps_label in provinces_inps_labels.items():
            prov_uri = URIRef(_AGIDP_BASE + codice_istat)
            g.add((prov_uri, SKOS.altLabel, Literal(inps_label, lang="it-x-inps")))

    # ---- Pattern 2: 106 istanze idpt:SedeINPS ----
    for rec in sede_records:
        sede_uri = URIRef(_IDPT_BASE + "sede-inps-" + rec["slug_sede"])
        g.add((sede_uri, RDF.type, idpt.SedeINPS))
        g.add((sede_uri, SKOS.prefLabel, Literal(rec["pref_label_inps"], lang="it")))
        g.add((sede_uri, SKOS.notation, Literal(rec["notation"])))

        if rec.get("correspondsto_codice_istat"):
            prov_uri = URIRef(_AGIDP_BASE + rec["correspondsto_codice_istat"])
            g.add((sede_uri, idpt.correspondsToProvinceAGID, prov_uri))
        if rec.get("aggregates_codici_istat"):
            for code in rec["aggregates_codici_istat"]:
                prov_uri = URIRef(_AGIDP_BASE + code)
                g.add((sede_uri, idpt.aggregatesProvince, prov_uri))

        if rec.get("rdfs_comment"):
            g.add((sede_uri, RDFS.comment, Literal(rec["rdfs_comment"], lang="it")))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output_path), format="turtle")


class LinkSedeINPS(PipelineStep):
    """Risolve i nomi sede INPS in URI ``idpt:SedeINPS`` + URI provincia AGID.

    I CSV INPS "regime di liquidazione" e "serie storica" hanno asse territoriale
    "sede INPS" (106 sedi), non "provincia di residenza". Le sedi non sono nel
    vocabolario AGID — sono entità del nostro grafo, modellate come
    ``idpt:SedeINPS`` (sottoclasse di ``clv:Feature``). Vedi PROGETTO_CONTESTO.md
    sez. 4 + sez. 10.9 per il razionale.

    La maggioranza delle sedi è 1:1 con una provincia AGID (es. "TORINO" →
    ``agidp:001``). Una sola sede è 1:N: ``CAGLIARI E SUD SARDEGNA`` aggrega
    ``agidp:092`` (Cagliari) + ``agidp:111`` (Sud Sardegna).

    Args:
        sede_column: nome colonna che contiene il nome della sede INPS.
        provinces_ttl: path a ``data/provinces.ttl``.
        emit_sidecar_to: path opzionale dove emettere ``inps_to_agid.ttl``
            al primo apply(). Anticipa il sidecar previsto in Fase 2.
        emit_inps_residence_labels: se True, e se ``emit_sidecar_to`` è fornito,
            emette anche le 107 ``skos:altLabel "..."@it-x-inps`` con la forma
            del CSV vigenti residenza (mapping hardcoded ``INPS_RESIDENCE_LABELS``).
        output_columns: rinomina facoltativa delle 5 colonne di output:
            ``uri_sede_inps``, ``slug_sede``, ``correspondsto_codice_istat``,
            ``aggregates_codici_istat`` (lista come str CSV), ``uri_provincia_agid_principale``.
    """

    # Mapping hardcoded per le altLabel `@it-x-inps` (forma CSV vigenti residenza).
    # 107 entry corrispondenti alle 107 province AGID, le 13 anomalie più i nomi
    # standard sono già coperti. Le ex-province sarde non sono qui perché vanno
    # aggregate prima e non hanno corrispondenza diretta 1:1 in AGID.
    INPS_RESIDENCE_LABELS: dict[str, str] = {
        # Anomalie strutturali / tipografiche
        "007": "Aosta",                                # AO → Valle d'Aosta
        "021": "Provincia Autonoma di Bolzano/Bozen",  # BZ
        "022": "Provincia Autonoma di Trento",         # TN
        "035": "Reggio Emilia",                         # RE → Reggio nell'Emilia
        "040": "Forli' -Cesena",                        # FC → Forlì-Cesena
        "045": "Massa -Carrara",                        # MS → Massa-Carrara
        "080": "Reggio Calabria",                       # RC → Reggio di Calabria
        "103": "Verbano -Cusio-Ossola",                 # VB
        "110": "Barletta -Andria-Trani",                # BT
        # Le 94 province "regolari" hanno nome INPS = nome AGID e non richiedono
        # altLabel ridondante (il loro skos:prefLabel@it è già la forma INPS).
        # Le 5 sarde attuali pre-aggregazione hanno nomi base coincidenti con AGID:
        # Cagliari, Nuoro, Oristano, Sassari (Sud Sardegna era nata dopo
        # l'ultima esportazione AGID).
    }

    def __init__(
        self,
        sede_column: str,
        provinces_ttl: str | Path,
        emit_sidecar_to: str | Path | None = None,
        emit_inps_residence_labels: bool = True,
        output_columns: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.sede_column = sede_column
        self.provinces_ttl = Path(provinces_ttl)
        self.emit_sidecar_to = (
            Path(emit_sidecar_to) if emit_sidecar_to is not None else None
        )
        self.emit_inps_residence_labels = emit_inps_residence_labels
        default_out = {
            "uri_sede_inps": "uri_sede_inps",
            "slug_sede": "slug_sede",
            "correspondsto_codice_istat": "correspondsto_codice_istat",
            "aggregates_codici_istat": "aggregates_codici_istat",
            "uri_provincia_agid_principale": "uri_provincia_agid_principale",
        }
        if output_columns is None:
            self.output_columns = default_out
        else:
            self.output_columns = {**default_out, **output_columns}

        # Caches
        self._inner_byname: LinkProvinceToAGID_byName | None = None
        self._sidecar_emitted: bool = False

    def _resolve_sede(
        self, raw_sede: str
    ) -> tuple[str | None, list[str] | None, str | None]:
        """Ritorna (slug_sede, lista_codici_istat, source).

        source ∈ {"aggregates_1_to_N", "direct_1_to_1", "alias_1_to_1",
                  "fuzzy_1_to_1", "unmatched"}.
        """
        norm = _normalize_province_name(raw_sede)
        slug = _slugify_inps(raw_sede)

        # Caso 1:N (sede aggregata)
        if norm in SEDE_INPS_1_TO_N:
            return slug, list(SEDE_INPS_1_TO_N[norm]), "aggregates_1_to_N"

        # Caso 1:1: delego a LinkProvinceToAGID_byName per la risoluzione
        if self._inner_byname is None:
            self._inner_byname = LinkProvinceToAGID_byName(
                name_column="_tmp", provinces_ttl=self.provinces_ttl
            )
            self._inner_byname._build_indices()
        meta, source = self._inner_byname._match_one(raw_sede)
        if meta is None:
            return slug, None, "unmatched"
        return slug, [meta["codice_istat"]], f"{source}_1_to_1"

    def apply(self, dataset: "Dataset") -> "Dataset":
        df = dataset.to_pandas()

        if self.sede_column not in df.columns:
            raise KeyError(
                f"LinkSedeINPS: colonna sede '{self.sede_column}' non presente. "
                f"Disponibili: {list(df.columns)}"
            )

        # Costruisco i 5 valori per ogni riga
        counts = {"aggregates_1_to_N": 0, "unmatched": 0}
        counts.update({f"{s}_1_to_1": 0 for s in ("direct", "alias", "fuzzy")})
        out_vals: dict[str, list] = {
            k: [] for k in self.output_columns.values()
        }
        unmatched_sedi: list[str] = []
        sede_records_for_sidecar: list[dict[str, Any]] = []
        seen_slugs: set[str] = set()

        for raw_sede in df[self.sede_column]:
            slug, codici, source = self._resolve_sede(str(raw_sede))
            counts[source] = counts.get(source, 0) + 1

            if codici is None:
                # Unmatched
                for k in self.output_columns.values():
                    out_vals[k].append(None)
                unmatched_sedi.append(str(raw_sede))
                continue

            uri_sede = _IDPT_BASE + "sede-inps-" + slug
            if source == "aggregates_1_to_N":
                out_vals[self.output_columns["uri_sede_inps"]].append(uri_sede)
                out_vals[self.output_columns["slug_sede"]].append(slug)
                out_vals[self.output_columns["correspondsto_codice_istat"]].append(None)
                out_vals[self.output_columns["aggregates_codici_istat"]].append(",".join(codici))
                # principale = prima provincia (per le query "1 sede → 1 provincia rappresentativa")
                out_vals[self.output_columns["uri_provincia_agid_principale"]].append(
                    _AGIDP_BASE + codici[0]
                )
            else:
                # 1:1
                out_vals[self.output_columns["uri_sede_inps"]].append(uri_sede)
                out_vals[self.output_columns["slug_sede"]].append(slug)
                out_vals[self.output_columns["correspondsto_codice_istat"]].append(codici[0])
                out_vals[self.output_columns["aggregates_codici_istat"]].append(None)
                out_vals[self.output_columns["uri_provincia_agid_principale"]].append(
                    _AGIDP_BASE + codici[0]
                )

            # Registro la sede per il sidecar (una sola volta per slug)
            if slug not in seen_slugs:
                seen_slugs.add(slug)
                sigla_guess = _slug_to_inps_notation(slug, codici)
                sede_rec: dict[str, Any] = {
                    "slug_sede": slug,
                    "pref_label_inps": str(raw_sede),
                    "notation": sigla_guess,
                }
                if source == "aggregates_1_to_N":
                    sede_rec["aggregates_codici_istat"] = codici
                    sede_rec["rdfs_comment"] = (
                        "Sede INPS aggregata di Cagliari e Sud Sardegna. "
                        "Mappa 1-a-N verso 2 province AGID."
                    )
                else:
                    sede_rec["correspondsto_codice_istat"] = codici[0]
                sede_records_for_sidecar.append(sede_rec)

        # Popolo il df con le colonne calcolate
        for col_name, values in out_vals.items():
            df[col_name] = values

        # Emissione opzionale del sidecar (al primo apply, una sola volta)
        if self.emit_sidecar_to is not None and not self._sidecar_emitted:
            # Carico il meta_by_uri per gli URI canonici (serve solo se emettiamo altLabel)
            _, meta_by_uri = _load_province_metadata(self.provinces_ttl)
            provinces_inps_labels = (
                self.INPS_RESIDENCE_LABELS if self.emit_inps_residence_labels else None
            )
            emit_inps_to_agid_sidecar(
                output_path=self.emit_sidecar_to,
                meta_by_uri=meta_by_uri,
                sede_records=sede_records_for_sidecar,
                provinces_inps_labels=provinces_inps_labels,
            )
            self._sidecar_emitted = True

        matched_total = len(df) - counts["unmatched"]
        record = StepRecord(
            name=self.name,
            params={
                "sede_column": self.sede_column,
                "provinces_ttl": str(self.provinces_ttl),
                "emit_sidecar_to": (
                    str(self.emit_sidecar_to) if self.emit_sidecar_to else None
                ),
                "emit_inps_residence_labels": self.emit_inps_residence_labels,
                "output_columns": dict(self.output_columns),
            },
            metrics={
                "input_rows": int(len(df)),
                "matched_rows": int(matched_total),
                "unmatched_rows": counts["unmatched"],
                "unmatched_sedi": sorted(set(unmatched_sedi)),
                "matched_1_to_1_direct": counts.get("direct_1_to_1", 0),
                "matched_1_to_1_alias": counts.get("alias_1_to_1", 0),
                "matched_1_to_1_fuzzy": counts.get("fuzzy_1_to_1", 0),
                "matched_1_to_N": counts.get("aggregates_1_to_N", 0),
                "distinct_sedi": len(seen_slugs),
                "sidecar_emitted": self._sidecar_emitted,
            },
        )
        return dataset.with_data(df, step_record=record)


def _slug_to_inps_notation(slug: str, codici_istat: list[str]) -> str:
    """Genera la notation INPS della sede. Pattern:

    - 1:1: ``INPS-{sigla}``. La sigla viene dedotta dal codice ISTAT via
      la query del TTL AGID — qui usiamo una stringa segnaposto basata sullo
      slug delle prime 2 lettere, perché lo step non ha accesso al TTL al
      momento di costruire la notation (la metadata province la conosciamo
      solo via _load_province_metadata che viene chiamato altrove).
      In pratica useremo la sigla AGID se passata, altrimenti slug.upper()[:6].
    - 1:N (Cagliari e Sud Sardegna): ``INPS-CA-SU``.

    Per ora ritorno il pattern ``INPS-{slug}`` se 1:1, ``INPS-CA-SU`` se l'unico
    caso aggregato. La forma definitiva è canonizzata nel sidecar TTL.
    """
    if len(codici_istat) > 1:
        # Solo Cagliari + Sud Sardegna nel nostro caso (la modellazione formale
        # prevede esattamente questa 1 sede 1:N).
        return "INPS-CA-SU"
    return "INPS-" + slug.upper()[:8]
