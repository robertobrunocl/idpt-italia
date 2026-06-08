"""Test LinkProvinceToAGID_bySigla — match via Sigla Provincia (chiave MEF)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import LinkProvinceToAGID_bySigla

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
MEF_CSV = PROJECT_ROOT / "data" / "mef_redditi_irpef_comune_2024_v1.csv"

rdflib_available = pytest.importorskip("rdflib", reason="rdflib non installato")
ttl_available = pytest.mark.skipif(
    not PROVINCES_TTL.exists(), reason="provinces.ttl non trovato"
)


@ttl_available
class TestLinkProvinceToAGIDBySigla:
    @pytest.fixture(scope="class")
    def step(self):
        return LinkProvinceToAGID_bySigla(
            sigla_column="Sigla Provincia",
            provinces_ttl=PROVINCES_TTL,
        )

    def test_matches_uppercase(self, step):
        df = pd.DataFrame({"Sigla Provincia": ["TO", "RM", "MI"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out["codice_istat"].tolist() == ["001", "058", "015"]
        assert out["uri_agid"].iloc[0].endswith("/provinces/001")

    def test_case_insensitive(self, step):
        df = pd.DataFrame({"Sigla Provincia": ["to", "Rm", "mI"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out["codice_istat"].tolist() == ["001", "058", "015"]

    def test_unmatched_kept_as_nan(self, step):
        df = pd.DataFrame({"Sigla Provincia": ["TO", "XX", "ZZ"]})
        out_ds = step.apply(Dataset(df))
        out = out_ds.to_pandas()
        assert pd.isna(out["uri_agid"].iloc[1])
        rec = out_ds.history[0]
        assert "XX" in rec.metrics["unmatched_codes"]
        assert "ZZ" in rec.metrics["unmatched_codes"]
        assert rec.metrics["matched_rows"] == 1

    def test_index_has_107_sigle(self, step):
        step.apply(Dataset(pd.DataFrame({"Sigla Provincia": ["TO"]})))
        assert len(step._index) == 107

    def test_special_sigle_present(self, step):
        """Le 4 sigle moderne BT, FM, MB, SU devono essere nell'index."""
        step.apply(Dataset(pd.DataFrame({"Sigla Provincia": ["TO"]})))
        for s in ("BT", "FM", "MB", "SU"):
            assert s in step._index, f"sigla {s} mancante nell'index"


@pytest.mark.skipif(not MEF_CSV.exists(), reason="CSV MEF non trovato")
class TestLinkBySigla_EndToEnd:
    def test_mef_aggregated_by_sigla_matches_107(self):
        """Aggregato per Sigla Provincia, il CSV MEF deve dare 107 sigle uniche
        risolvibili (escludendo riga sentinella "0" + 92 NA Napoli risolti con
        keep_default_na=False)."""
        df = pd.read_csv(
            MEF_CSV, sep=";", dtype=str, encoding="utf-8",
            keep_default_na=False,  # fix per "NA" Napoli interpretato come NaN
            usecols=["Sigla Provincia"],
        )
        # Escludo riga sentinella ("0") + eventuali stringhe vuote residue
        df = df[df["Sigla Provincia"].str.strip() != "0"]
        df = df[df["Sigla Provincia"].str.strip() != ""]
        # Deduplica per sigla
        df_unique = df.drop_duplicates(subset="Sigla Provincia").reset_index(drop=True)
        assert df_unique.shape[0] == 107, (
            f"Atteso 107 sigle uniche dopo cleanup, trovate {df_unique.shape[0]}"
        )

        step = LinkProvinceToAGID_bySigla(
            sigla_column="Sigla Provincia",
            provinces_ttl=PROVINCES_TTL,
        )
        out_ds = step.apply(Dataset(df_unique))
        rec = out_ds.history[0]
        assert rec.metrics["matched_rows"] == 107, (
            f"Matched {rec.metrics['matched_rows']}/107, "
            f"unmatched: {rec.metrics['unmatched_codes']}"
        )
        assert rec.metrics["unmatched_rows"] == 0
