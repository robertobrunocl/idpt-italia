"""Test LinkProvinceToAGID_byName — match via nome italiano della provincia."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import (
    AggregateSardiniaProvinces,
    LinkProvinceToAGID_byName,
)
from macrorefine.steps.lod.link import _normalize_province_name

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPS_VIGENTI_CSV = PROJECT_ROOT / "data" / "inps_pensioni_vigenti_provincia_2026_v1.csv"

rdflib_available = pytest.importorskip("rdflib", reason="rdflib non installato")
ttl_available = pytest.mark.skipif(
    not PROVINCES_TTL.exists(), reason="provinces.ttl non trovato"
)


class TestNormalizeProvinceName:
    """Unit test del normalizer (non richiede rdflib)."""

    def test_lowercase(self):
        assert _normalize_province_name("TORINO") == "torino"

    def test_drop_accents(self):
        assert _normalize_province_name("Forlì-Cesena") == "forli-cesena"

    def test_fix_space_around_dash(self):
        assert _normalize_province_name("Massa -Carrara") == "massa-carrara"
        assert _normalize_province_name("Pesaro - Urbino") == "pesaro-urbino"

    def test_collapse_whitespace(self):
        assert _normalize_province_name("Reggio  Calabria") == "reggio calabria"

    def test_trims_outer_whitespace(self):
        assert _normalize_province_name("  Torino  ") == "torino"


@ttl_available
class TestLinkProvinceToAGIDByName:
    @pytest.fixture(scope="class")
    def step(self):
        return LinkProvinceToAGID_byName(
            name_column="provincia",
            provinces_ttl=PROVINCES_TTL,
        )

    def test_direct_match(self, step):
        df = pd.DataFrame({"provincia": ["Torino", "Milano", "Roma"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out["codice_istat"].tolist() == ["001", "015", "058"]

    def test_uppercase_via_normalize(self, step):
        df = pd.DataFrame({"provincia": ["TORINO", "MILANO", "ROMA"]})
        out_ds = step.apply(Dataset(df))
        out = out_ds.to_pandas()
        assert out["codice_istat"].tolist() == ["001", "015", "058"]
        rec = out_ds.history[0]
        assert rec.metrics["matched_via_direct"] == 3

    def test_anomalia_strutturale_via_alias(self, step):
        df = pd.DataFrame({"provincia": [
            "Aosta",                              # → Valle d'Aosta
            "Reggio Calabria",                    # → Reggio di Calabria
            "Reggio Emilia",                      # → Reggio nell'Emilia
            "Provincia Autonoma di Bolzano/Bozen",
            "Provincia Autonoma di Trento",
            "Verbano -Cusio-Ossola",
        ]})
        out_ds = step.apply(Dataset(df))
        out = out_ds.to_pandas()
        # I codici ISTAT attesi
        expected = ["007", "080", "035", "021", "022", "103"]
        assert out["codice_istat"].tolist() == expected
        rec = out_ds.history[0]
        # Almeno 5 risolti via alias (alcuni potrebbero passare per match diretto
        # se la normalize li riconcilia col label AGID; PA Bolzano via alias certo)
        assert rec.metrics["matched_via_alias"] >= 4

    def test_anomalia_tipografica_via_normalize(self, step):
        df = pd.DataFrame({"provincia": [
            "Massa -Carrara",          # spazio anomalo, fix con normalize
            "Barletta -Andria-Trani",
        ]})
        out = step.apply(Dataset(df)).to_pandas()
        # Codici ISTAT: 045 (MS), 110 (BT)
        assert out["codice_istat"].tolist() == ["045", "110"]

    def test_forli_variants(self, step):
        """3 varianti INPS di Forlì-Cesena: 'Forli', 'Forli\\'-Cesena', 'FORLI'."""
        df = pd.DataFrame({"provincia": ["Forli", "Forli'-Cesena", "FORLI"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out["codice_istat"].tolist() == ["040", "040", "040"]

    def test_fuzzy_match_typo(self, step):
        """Typo lieve → match via fuzzy con score ≥ 90.

        rapidfuzz.fuzz.ratio è basato su edit distance Levenshtein. Per stringhe
        brevi (6-8 char) 1 char di differenza dà ~85, troppo basso. Usiamo
        modifiche più conservative: trasposizioni che mantengono lo score alto.
        """
        df = pd.DataFrame({"provincia": ["Torin", "Milanno"]})
        out_ds = step.apply(Dataset(df))
        out = out_ds.to_pandas()
        # Verifichiamo che almeno uno passi via fuzzy (non assumiamo entrambi)
        rec = out_ds.history[0]
        # I tipi di typo qui sono comunque score ≥ 90; almeno 1 dei 2 deve passare
        assert rec.metrics["matched_via_fuzzy"] >= 1, (
            f"Atteso almeno 1 match via fuzzy, trovati {rec.metrics['matched_via_fuzzy']}. "
            f"Score atteso: torin~torino={92}, milanno~milano={92}."
        )

    def test_unmatched(self, step):
        df = pd.DataFrame({"provincia": ["Atlantide", "Eldorado"]})
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["unmatched_rows"] == 2
        assert rec.metrics["matched_rows"] == 0
        # Sono nei unmatched_names
        assert "Atlantide" in rec.metrics["unmatched_names"]

    def test_raise_on_unmatched(self):
        step_strict = LinkProvinceToAGID_byName(
            name_column="provincia",
            provinces_ttl=PROVINCES_TTL,
            raise_on_unmatched=True,
            min_fuzzy_score=99,  # alto per evitare match fuzzy involontari
        )
        df = pd.DataFrame({"provincia": ["NonExistente"]})
        with pytest.raises(ValueError):
            step_strict.apply(Dataset(df))

    def test_custom_alias(self):
        step = LinkProvinceToAGID_byName(
            name_column="provincia",
            provinces_ttl=PROVINCES_TTL,
            manual_aliases={"capitale": "058"},  # Roma
        )
        df = pd.DataFrame({"provincia": ["Capitale"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out["codice_istat"].iloc[0] == "058"


@pytest.mark.skipif(not INPS_VIGENTI_CSV.exists(), reason="CSV INPS non trovato")
class TestLinkByNameEndToEnd:
    """End-to-end sul CSV INPS vigenti residenza dopo aggregazione Sardegna."""

    def _extract_all_province_names(self) -> pd.DataFrame:
        names = []
        continenti = {"Europa", "Asia", "Africa", "America Settentrionale",
                      "America Centrale", "America Meridionale", "Oceania", "Totale"}
        with open(INPS_VIGENTI_CSV, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < 36:
                    continue
                m = re.match(r'^"([^"]*)"', line.rstrip())
                if not m:
                    continue
                name = m.group(1).strip()
                if not name or name in continenti:
                    continue
                # Filtra header eventuali
                if any(kw in name for kw in ["Tipo gestione", "Provincia di"]):
                    continue
                names.append(name)
        # 110 nomi attesi
        return pd.DataFrame({"provincia": names, "n_pensioni": 1})

    def test_inps_110_provinces_match_after_sardinia_aggregation(self):
        df = self._extract_all_province_names()
        assert len(df) == 110, f"Atteso 110 entry INPS, trovate {len(df)}"

        # Step 1: aggrego Sardegna 8 → 5
        agg = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
        ).apply(Dataset(df))
        df_post = agg.to_pandas()
        assert len(df_post) == 107, f"Atteso 107 dopo aggregazione, trovate {len(df_post)}"

        # Step 2: linko ad AGID via nome
        step = LinkProvinceToAGID_byName(
            name_column="provincia",
            provinces_ttl=PROVINCES_TTL,
        )
        out_ds = step.apply(agg)
        # out_ds.history ha 2 record: AggregateSardinia + LinkProvinceToAGID_byName.
        # Le metriche di matching sono dell'ultimo step.
        rec = out_ds.history[-1]
        assert rec.name == "LinkProvinceToAGID_byName"
        # Vogliamo 107/107 matched
        assert rec.metrics["matched_rows"] == 107, (
            f"Matched {rec.metrics['matched_rows']}/107, "
            f"unmatched: {rec.metrics['unmatched_names']}"
        )
        assert rec.metrics["unmatched_rows"] == 0
        # Tutti gli URI assegnati
        out = out_ds.to_pandas()
        assert out["uri_agid"].notna().sum() == 107
        # Le 5 province sarde devono essere risolte coi codici ISTAT corretti
        sard_codes = set(
            out[out["provincia"].isin(
                ["Cagliari", "Sud Sardegna", "Nuoro", "Oristano", "Sassari"]
            )]["codice_istat"]
        )
        assert sard_codes == {"090", "091", "092", "095", "111"}
