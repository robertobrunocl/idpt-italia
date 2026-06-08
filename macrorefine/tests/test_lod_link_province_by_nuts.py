"""Test LinkProvinceToAGID_byNUTS — linking NUTS → URI AGID via SPARQL.

I test usano i TTL reali del progetto (data/provinces.ttl + output/mappings/
nuts_aliases.ttl). I path sono relativi al file di test per robustezza:
funziona sia con `pytest` lanciato dalla root del progetto, sia da
macrorefine/.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import LinkProvinceToAGID_byNUTS

# Path ai file reali del progetto (relativo al file di test).
# tests/ → macrorefine/ → Progetto open data/ (project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROVINCES_TTL = PROJECT_ROOT / "data" / "provinces.ttl"
NUTS_ALIASES_TTL = PROJECT_ROOT / "output" / "mappings" / "nuts_aliases.ttl"

# Marker condizionale: alcuni ambienti CI possono non avere rdflib installato.
rdflib_available = pytest.importorskip("rdflib", reason="rdflib non installato")
ttl_available = pytest.mark.skipif(
    not PROVINCES_TTL.exists(),
    reason=f"TTL AGID non trovato: {PROVINCES_TTL}",
)


@ttl_available
class TestLinkProvinceToAGIDByNUTS:
    """Test sul TTL AGID reale + sidecar nuts_aliases.ttl."""

    @pytest.fixture(scope="class")
    def step(self) -> LinkProvinceToAGID_byNUTS:
        """Step costruito una volta per classe (riusa l'index cachato)."""
        return LinkProvinceToAGID_byNUTS(
            nuts_column="REF_AREA",
            provinces_ttl=PROVINCES_TTL,
            nuts_aliases_ttl=NUTS_ALIASES_TTL if NUTS_ALIASES_TTL.exists() else None,
        )

    def test_matches_standard_nuts3(self, step):
        """ITC11 → Torino, codice ISTAT 001, sigla TO."""
        df = pd.DataFrame({"REF_AREA": ["ITC11"]})
        out = step.apply(Dataset(df)).to_pandas()
        row = out.iloc[0]
        assert row["sigla"] == "TO"
        assert row["codice_istat"] == "001"
        assert row["uri_agid"].endswith("/provinces/001")
        assert row["uri_regione_agid"].endswith("/regions/01")

    def test_matches_metro_city_rome(self, step):
        """ITE43 → Roma, codice ISTAT 058."""
        df = pd.DataFrame({"REF_AREA": ["ITE43"]})
        out = step.apply(Dataset(df)).to_pandas()
        row = out.iloc[0]
        assert row["sigla"] == "RM"
        assert row["codice_istat"] == "058"

    def test_matches_pa_via_nuts2_alias(self, step):
        """ITD1 (NUTS-2 PA Bolzano in ISTAT-RFL) → URI AGID Bolzano via alias."""
        if not NUTS_ALIASES_TTL.exists():
            pytest.skip("nuts_aliases.ttl non presente, test alias salta")
        df = pd.DataFrame({"REF_AREA": ["ITD1", "ITD2"]})
        out = step.apply(Dataset(df)).to_pandas()
        # ITD1 → Bolzano (021), ITD2 → Trento (022)
        bz = out.iloc[0]
        tn = out.iloc[1]
        assert bz["codice_istat"] == "021"
        assert bz["sigla"] == "BZ"
        assert tn["codice_istat"] == "022"
        assert tn["sigla"] == "TN"

    def test_matches_fake_nuts_via_skos_exact_match(self, step):
        """I 4 fake-NUTS ISTAT IT108-IT111 → province AGID via skos:exactMatch."""
        if not NUTS_ALIASES_TTL.exists():
            pytest.skip("nuts_aliases.ttl non presente, test fake-NUTS salta")
        df = pd.DataFrame({"REF_AREA": ["IT108", "IT109", "IT110", "IT111"]})
        out = step.apply(Dataset(df)).to_pandas()
        # Codici ISTAT attesi: 108=Monza MB, 109=Fermo FM, 110=BAT, 111=Sud Sardegna SU
        result = list(zip(out["codice_istat"].tolist(), out["sigla"].tolist()))
        assert result == [("108", "MB"), ("109", "FM"), ("110", "BT"), ("111", "SU")]

    def test_unmatched_kept_as_nan(self, step):
        """Codice NUTS inesistente → 4 colonne NaN, registrato in unmatched_codes."""
        df = pd.DataFrame({"REF_AREA": ["ITC11", "BOGUS_NUTS", "ITE43"]})
        out_ds = step.apply(Dataset(df))
        out = out_ds.to_pandas()
        # La riga BOGUS deve avere NaN nelle 4 colonne di output
        bogus = out.iloc[1]
        assert pd.isna(bogus["uri_agid"])
        assert pd.isna(bogus["codice_istat"])
        # Le metriche devono riportare l'unmatched
        rec = out_ds.history[0]
        assert "BOGUS_NUTS" in rec.metrics["unmatched_codes"]
        assert rec.metrics["matched_rows"] == 2
        assert rec.metrics["unmatched_rows"] == 1
        assert rec.metrics["input_rows"] == 3

    def test_index_structural_properties(self, step):
        """Verifiche strutturali sull'index NUTS → provincia.

        Non testiamo il count esatto (fragile: dipende dal numero di NUTS
        condivisi storicamente fra province, es. ITG27 fra Cagliari e Sud
        Sardegna, ITG2A fra Nuoro e Sud Sardegna). Testiamo invece le
        proprietà di copertura:
        - tutti i NUTS-3 di interesse pratico sono presenti
        - i 2 alias PA (ITD1, ITD2) sono presenti via transitività
        - i 4 fake-NUTS ISTAT (IT108-IT111) sono presenti via skos:exactMatch
        - nessuna chiave degenere "-" o "" (URI placeholder AGID)
        """
        if not NUTS_ALIASES_TTL.exists():
            pytest.skip("nuts_aliases.ttl non presente")
        step.apply(Dataset(pd.DataFrame({"REF_AREA": ["ITC11"]})))
        index = step._index
        assert index is not None

        # NUTS standard di sample
        for nuts in ("ITC11", "ITE43", "ITG27"):
            assert nuts in index, f"{nuts} dovrebbe essere nell'index"

        # Alias PA via transitività owl:sameAs+
        assert "ITD1" in index, "ITD1 (NUTS-2 PA Bolzano) dovrebbe essere via alias"
        assert "ITD2" in index, "ITD2 (NUTS-2 PA Trento) dovrebbe essere via alias"
        assert index["ITD1"]["codice_istat"] == "021"  # Bolzano
        assert index["ITD2"]["codice_istat"] == "022"  # Trento

        # Fake-NUTS ISTAT via skos:exactMatch
        for fake, expected_istat in [("IT108", "108"), ("IT109", "109"),
                                      ("IT110", "110"), ("IT111", "111")]:
            assert fake in index, f"{fake} (fake-NUTS ISTAT) dovrebbe essere via skos:exactMatch"
            assert index[fake]["codice_istat"] == expected_istat

        # NESSUNA chiave degenere
        assert "-" not in index, "Chiave '-' (URI AGID placeholder degenere) NON deve essere nell'index"
        assert "" not in index, "Chiave stringa vuota non ammessa"

        # Numero ragionevole di chiavi: ≥ 107 (almeno una per provincia attuale)
        # e ≤ 130 (margine per NUTS storici + alias)
        assert 107 <= len(index) <= 130, (
            f"Index size atteso fra 107 e 130, trovato {len(index)}. "
            f"Se cresce o si riduce verifica i NUTS storici nel TTL AGID."
        )

    def test_record_params(self, step):
        df = pd.DataFrame({"REF_AREA": ["ITC11"]})
        out = step.apply(Dataset(df))
        rec = out.history[0]
        assert rec.name == "LinkProvinceToAGID_byNUTS"
        assert rec.params["nuts_column"] == "REF_AREA"

    def test_shared_nuts_resolves_to_province_with_fewest_nuts(self, step):
        """NUTS condivisi: vince la provincia con MENO NUTS associati.

        Casi:
        - ITC43: Bergamo (016) ha [ITC43, ITC46], Lecco (097) ha [ITC43] →
          Lecco ha meno NUTS → vince Lecco
        - ITG27: Cagliari (092) ha [ITG27], Sud Sardegna (111) ha 5 NUTS →
          Cagliari vince
        - ITG28: Oristano (095) ha [ITG28], Sud Sardegna ha 5 → Oristano vince
        - ITG2A: Nuoro (091) ha [ITG26, ITG2A], Sud Sardegna ha 5 → Nuoro vince
        """
        df = pd.DataFrame({"REF_AREA": ["ITC43", "ITG27", "ITG28", "ITG2A"]})
        out = step.apply(Dataset(df)).to_pandas()
        assert out.iloc[0]["codice_istat"] == "097"  # Lecco, non Bergamo
        assert out.iloc[1]["codice_istat"] == "092"  # Cagliari, non Sud Sardegna
        assert out.iloc[2]["codice_istat"] == "095"  # Oristano, non Sud Sardegna
        assert out.iloc[3]["codice_istat"] == "091"  # Nuoro, non Sud Sardegna


@ttl_available
class TestLinkProvinceToAGIDByNUTSEndToEnd:
    """Test end-to-end sul CSV ISTAT occupati reale (107 entità)."""

    def test_all_107_matched(self):
        """Carica il CSV ISTAT occupati 2025, applica lo step, attende 107/107 matched."""
        csv_path = PROJECT_ROOT / "data" / "istat_occupati_provincia_2025_v1.csv"
        if not csv_path.exists():
            pytest.skip(f"CSV ISTAT occupati non trovato: {csv_path}")
        if not NUTS_ALIASES_TTL.exists():
            pytest.skip("nuts_aliases.ttl non presente, test integration salta")

        df = pd.read_csv(csv_path, dtype=str, encoding="utf-8-sig")
        assert df.shape[0] == 107, f"Atteso 107 righe ISTAT, trovate {df.shape[0]}"

        step = LinkProvinceToAGID_byNUTS(
            nuts_column="REF_AREA",
            provinces_ttl=PROVINCES_TTL,
            nuts_aliases_ttl=NUTS_ALIASES_TTL,
        )
        out_ds = step.apply(Dataset(df))
        rec = out_ds.history[0]
        assert rec.metrics["matched_rows"] == 107, (
            f"Matched {rec.metrics['matched_rows']}/107, "
            f"unmatched: {rec.metrics['unmatched_codes']}"
        )
        assert rec.metrics["unmatched_rows"] == 0
        # Tutte le righe hanno URI AGID
        out = out_ds.to_pandas()
        assert out["uri_agid"].notna().sum() == 107
