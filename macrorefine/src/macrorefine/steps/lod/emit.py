"""EmitQbObservations — materializza qb:DataSet + qb:Observation in Turtle.

Step finale di ogni Recipe di cubo. Prende il df arricchito di metadata
(URI provincia AGID, codici, misure parsate) e scrive
``output/observations/cuboN_*.ttl`` con:

- 1 ``qb:DataSet`` con ``qb:structure`` verso la DSD + metadati ``dcterms:``
- 1 ``qb:Observation`` per riga, con dimensioni + misure + obsStatus
- attributi a livello DataSet (``unitMeasure`` quando uniforme) o
  Observation (``unitMeasure`` quando variabile per riga)

Pattern riusabile per tutti e 9 i cubi del progetto idpt-italia.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from macrorefine.history import StepRecord
from macrorefine.step import PipelineStep

if TYPE_CHECKING:
    from macrorefine.dataset import Dataset


# Default URI per sdmx-attribute:obsStatus = Normal (cubi con dati primari)
SDMX_OBS_STATUS_NORMAL = "http://purl.org/linked-data/sdmx/2009/code#obsStatus-A"
SDMX_ATTRIBUTE_OBS_STATUS = "http://purl.org/linked-data/sdmx/2009/attribute#obsStatus"

# Default property qb (URI completi)
QB_DATASET = "http://purl.org/linked-data/cube#dataSet"
QB_OBSERVATION = "http://purl.org/linked-data/cube#Observation"
QB_DATASET_CLS = "http://purl.org/linked-data/cube#DataSet"
QB_STRUCTURE = "http://purl.org/linked-data/cube#structure"
QB_MEASURE_TYPE = "http://purl.org/linked-data/cube#measureType"


class EmitQbObservations(PipelineStep):
    """Materializza un cubo qb in Turtle leggendo le righe del df.

    Args:
        dataset_uri: URI del ``qb:DataSet`` (es. ``idpt:cubo-occupati-istat``).
        dsd_uri: URI della ``qb:DataStructureDefinition`` associata.
        obs_uri_template: f-string Python che genera l'URI dell'observation
            interpolando colonne del df. Esempio:
            ``"https://example.org/idpt/obs-occupati-{codice_istat}-2025"``.
            Tutti i placeholder ``{name}`` devono corrispondere a colonne del df.
        dimensions: dict ``{nome_colonna_df: uri_property_dimension}``. Per ogni
            riga emette ``<obs> <property> <valore>`` dove ``<valore>`` è
            interpretato come URI se inizia con ``http://`` o ``https://``,
            altrimenti come literal.
        measures: dict ``{nome_colonna_df: uri_property_measure}``. Valori
            sempre literal (typed). Default: tipo inferito da pandas dtype
            (int → xsd:integer/nonNegativeInteger, float → xsd:decimal).
        constant_dimensions: dict ``{uri_property: literal | uri}`` per
            dimensioni con valore costante per tutto il dataset (es.
            ``annoRiferimento``). I valori literal vanno espressi con il
            datatype esplicito tra backtick, es. ``'"2025"^^xsd:gYear'``.
        dataset_metadata: dict ``{key: value}`` con keys fra
            ``title, description, issued, source, license, rights``.
            Emessi come ``dcterms:*`` sul ``qb:DataSet``.
        dataset_attributes: dict ``{uri_attribute: literal | uri}`` per
            attributi qb a livello DataSet (es. ``unitMeasure``).
        default_obs_status: URI dello stato da assegnare a tutte le obs
            (default = obsStatus-A Normal). Per cubi con obs derivate
            (cubi 8/9) la Recipe userà ``obsStatus-E`` Estimated.
        output_path: dove scrivere il file TTL.
        rdf_prefixes: dict di prefix utente da bindare nel TTL (oltre ai
            default qb/skos/sdmx/clv/idpt/dcterms/xsd).

    Output:
        Il df ritornato ha 1 colonna aggiunta ``_obs_uri`` con l'URI di ogni
        observation emessa (utile per i cubi successivi 8/9 che dovranno
        puntarvi via ``prov:wasDerivedFrom``).

    Metriche:
        - ``observations_emitted``: numero obs scritte
        - ``output_path``: path del file TTL
        - ``triples_written``: stima triple totali (dataset + obs)
    """

    def __init__(
        self,
        dataset_uri: str,
        dsd_uri: str,
        obs_uri_template: str,
        dimensions: dict[str, str | tuple[str, str]],
        measures: dict[str, str],
        output_path: str | Path,
        constant_dimensions: dict[str, str] | None = None,
        dataset_metadata: dict[str, str] | None = None,
        dataset_attributes: dict[str, str] | None = None,
        observation_attributes: dict[str, str] | None = None,
        default_obs_status: str = SDMX_OBS_STATUS_NORMAL,
        obs_status_column: str | None = None,
        prov_derived_from_column: str | None = None,
        measure_type_column: str | None = None,
        value_column: str | None = None,
        rdf_prefixes: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self.dataset_uri = dataset_uri
        self.dsd_uri = dsd_uri
        self.obs_uri_template = obs_uri_template
        self.dimensions = dict(dimensions)
        self.measures = dict(measures)
        self.constant_dimensions = dict(constant_dimensions) if constant_dimensions else {}
        self.dataset_metadata = dict(dataset_metadata) if dataset_metadata else {}
        self.dataset_attributes = dict(dataset_attributes) if dataset_attributes else {}
        self.observation_attributes = (
            dict(observation_attributes) if observation_attributes else {}
        )
        self.default_obs_status = default_obs_status
        self.obs_status_column = obs_status_column
        self.prov_derived_from_column = prov_derived_from_column
        self.measure_type_column = measure_type_column
        self.value_column = value_column
        # Stile B: se measure_type_column è passato, value_column deve esserlo
        if (measure_type_column is None) != (value_column is None):
            raise ValueError(
                "EmitQbObservations: measure_type_column e value_column devono "
                "essere passati insieme (stile B qb:measureType)."
            )
        self.output_path = Path(output_path)
        self.rdf_prefixes = dict(rdf_prefixes) if rdf_prefixes else {}

    # ------------------------------------------------------------------ apply

    def apply(self, dataset: "Dataset") -> "Dataset":
        from rdflib import Graph, Literal, Namespace, URIRef
        from rdflib.namespace import DCTERMS, RDF, XSD

        df = dataset.to_pandas()

        # Verifica colonne richieste
        required_cols = (
            list(self.dimensions.keys())
            + list(self.measures.keys())
            + list(self.observation_attributes.keys())
        )
        if self.measure_type_column:
            required_cols.append(self.measure_type_column)
        if self.value_column:
            required_cols.append(self.value_column)
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise KeyError(
                f"EmitQbObservations: colonne mancanti nel dataset: {missing}. "
                f"Disponibili: {list(df.columns)}"
            )

        # Bind prefissi standard del progetto
        g = Graph()
        QB = Namespace("http://purl.org/linked-data/cube#")
        SDMX_ATTR = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
        IDPT = Namespace("https://example.org/idpt/")
        AGIDP = Namespace(
            "https://w3id.org/italia/controlled-vocabulary/"
            "territorial-classifications/provinces/"
        )
        g.bind("qb", QB)
        g.bind("sdmx-attribute", SDMX_ATTR)
        g.bind("dcterms", DCTERMS)
        g.bind("xsd", XSD)
        g.bind("idpt", IDPT)
        g.bind("agidp", AGIDP)
        for prefix, ns in self.rdf_prefixes.items():
            g.bind(prefix, Namespace(ns))

        # ---- 1. Emissione del qb:DataSet con metadati e attributi -----
        ds_uri = URIRef(self.dataset_uri)
        g.add((ds_uri, RDF.type, URIRef(QB_DATASET_CLS)))
        g.add((ds_uri, URIRef(QB_STRUCTURE), URIRef(self.dsd_uri)))

        # Metadati dcterms
        dcterms_map = {
            "title": DCTERMS.title,
            "description": DCTERMS.description,
            "issued": DCTERMS.issued,
            "source": DCTERMS.source,
            "license": DCTERMS.license,
            "rights": DCTERMS.rights,
        }
        for key, val in self.dataset_metadata.items():
            if key not in dcterms_map:
                # Permettiamo anche URI complete in caso di custom
                pred = URIRef(key)
            else:
                pred = dcterms_map[key]
            # Auto-detect URI vs literal: se inizia con http(s), è URI
            if isinstance(val, str) and val.startswith(("http://", "https://")):
                g.add((ds_uri, pred, URIRef(val)))
            elif key == "issued" and isinstance(val, str):
                g.add((ds_uri, pred, Literal(val, datatype=XSD.date)))
            else:
                g.add((ds_uri, pred, Literal(val, lang="it")))

        # Attributi a livello DataSet
        for attr_uri, val in self.dataset_attributes.items():
            obj = self._serialize_value(val)
            g.add((ds_uri, URIRef(attr_uri), obj))

        # ---- 2. Emissione delle qb:Observation -----------------------
        obs_uris_list: list[str] = []
        skipped = 0
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            # Skip riga se mancano valori chiave (es. provincia non risolta)
            if any(pd.isna(row_dict.get(c)) for c in self.dimensions):
                obs_uris_list.append(None)  # type: ignore[arg-type]
                skipped += 1
                continue

            # Costruisco URI obs interpolando placeholder
            try:
                obs_uri_str = self.obs_uri_template.format(**row_dict)
            except KeyError as e:
                raise KeyError(
                    f"Placeholder {e} in obs_uri_template non trovato come colonna del df"
                )
            obs_uri = URIRef(obs_uri_str)
            obs_uris_list.append(obs_uri_str)

            g.add((obs_uri, RDF.type, URIRef(QB_OBSERVATION)))
            g.add((obs_uri, URIRef(QB_DATASET), ds_uri))

            # Dimensioni variabili
            for col, prop_spec in self.dimensions.items():
                val = row_dict[col]
                if isinstance(prop_spec, tuple):
                    # (uri_property, xsd_datatype) → literal tipato
                    prop_uri, datatype_short = prop_spec
                    obj = self._make_typed_literal(val, datatype_short)
                else:
                    prop_uri = prop_spec
                    obj = self._serialize_value(val)
                g.add((obs_uri, URIRef(prop_uri), obj))

            # Dimensioni costanti
            for prop_uri, raw_val in self.constant_dimensions.items():
                obj = self._serialize_value(raw_val)
                g.add((obs_uri, URIRef(prop_uri), obj))

            # Misure: stile A (multi-measure per obs) vs stile B (1 obs = 1 misura via qb:measureType)
            if self.measure_type_column and self.value_column:
                # Stile B: leggi URI della measure-property dalla colonna e
                # emetti solo quella per la riga, + dimensione qb:measureType
                measure_prop_uri = str(row_dict[self.measure_type_column])
                val = row_dict[self.value_column]
                if not pd.isna(val) and measure_prop_uri:
                    g.add((obs_uri, URIRef(measure_prop_uri),
                           self._infer_measure_literal(val)))
                    g.add((obs_uri, URIRef(QB_MEASURE_TYPE),
                           URIRef(measure_prop_uri)))
            else:
                # Stile A: emetti tutte le misure dichiarate per ogni obs
                for col, prop_uri in self.measures.items():
                    val = row_dict[col]
                    if pd.isna(val):
                        continue
                    obj = self._infer_measure_literal(val)
                    g.add((obs_uri, URIRef(prop_uri), obj))

            # obsStatus: variabile per riga se obs_status_column passato, altrimenti default
            if self.obs_status_column and self.obs_status_column in row_dict:
                status_val = row_dict[self.obs_status_column]
                if pd.notna(status_val):
                    g.add((obs_uri, URIRef(SDMX_ATTRIBUTE_OBS_STATUS), URIRef(str(status_val))))
                else:
                    g.add((obs_uri, URIRef(SDMX_ATTRIBUTE_OBS_STATUS), URIRef(self.default_obs_status)))
            else:
                g.add((obs_uri, URIRef(SDMX_ATTRIBUTE_OBS_STATUS), URIRef(self.default_obs_status)))

            # prov:wasDerivedFrom: 1+ URI sorgenti se prov_derived_from_column passato
            # (utile per cubi 8 IDPT-computed e 9 Plan B che derivano da altre obs).
            # Il valore della colonna può essere stringa singola (1 URI) o lista di stringhe.
            if self.prov_derived_from_column and self.prov_derived_from_column in row_dict:
                prov_val = row_dict[self.prov_derived_from_column]
                if isinstance(prov_val, (list, tuple)):
                    uris = [str(u) for u in prov_val if u and not pd.isna(u)]
                elif pd.notna(prov_val) and prov_val:
                    uris = [str(prov_val)]
                else:
                    uris = []
                from rdflib.namespace import Namespace
                PROV = Namespace("http://www.w3.org/ns/prov#")
                g.bind("prov", PROV)
                for source_uri in uris:
                    g.add((obs_uri, URIRef(str(PROV.wasDerivedFrom)), URIRef(source_uri)))

            # Attributi a livello observation (es. unitMeasure variabile)
            for col, attr_uri in self.observation_attributes.items():
                val = row_dict.get(col)
                if pd.isna(val):
                    continue
                obj = self._serialize_value(val)
                g.add((obs_uri, URIRef(attr_uri), obj))

        # ---- 3. Serializzazione su file -----------------------
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(self.output_path), format="turtle")

        # Aggiungo colonna _obs_uri al df ritornato
        df_out = df.copy()
        df_out["_obs_uri"] = obs_uris_list

        record = StepRecord(
            name=self.name,
            params={
                "dataset_uri": self.dataset_uri,
                "dsd_uri": self.dsd_uri,
                "obs_uri_template": self.obs_uri_template,
                "dimensions": dict(self.dimensions),
                "measures": dict(self.measures),
                "constant_dimensions": dict(self.constant_dimensions),
                "default_obs_status": self.default_obs_status,
                "output_path": str(self.output_path),
            },
            metrics={
                "input_rows": int(len(df)),
                "observations_emitted": int(len(df) - skipped),
                "rows_skipped_missing_dimension": skipped,
                "triples_written": int(len(g)),
            },
        )
        return dataset.with_data(df_out, step_record=record)

    # --------------------------------------------------------- helpers

    @staticmethod
    def _serialize_value(val: Any) -> Any:
        """Serializza un valore come URIRef o Literal a seconda della forma.

        - Se inizia con http(s):// → URIRef
        - Se contiene "^^" o "@" → literal tipato/lingua già esplicito
        - Altrimenti → Literal stringa plain
        """
        from rdflib import Literal, URIRef
        from rdflib.namespace import XSD

        s = str(val)
        if s.startswith(("http://", "https://")):
            return URIRef(s)
        if '^^' in s or s.startswith('"'):
            # Forma "valore"^^datatype o "valore"@lang.
            # Parse manuale: cerca "^^xsd:..." al termine
            if '^^' in s:
                value_part, _, dt_part = s.partition('^^')
                value_clean = value_part.strip('"')
                # Prova mapping xsd: → URI
                if dt_part.startswith('xsd:'):
                    dt_uri = str(XSD) + dt_part[4:]
                else:
                    dt_uri = dt_part.strip('<>')
                return Literal(value_clean, datatype=URIRef(dt_uri))
            if '@' in s:
                value_part, _, lang = s.rpartition('@')
                value_clean = value_part.strip('"')
                return Literal(value_clean, lang=lang)
        # Default: literal plain
        return Literal(s)

    @staticmethod
    def _make_typed_literal(val: Any, datatype_short: str) -> Any:
        """Crea un Literal con datatype xsd: esplicito.

        Args:
            val: il valore (str, int, float).
            datatype_short: short name (es. "xsd:gYear") o URI completo.
        """
        from rdflib import Literal, URIRef
        from rdflib.namespace import XSD

        if datatype_short.startswith("xsd:"):
            dt_uri = URIRef(str(XSD) + datatype_short[4:])
        else:
            dt_uri = URIRef(datatype_short)
        return Literal(str(val), datatype=dt_uri)

    @staticmethod
    def _infer_measure_literal(val: Any) -> Any:
        """Inferisce il datatype xsd per una misura numerica."""
        from rdflib import Literal
        from rdflib.namespace import XSD

        # Bool prima di int (in pandas isinstance(True, int) è True)
        if isinstance(val, bool):
            return Literal(val, datatype=XSD.boolean)
        if isinstance(val, int):
            if val >= 0:
                return Literal(val, datatype=XSD.nonNegativeInteger)
            return Literal(val, datatype=XSD.integer)
        if isinstance(val, float):
            # Se è float ma rappresenta intero ("100.0" → 100), usa integer
            if val.is_integer() and val >= 0:
                return Literal(int(val), datatype=XSD.nonNegativeInteger)
            return Literal(val, datatype=XSD.decimal)
        return Literal(val)
