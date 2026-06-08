"""Test ProjectGDPRegimeComposition — Plan B GDP regime composition projection."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import ProjectGDPRegimeComposition
from macrorefine.steps.lod.project import (
    DEFAULT_THRESHOLDS,
    _parse_decorrenza_year,
    compute_national_regime_composition,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DECORRENZA_CSV = (
    PROJECT_ROOT
    / "data"
    / "inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv"
)


class TestParseDecorrenzaYear:
    """Test del parser anno di decorrenza (pure, no I/O)."""

    def test_standard_year(self):
        assert _parse_decorrenza_year("1985") == 1985
        assert _parse_decorrenza_year("2025") == 2025

    def test_anteriore_label(self):
        """'Decorrenza anteriore al 31/12/1980' → 1980 (rappresentativo)."""
        assert _parse_decorrenza_year("Decorrenza anteriore al 31/12/1980") == 1980

    def test_totale_returns_none(self):
        assert _parse_decorrenza_year("Totale") is None

    def test_unparsable_returns_none(self):
        assert _parse_decorrenza_year("foo") is None
        assert _parse_decorrenza_year("") is None


class TestComputeNationalComposition:
    """Test della funzione di composizione nazionale (pure)."""

    def test_basic_three_regimes(self):
        df = pd.DataFrame({
            "anno_decorrenza": [1990, 2000, 2020],
            "numero_pensioni": [100, 200, 300],
        })
        comp = compute_national_regime_composition(df)
        # 100 retributivo, 200 misto-dini, 300 misto-fornero → 600 tot
        assert comp["retributivo"] == pytest.approx(100 / 600)
        assert comp["misto-dini"] == pytest.approx(200 / 600)
        assert comp["misto-fornero"] == pytest.approx(300 / 600)
        assert comp["contributivo-puro"] == 0.0

    def test_fractions_sum_to_one(self):
        df = pd.DataFrame({
            "anno_decorrenza": [1985, 1995, 2005, 2015, 2020, 2025],
            "numero_pensioni": [50, 50, 100, 100, 100, 100],
        })
        comp = compute_national_regime_composition(df)
        total = sum(comp.values())
        assert total == pytest.approx(1.0)

    def test_year_1995_inclusive_retributivo(self):
        """Boundary: 1995 → retributivo (≤ 1995)."""
        df = pd.DataFrame({
            "anno_decorrenza": [1995, 1996],
            "numero_pensioni": [100, 100],
        })
        comp = compute_national_regime_composition(df)
        assert comp["retributivo"] == 0.5
        assert comp["misto-dini"] == 0.5

    def test_year_2012_inclusive_fornero(self):
        """Boundary: 2012 → misto-fornero (≥ 2012)."""
        df = pd.DataFrame({
            "anno_decorrenza": [2011, 2012],
            "numero_pensioni": [100, 100],
        })
        comp = compute_national_regime_composition(df)
        assert comp["misto-dini"] == 0.5
        assert comp["misto-fornero"] == 0.5

    def test_empty_df(self):
        df = pd.DataFrame({"anno_decorrenza": [], "numero_pensioni": []})
        comp = compute_national_regime_composition(df)
        assert all(v == 0.0 for v in comp.values())

    def test_custom_thresholds(self):
        custom = {
            "regime-a": (1900, 2000),
            "regime-b": (2001, 2025),
        }
        df = pd.DataFrame({
            "anno_decorrenza": [1995, 2010],
            "numero_pensioni": [100, 100],
        })
        comp = compute_national_regime_composition(df, thresholds=custom)
        assert comp["regime-a"] == 0.5
        assert comp["regime-b"] == 0.5


class TestProjectGDPRegimeCompositionSynthetic:
    """Test sintetici sullo step (con CSV fittizio inline)."""

    @pytest.fixture
    def fake_decorrenza_csv(self, tmp_path):
        """CSV inline che imita il formato INPS reale."""
        path = tmp_path / "fake_decorrenza.csv"
        content = (
            '"header line 1"\n' * 34
            + '"Anno di decorrenza";"";"Numero Pensioni "\n'
            + '"Decorrenza anteriore al 31/12/1980";"";"100 "\n'
            + '"1990";"";"200 "\n'
            + '"2000";"";"300 "\n'
            + '"2020";"";"400 "\n'
            + '"Totale";"";"1.000 "\n'
        )
        path.write_text(content, encoding="utf-8")
        return path

    def test_long_shape(self, fake_decorrenza_csv):
        """4 regimi × 2 province = 8 righe output."""
        df = pd.DataFrame({
            "provincia": ["Torino", "Roma"],
            "n_pubblici": [10_000, 20_000],
        })
        step = ProjectGDPRegimeComposition(
            count_column="n_pubblici",
            decorrenza_csv=fake_decorrenza_csv,
            output_shape="long",
        )
        out = step.apply(Dataset(df)).to_pandas()
        assert len(out) == 8  # 2 province × 4 regimi
        assert set(out["regime_notation"].unique()) == set(DEFAULT_THRESHOLDS.keys())
        # Sum per provincia = input count (conservazione)
        for prov_name in ("Torino", "Roma"):
            sub = out[out["provincia"] == prov_name]
            total_proj = sub["numero_pensioni_proiettato"].sum()
            input_count = df[df["provincia"] == prov_name]["n_pubblici"].iloc[0]
            assert total_proj == pytest.approx(input_count)
        # _status marcato come estimated_plan_b
        assert (out["_status"] == "estimated_plan_b").all()

    def test_wide_shape(self, fake_decorrenza_csv):
        df = pd.DataFrame({"provincia": ["Torino"], "n_pubblici": [10_000]})
        step = ProjectGDPRegimeComposition(
            count_column="n_pubblici",
            decorrenza_csv=fake_decorrenza_csv,
            output_shape="wide",
        )
        out = step.apply(Dataset(df)).to_pandas()
        # 4 colonne nuove
        for regime in DEFAULT_THRESHOLDS:
            col = f"numero_pensioni_proiettato_{regime}"
            assert col in out.columns
        # Somma colonne = input
        total = sum(
            out[f"numero_pensioni_proiettato_{r}"].iloc[0]
            for r in DEFAULT_THRESHOLDS
        )
        assert total == pytest.approx(10_000)

    def test_records_composition_in_metrics(self, fake_decorrenza_csv):
        df = pd.DataFrame({"provincia": ["X"], "n_pubblici": [100]})
        out_ds = ProjectGDPRegimeComposition(
            count_column="n_pubblici",
            decorrenza_csv=fake_decorrenza_csv,
        ).apply(Dataset(df))
        rec = out_ds.history[0]
        assert "composition_percentages" in rec.metrics
        # Il CSV fittizio ha 100 (≤1980) + 200 (1990) + 300 (2000) + 400 (2020)
        # = 1000 tot. Retributivo = (100+200)/1000 = 30%, Dini = 300/1000 = 30%,
        # Fornero = 400/1000 = 40%.
        comp = rec.metrics["composition_percentages"]
        assert comp["retributivo"] == pytest.approx(30.0)
        assert comp["misto-dini"] == pytest.approx(30.0)
        assert comp["misto-fornero"] == pytest.approx(40.0)

    def test_unknown_shape_raises(self, fake_decorrenza_csv):
        with pytest.raises(ValueError):
            ProjectGDPRegimeComposition(
                count_column="n",
                decorrenza_csv=fake_decorrenza_csv,
                output_shape="invalid",
            )

    def test_missing_count_column_raises(self, fake_decorrenza_csv):
        df = pd.DataFrame({"provincia": ["X"]})
        with pytest.raises(KeyError):
            ProjectGDPRegimeComposition(
                count_column="missing",
                decorrenza_csv=fake_decorrenza_csv,
            ).apply(Dataset(df))

    def test_missing_csv_raises(self):
        df = pd.DataFrame({"n": [10]})
        with pytest.raises(FileNotFoundError):
            ProjectGDPRegimeComposition(
                count_column="n",
                decorrenza_csv="/non/exists.csv",
            ).apply(Dataset(df))


@pytest.mark.skipif(not DECORRENZA_CSV.exists(), reason="CSV decorrenza GDP non trovato")
class TestProjectGDPRegimeCompositionRealCSV:
    """End-to-end sul CSV decorrenza GDP reale (46 righe)."""

    def test_load_decorrenza_csv_yields_46_rows(self):
        from macrorefine.steps.lod.project import _load_decorrenza_csv
        df = _load_decorrenza_csv(DECORRENZA_CSV)
        assert len(df) == 46, f"Atteso 46 anni di decorrenza, trovate {len(df)}"

    def test_national_total_matches_documented(self):
        """Totale nazionale GDP = 3.171.265 (sez. 6 PROGETTO_CONTESTO.md)."""
        from macrorefine.steps.lod.project import _load_decorrenza_csv
        df = _load_decorrenza_csv(DECORRENZA_CSV)
        total = df["numero_pensioni"].sum()
        assert total == 3_171_265, (
            f"Atteso 3.171.265 pensioni GDP nazionali, trovate {total}"
        )

    def test_projection_preserves_provincial_totals(self):
        """Per ogni provincia, sum dei 4 valori proiettati = numero pensioni input."""
        df = pd.DataFrame({
            "provincia": ["Torino", "Roma", "Bolzano"],
            "n_pubblici": [101_503, 234_876, 30_947],
        })
        step = ProjectGDPRegimeComposition(
            count_column="n_pubblici",
            decorrenza_csv=DECORRENZA_CSV,
        )
        out = step.apply(Dataset(df)).to_pandas()
        assert len(out) == 12  # 3 × 4
        for prov in ("Torino", "Roma", "Bolzano"):
            sub = out[out["provincia"] == prov]
            total_proj = sub["numero_pensioni_proiettato"].sum()
            input_count = df[df["provincia"] == prov]["n_pubblici"].iloc[0]
            assert total_proj == pytest.approx(input_count, rel=1e-9), (
                f"Conservazione totale violata per {prov}"
            )

    def test_composition_percentages_reasonable(self):
        """Sanity: le % devono sommare a 100, retributivo non > 50% (storia)."""
        df = pd.DataFrame({"provincia": ["X"], "n_pubblici": [1]})
        out_ds = ProjectGDPRegimeComposition(
            count_column="n_pubblici",
            decorrenza_csv=DECORRENZA_CSV,
        ).apply(Dataset(df))
        comp = out_ds.history[0].metrics["composition_percentages"]
        assert sum(comp.values()) == pytest.approx(100.0, abs=0.1)
        # Retributivo ≤ 50% (la maggioranza GDP è post-1995)
        assert comp["retributivo"] < 50
