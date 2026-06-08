"""Test AggregateSardiniaProvinces — aggregazione 8 ex/sard province → 5."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import AggregateSardiniaProvinces

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPS_VIGENTI_CSV = PROJECT_ROOT / "data" / "inps_pensioni_vigenti_provincia_2026_v1.csv"


class TestAggregateSardiniaSynthetic:
    """Test su dati sintetici per validare la logica di aggregazione."""

    def _make_synthetic_df(self) -> pd.DataFrame:
        """8 entry sarde + 1 entry non-sarda di controllo."""
        return pd.DataFrame({
            "provincia": [
                "Cagliari", "Carbonia -Iglesias", "Medio Campidano",
                "Nuoro", "Ogliastra",
                "Olbia -Tempio", "Oristano", "Sassari",
                "Torino",  # control
            ],
            "n_pensioni": [50, 10, 8, 20, 5, 12, 15, 25, 100],
            "media_mensile": [
                # Importi medi: media pesata su n_pensioni
                1000.0, 800.0, 900.0, 950.0, 850.0,
                1100.0, 920.0, 980.0, 1500.0,
            ],
            "importo_annuo_mln": [
                # Somma diretta (= n × media × 13 / 1e6, ma sintetico)
                0.65, 0.10, 0.09, 0.25, 0.06, 0.17, 0.18, 0.32, 1.95,
            ],
        })

    def test_collapses_8_into_5(self):
        df = self._make_synthetic_df()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()

        # 9 righe input → 6 righe output (5 sarde aggregate + 1 Torino)
        assert len(out) == 6
        # Le 5 province sarde canoniche AGID
        sarde = set(out[out["provincia"] != "Torino"]["provincia"])
        assert sarde == {"Cagliari", "Sud Sardegna", "Nuoro", "Oristano", "Sassari"}

    def test_count_columns_sum_preserved(self):
        """Sanity: la somma dei conteggi pre = post (preservazione del totale)."""
        df = self._make_synthetic_df()
        total_pre = df["n_pensioni"].sum()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()
        total_post = out["n_pensioni"].sum()
        assert total_pre == total_post, (
            f"Totale n_pensioni non conservato: pre={total_pre} post={total_post}"
        )

    def test_sum_columns_preserved(self):
        df = self._make_synthetic_df()
        total_pre = df["importo_annuo_mln"].sum()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()
        total_post = out["importo_annuo_mln"].sum()
        assert total_pre == pytest.approx(total_post)

    def test_weighted_average_correct(self):
        """Per Sud Sardegna (Carbonia + Medio Campidano):
        media pesata = (800*10 + 900*8) / (10+8) = (8000+7200)/18 = 844.444..."""
        df = self._make_synthetic_df()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()
        sud = out[out["provincia"] == "Sud Sardegna"].iloc[0]
        assert sud["media_mensile"] == pytest.approx((800 * 10 + 900 * 8) / 18)
        assert sud["n_pensioni"] == 18
        assert sud["importo_annuo_mln"] == pytest.approx(0.19)

    def test_non_sardinia_rows_intact(self):
        df = self._make_synthetic_df()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()
        torino = out[out["provincia"] == "Torino"].iloc[0]
        assert torino["n_pensioni"] == 100
        assert torino["media_mensile"] == 1500.0

    def test_ex_provinces_dropped(self):
        df = self._make_synthetic_df()
        out = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
            sum_columns=["importo_annuo_mln"],
        ).apply(Dataset(df)).to_pandas()
        ex = {"Carbonia -Iglesias", "Medio Campidano", "Ogliastra", "Olbia -Tempio"}
        assert ex.isdisjoint(set(out["provincia"]))


class TestAggregateSardiniaConfig:
    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            AggregateSardiniaProvinces(
                province_column="provincia",
                count_columns=["n"],
                mode="something_else",
            )

    def test_missing_column_raises(self):
        df = pd.DataFrame({"provincia": ["Cagliari"], "n": [10]})
        ds = Dataset(df)
        with pytest.raises(KeyError):
            AggregateSardiniaProvinces(
                province_column="provincia",
                count_columns=["n"],
                weight_pairs={"missing": "n"},
            ).apply(ds)

    def test_no_sardinia_rows_no_op(self):
        """Df senza righe sarde: lo step non altera il dataset."""
        df = pd.DataFrame({
            "provincia": ["Torino", "Milano"],
            "n_pensioni": [100, 200],
        })
        out_ds = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
        ).apply(Dataset(df))
        out = out_ds.to_pandas()
        assert len(out) == 2
        rec = out_ds.history[0]
        assert rec.metrics["sardinian_rows_collapsed_input"] == 0
        assert rec.metrics["aggregated_groups"] == 0


@pytest.mark.skipif(not INPS_VIGENTI_CSV.exists(), reason="CSV INPS vigenti non trovato")
class TestAggregateSardiniaEndToEnd:
    """Verifica integration sul CSV INPS reale (estratto delle 8 sarde + Torino)."""

    def _extract_inps_rows(self) -> pd.DataFrame:
        """Estrae 8 righe sarde + 1 Torino dal CSV vigenti residenza reale."""
        rows = []
        target_names = set(
            ["Torino", "Cagliari", "Carbonia -Iglesias", "Medio Campidano",
             "Nuoro", "Ogliastra", "Olbia -Tempio", "Oristano", "Sassari"]
        )
        with open(INPS_VIGENTI_CSV, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^"([^"]*)"', line.rstrip())
                if not m:
                    continue
                name = m.group(1).strip()
                if name not in target_names:
                    continue
                # Spezzo la riga per ottenere il "Totale numero pensioni"
                # (colonna 14, da L35 dell'header), cioè 14° colonna 0-indexed dal CSV
                cells = re.findall(r'"([^"]*)"', line)
                # cells[0]=nome, cells[1]="", cells[2..16]=misure dei 5 gruppi gestione
                # cells[14] = Numero Pensioni Totale, cells[15] = Importo Medio Mensile Tot
                tot_n = cells[14].strip()
                tot_mm = cells[15].strip()
                rows.append({
                    "provincia": name,
                    "n_pensioni_str": tot_n,
                    "media_mensile_str": tot_mm,
                })
        return pd.DataFrame(rows)

    def test_aggregation_preserves_totals_on_real_data(self):
        df = self._extract_inps_rows()
        assert len(df) == 9, f"Atteso 9 righe (8 sarde + Torino), trovate {len(df)}"

        # Parsing formato italiano
        from macrorefine.steps.lod import ParseItalianNumbers
        # Rename per match con i nomi attesi dallo step
        df = df.rename(columns={
            "n_pensioni_str": "n_pensioni",
            "media_mensile_str": "media_mensile",
        })
        clean = ParseItalianNumbers(
            columns=["n_pensioni", "media_mensile"]
        ).apply(Dataset(df))

        total_pre = clean.to_pandas()["n_pensioni"].sum()
        out_ds = AggregateSardiniaProvinces(
            province_column="provincia",
            count_columns=["n_pensioni"],
            weight_pairs={"media_mensile": "n_pensioni"},
        ).apply(clean)
        out = out_ds.to_pandas()

        # 9 → 6 righe (5 sarde aggregate + Torino)
        assert len(out) == 6
        # Totale numero pensioni preservato
        total_post = out["n_pensioni"].sum()
        assert total_pre == pytest.approx(total_post), (
            f"Totale pensioni non preservato: pre={total_pre}, post={total_post}"
        )
        # Le 5 province sarde canoniche
        sarde = set(out[out["provincia"] != "Torino"]["provincia"])
        assert sarde == {"Cagliari", "Sud Sardegna", "Nuoro", "Oristano", "Sassari"}
