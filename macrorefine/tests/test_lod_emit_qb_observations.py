"""Test EmitQbObservations — emissione qb:DataSet + qb:Observation in Turtle."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from macrorefine.dataset import Dataset
from macrorefine.steps.lod import EmitQbObservations


# Test fixtures comuni
IDPT_NS = "https://example.org/idpt/"
SAMPLE_DATASET_URI = IDPT_NS + "cubo-test"
SAMPLE_DSD_URI = IDPT_NS + "dsd-test"


def _make_df():
    """Df sintetico con 3 province + URI AGID + n_occupati."""
    return pd.DataFrame({
        "uri_agid": [
            "https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/001",
            "https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/015",
            "https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/058",
        ],
        "codice_istat": ["001", "015", "058"],
        "n_occupati": [947.559, 1500.0, 1200.5],
    })


class TestEmitQbObservationsBasic:
    def test_emits_dataset_and_observations(self, tmp_path):
        """Df 3 righe → 3 obs nel TTL + 1 qb:DataSet."""
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        result = step.apply(Dataset(_make_df()))
        assert out.exists()

        # Verifica via rdflib
        from rdflib import Graph
        g = Graph()
        g.parse(str(out), format="turtle")

        # 3 observation
        n_obs = list(g.query("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        SELECT (COUNT(?o) AS ?n) WHERE { ?o a qb:Observation }
        """))[0][0]
        assert int(n_obs) == 3

        # 1 dataset
        n_ds = list(g.query("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        SELECT (COUNT(?d) AS ?n) WHERE { ?d a qb:DataSet }
        """))[0][0]
        assert int(n_ds) == 1

    def test_obs_uri_template_with_placeholder(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}-2025",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        step.apply(Dataset(_make_df()))
        content = out.read_text(encoding="utf-8")
        # I 3 codici ISTAT devono apparire nelle URI
        assert "obs-test-001-2025" in content
        assert "obs-test-015-2025" in content
        assert "obs-test-058-2025" in content

    def test_constant_dimensions(self, tmp_path):
        """annoRiferimento come dimensione costante con datatype xsd:gYear."""
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            constant_dimensions={
                IDPT_NS + "annoRiferimento": '"2025"^^xsd:gYear',
            },
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        step.apply(Dataset(_make_df()))

        from rdflib import Graph
        g = Graph()
        g.parse(str(out), format="turtle")
        # Tutte le obs hanno annoRiferimento "2025"^^xsd:gYear
        n_year = list(g.query("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX idpt: <https://example.org/idpt/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
        SELECT (COUNT(?o) AS ?n) WHERE {
          ?o a qb:Observation ;
             idpt:annoRiferimento "2025"^^xsd:gYear .
        }
        """))[0][0]
        assert int(n_year) == 3

    def test_default_obs_status_assigned(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        step.apply(Dataset(_make_df()))

        from rdflib import Graph
        g = Graph()
        g.parse(str(out), format="turtle")
        n_normal = list(g.query("""
        PREFIX qb: <http://purl.org/linked-data/cube#>
        PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#>
        PREFIX sdmx-code: <http://purl.org/linked-data/sdmx/2009/code#>
        SELECT (COUNT(?o) AS ?n) WHERE {
          ?o a qb:Observation ;
             sdmx-attribute:obsStatus sdmx-code:obsStatus-A .
        }
        """))[0][0]
        assert int(n_normal) == 3

    def test_dataset_metadata_emitted(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            dataset_metadata={
                "title": "Cubo di test",
                "description": "Descrizione",
                "issued": "2026-05-29",
                "source": "https://example.org/source",
                "license": "https://creativecommons.org/licenses/by/4.0/",
            },
            output_path=out,
        )
        step.apply(Dataset(_make_df()))

        content = out.read_text(encoding="utf-8")
        assert "Cubo di test" in content
        assert "2026-05-29" in content
        assert "creativecommons.org/licenses/by/4.0" in content


class TestEmitQbObservationsHistory:
    def test_metrics_count_correct(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        result = step.apply(Dataset(_make_df()))
        rec = result.history[-1]
        assert rec.metrics["input_rows"] == 3
        assert rec.metrics["observations_emitted"] == 3
        assert rec.metrics["rows_skipped_missing_dimension"] == 0
        assert rec.metrics["triples_written"] > 0

    def test_obs_uri_column_added(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        result = step.apply(Dataset(_make_df()))
        df_out = result.to_pandas()
        assert "_obs_uri" in df_out.columns
        assert df_out["_obs_uri"].iloc[0] == IDPT_NS + "obs-test-001"

    def test_skip_row_with_missing_dimension(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        df = _make_df()
        df.loc[1, "uri_agid"] = None
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-test-{codice_istat}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        result = step.apply(Dataset(df))
        rec = result.history[-1]
        assert rec.metrics["observations_emitted"] == 2
        assert rec.metrics["rows_skipped_missing_dimension"] == 1


class TestEmitQbObservationsErrors:
    def test_missing_column_raises(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-{x}",
            dimensions={"missing_col": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        with pytest.raises(KeyError):
            step.apply(Dataset(_make_df()))

    def test_unknown_template_placeholder_raises(self, tmp_path):
        out = tmp_path / "cubo_test.ttl"
        step = EmitQbObservations(
            dataset_uri=SAMPLE_DATASET_URI,
            dsd_uri=SAMPLE_DSD_URI,
            obs_uri_template=IDPT_NS + "obs-{nonexistent_col}",
            dimensions={"uri_agid": IDPT_NS + "provincia"},
            measures={"n_occupati": IDPT_NS + "numeroOccupati"},
            output_path=out,
        )
        with pytest.raises(KeyError):
            step.apply(Dataset(_make_df()))
