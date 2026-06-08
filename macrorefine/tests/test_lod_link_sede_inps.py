"""Test LinkSedeINPS — risoluzione 106 sedi INPS → URI sede + URI provincia AGID."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import LinkSedeINPS
from macrorefine.steps.lod.link import _slugify_inps

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
INPS_REGIME_CSV = (
    PROJECT_ROOT
    / "data"
    / "inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv"
)

rdflib_available = pytest.importorskip("rdflib", reason="rdflib non installato")
ttl_available = pytest.mark.skipif(
    not PROVINCES_TTL.exists(), reason="provinces.ttl non trovato"
)


class TestSlugifyInps:
    """Test pura del normalizer di slug (non richiede rdflib)."""

    def test_simple(self):
        assert _slugify_inps("TORINO") == "torino"

    def test_drops_accents(self):
        assert _slugify_inps("FORLÌ") == "forli"

    def test_collapses_separators(self):
        assert _slugify_inps("PESARO -URBINO") == "pesaro-urbino"
        assert _slugify_inps("BARLETTA -ANDRIA-TRANI") == "barletta-andria-trani"
        assert _slugify_inps("CAGLIARI E SUD SARDEGNA") == "cagliari-e-sud-sardegna"

    def test_handles_slash(self):
        assert _slugify_inps("Bolzano/Bozen") == "bolzano-bozen"

    def test_strips_outer_dashes(self):
        assert _slugify_inps("--TORINO--") == "torino"


@ttl_available
class TestLinkSedeINPSBasic:
    @pytest.fixture(scope="class")
    def step(self):
        return LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
        )

    def test_one_to_one_match(self, step):
        df = pd.DataFrame({"sede": ["TORINO"]})
        out = step.apply(Dataset(df)).to_pandas().iloc[0]
        assert out["slug_sede"] == "torino"
        assert out["uri_sede_inps"].endswith("sede-inps-torino")
        assert out["correspondsto_codice_istat"] == "001"
        assert out["aggregates_codici_istat"] is None
        assert out["uri_provincia_agid_principale"].endswith("/provinces/001")

    def test_one_to_many_cagliari_sud_sardegna(self, step):
        df = pd.DataFrame({"sede": ["CAGLIARI E SUD SARDEGNA"]})
        out = step.apply(Dataset(df)).to_pandas().iloc[0]
        assert out["slug_sede"] == "cagliari-e-sud-sardegna"
        assert out["correspondsto_codice_istat"] is None
        assert out["aggregates_codici_istat"] == "092,111"
        # principale = prima provincia
        assert out["uri_provincia_agid_principale"].endswith("/provinces/092")

    def test_anomaly_verbania_to_vb(self, step):
        """'VERBANIA' (forma sede INPS) → Verbano-Cusio-Ossola (103)."""
        df = pd.DataFrame({"sede": ["VERBANIA"]})
        out = step.apply(Dataset(df)).to_pandas().iloc[0]
        assert out["correspondsto_codice_istat"] == "103"
        assert out["slug_sede"] == "verbania"

    def test_anomalies_typografiche(self, step):
        df = pd.DataFrame({
            "sede": [
                "MASSA CARRARA", "FORLI", "BOLZANO", "TRENTO",
                "PESARO -URBINO", "BARLETTA -ANDRIA-TRANI",
                "REGGIO CALABRIA", "REGGIO EMILIA", "AOSTA",
                "MONZA E DELLA BRIANZA", "FERMO",
            ]
        })
        out = step.apply(Dataset(df)).to_pandas()
        expected_codes = ["045", "040", "021", "022", "041", "110",
                          "080", "035", "007", "108", "109"]
        assert out["correspondsto_codice_istat"].tolist() == expected_codes

    def test_unmatched(self, step):
        df = pd.DataFrame({"sede": ["TORINO", "ATLANTIDE"]})
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["matched_rows"] == 1
        assert rec.metrics["unmatched_rows"] == 1
        assert "ATLANTIDE" in rec.metrics["unmatched_sedi"]

    def test_metrics_distinguish_sources(self, step):
        """Metriche separano 1:1 (direct/alias/fuzzy) e 1:N."""
        df = pd.DataFrame({
            "sede": ["TORINO", "VERBANIA", "CAGLIARI E SUD SARDEGNA"]
        })
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["matched_1_to_N"] == 1
        assert (
            rec.metrics["matched_1_to_1_direct"]
            + rec.metrics["matched_1_to_1_alias"]
            + rec.metrics["matched_1_to_1_fuzzy"]
        ) == 2

    def test_distinct_sedi_metric(self, step):
        """Stessa sede ripetuta = 1 slug distinto."""
        df = pd.DataFrame({"sede": ["TORINO", "TORINO", "MILANO"]})
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["distinct_sedi"] == 2


@ttl_available
class TestLinkSedeINPSSidecar:
    """Test dell'emissione del sidecar inps_to_agid.ttl."""

    def test_emit_sidecar_creates_file(self, tmp_path):
        sidecar = tmp_path / "inps_to_agid.ttl"
        step = LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            emit_sidecar_to=sidecar,
            emit_inps_residence_labels=True,
        )
        df = pd.DataFrame({"sede": ["TORINO", "CAGLIARI E SUD SARDEGNA"]})
        step.apply(Dataset(df))
        assert sidecar.exists()
        content = sidecar.read_text(encoding="utf-8")
        # Verifica triple chiave
        assert "idpt:SedeINPS" in content or "SedeINPS" in content
        assert "sede-inps-torino" in content
        assert "sede-inps-cagliari-e-sud-sardegna" in content
        assert "aggregatesProvince" in content
        assert "correspondsToProvinceAGID" in content

    def test_emit_sidecar_with_altLabels(self, tmp_path):
        """Le 9 altLabel @it-x-inps devono essere presenti se enabled."""
        sidecar = tmp_path / "inps_to_agid.ttl"
        step = LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            emit_sidecar_to=sidecar,
            emit_inps_residence_labels=True,
        )
        df = pd.DataFrame({"sede": ["TORINO"]})
        step.apply(Dataset(df))
        content = sidecar.read_text(encoding="utf-8")
        # Per esempio "Provincia Autonoma di Bolzano/Bozen"@it-x-inps deve essere lì
        assert "it-x-inps" in content
        # Verifica almeno 1 altLabel anomalia (es. Reggio Emilia o Aosta)
        assert (
            "Aosta" in content
            or "Reggio Emilia" in content
            or "Bolzano/Bozen" in content
        )

    def test_sidecar_loadable_by_rdflib(self, tmp_path):
        """Il TTL emesso deve essere riparsabile da rdflib (well-formed)."""
        sidecar = tmp_path / "inps_to_agid.ttl"
        step = LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            emit_sidecar_to=sidecar,
        )
        df = pd.DataFrame({"sede": ["TORINO", "CAGLIARI E SUD SARDEGNA"]})
        step.apply(Dataset(df))

        from rdflib import Graph
        g = Graph()
        g.parse(str(sidecar), format="turtle")
        assert len(g) > 0


@pytest.mark.skipif(not INPS_REGIME_CSV.exists(), reason="CSV INPS regime non trovato")
class TestLinkSedeINPSEndToEnd:
    """End-to-end sul CSV INPS regime sede reale (106 sedi)."""

    def _extract_all_sede_names(self) -> pd.DataFrame:
        names = []
        with open(INPS_REGIME_CSV, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < 36:
                    continue
                m = re.match(r'^"([^"]*)"', line.rstrip())
                if not m:
                    continue
                n = m.group(1).strip()
                if n and n != "Totale":
                    names.append(n)
        return pd.DataFrame({"sede": names})

    def test_all_106_sedi_matched(self, tmp_path):
        df = self._extract_all_sede_names()
        assert len(df) == 106, f"Atteso 106 sedi INPS, trovate {len(df)}"

        sidecar = tmp_path / "inps_to_agid.ttl"
        step = LinkSedeINPS(
            sede_column="sede",
            provinces_ttl=PROVINCES_TTL,
            emit_sidecar_to=sidecar,
        )
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["matched_rows"] == 106, (
            f"Matched {rec.metrics['matched_rows']}/106, "
            f"unmatched: {rec.metrics['unmatched_sedi']}"
        )
        assert rec.metrics["unmatched_rows"] == 0
        # 1 sola sede 1:N
        assert rec.metrics["matched_1_to_N"] == 1
        # Sidecar emesso
        assert sidecar.exists()
        assert rec.metrics["sidecar_emitted"] is True
