"""Test scripts/generate_agid_to_dbpedia.py — logica di reconciliation senza rete.

Lo script vero richiede rete verso DBpedia. Qui mockiamo la risposta SPARQL
con fixture inline e testiamo solo la logica:

1. Match esatto via prefLabel normalizzato
2. Reconciliation via DBPEDIA_MANUAL_OVERRIDES (priorità massima)
3. Identificazione unmatched
4. Serializzazione TTL well-formed

I test end-to-end con rete vera vengono eseguiti dal Mac dell'utente.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Aggiungo scripts/ al path per importare i moduli dello script
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

# Importo le funzioni testabili
from generate_agid_to_dbpedia import (  # noqa: E402
    DBPEDIA_MANUAL_OVERRIDES,
    _equivalent_forms,
    _strip_dbpedia_prefix,
    emit_agid_to_dbpedia_sidecar,
    reconcile_dbpedia_to_agid,
)


# Fixture: 3 risorse DBpedia che imitano una risposta SPARQL.
SAMPLE_DBPEDIA_RESPONSE = [
    {
        "resource": "http://dbpedia.org/resource/Province_of_Vercelli",
        "label_it": "Provincia di Vercelli",
        "label_en": "Province of Vercelli",
    },
    {
        "resource": "http://dbpedia.org/resource/Province_of_Cuneo",
        "label_it": "Provincia di Cuneo",
        "label_en": "Province of Cuneo",
    },
    {
        "resource": "http://dbpedia.org/resource/Province_of_Asti",
        "label_it": "Asti",   # qui label corta — match diretto su "asti"
        "label_en": "Asti",
    },
]

# AGID fittizio: 4 province (Vercelli 002, Cuneo 004, Asti 005, Torino 001).
# Torino è città metropolitana → matcha via DBPEDIA_MANUAL_OVERRIDES anche
# se non è in SAMPLE_DBPEDIA_RESPONSE.
SAMPLE_AGID = {
    "001": {"uri_agid": "https://w3id.org/.../001", "prefLabel": "Torino"},
    "002": {"uri_agid": "https://w3id.org/.../002", "prefLabel": "Vercelli"},
    "004": {"uri_agid": "https://w3id.org/.../004", "prefLabel": "Cuneo"},
    "005": {"uri_agid": "https://w3id.org/.../005", "prefLabel": "Asti"},
}


class TestReconcileDbpediaToAgid:
    def test_manual_override_has_priority(self):
        """Torino (001) è in DBPEDIA_MANUAL_OVERRIDES → preso da lì
        anche se non è in SAMPLE_DBPEDIA_RESPONSE."""
        mapping, unmatched = reconcile_dbpedia_to_agid(
            SAMPLE_DBPEDIA_RESPONSE, SAMPLE_AGID
        )
        assert mapping["001"] == DBPEDIA_MANUAL_OVERRIDES["001"]

    def test_direct_match_via_normalized_label(self):
        """Asti DBpedia label "Asti" → match diretto con AGID "Asti"."""
        mapping, unmatched = reconcile_dbpedia_to_agid(
            SAMPLE_DBPEDIA_RESPONSE, SAMPLE_AGID
        )
        assert mapping["005"] == "http://dbpedia.org/resource/Province_of_Asti"

    def test_match_via_label_with_prefix_now_resolved(self):
        """DBpedia label "Provincia di Vercelli" → strip prefisso "Provincia di"
        → "vercelli" → match con AGID "Vercelli".

        Test originale (Fase 1 blocco 3) verificava che fosse unmatched: con la
        prima esecuzione lato Mac si è scoperto che 71/107 finivano lì.
        Riprogettato il reconcile con strip dei prefissi DBpedia + varianti
        "e"/"and" → ora deve matchare.
        """
        mapping, unmatched = reconcile_dbpedia_to_agid(
            SAMPLE_DBPEDIA_RESPONSE, SAMPLE_AGID
        )
        assert mapping["002"] == "http://dbpedia.org/resource/Province_of_Vercelli"
        assert "002" not in unmatched

    def test_match_via_label_and_to_e_variant(self):
        """Pesaro: AGID "Pesaro e Urbino", DBpedia "Province of Pesaro and Urbino"
        → strip "Province of" → "pesaro and urbino" → _equivalent_forms genera
        anche "pesaro e urbino" → match."""
        rows = [{
            "resource": "http://dbpedia.org/resource/Province_of_Pesaro_and_Urbino",
            "label_it": "",
            "label_en": "Province of Pesaro and Urbino",
        }]
        agid = {"041": {"uri_agid": "...", "prefLabel": "Pesaro e Urbino"}}
        mapping, unmatched = reconcile_dbpedia_to_agid(rows, agid, manual_overrides={})
        assert mapping["041"] == "http://dbpedia.org/resource/Province_of_Pesaro_and_Urbino"

    def test_custom_overrides(self):
        """L'utente passa override manuali → priorità su tutto."""
        custom = {"002": "http://dbpedia.org/resource/CustomVercelli"}
        mapping, unmatched = reconcile_dbpedia_to_agid(
            SAMPLE_DBPEDIA_RESPONSE, SAMPLE_AGID, manual_overrides=custom
        )
        assert mapping["002"] == "http://dbpedia.org/resource/CustomVercelli"

    def test_unmatched_returns_codes(self):
        """Una provincia AGID senza match → finisce in unmatched."""
        extra_agid = dict(SAMPLE_AGID)
        extra_agid["999"] = {"uri_agid": "x", "prefLabel": "NomeInesistente"}
        mapping, unmatched = reconcile_dbpedia_to_agid(
            SAMPLE_DBPEDIA_RESPONSE, extra_agid
        )
        assert "999" in unmatched
        assert "999" not in mapping


class TestStripDbpediaPrefix:
    def test_strips_province_of_en(self):
        assert _strip_dbpedia_prefix("province of vercelli") == "vercelli"

    def test_strips_provincia_di_it(self):
        assert _strip_dbpedia_prefix("provincia di vercelli") == "vercelli"

    def test_strips_metropolitan_city_of(self):
        assert _strip_dbpedia_prefix("metropolitan city of turin") == "turin"

    def test_strips_free_municipal_consortium(self):
        """Province siciliane post-riforma 2014."""
        assert _strip_dbpedia_prefix("free municipal consortium of agrigento") == "agrigento"

    def test_no_prefix_no_change(self):
        assert _strip_dbpedia_prefix("torino") == "torino"


class TestEquivalentForms:
    def test_basic_no_e_no_and(self):
        assert _equivalent_forms("torino") == {"torino"}

    def test_e_generates_and(self):
        forms = _equivalent_forms("pesaro e urbino")
        assert "pesaro e urbino" in forms
        assert "pesaro and urbino" in forms

    def test_and_generates_e(self):
        forms = _equivalent_forms("pesaro and urbino")
        assert "pesaro and urbino" in forms
        assert "pesaro e urbino" in forms


class TestEmitSidecar:
    def test_creates_valid_ttl(self, tmp_path):
        out = tmp_path / "agid_to_dbpedia.ttl"
        mapping = {
            "001": "http://dbpedia.org/resource/Metropolitan_City_of_Turin",
            "058": "http://dbpedia.org/resource/Metropolitan_City_of_Rome_Capital",
        }
        emit_agid_to_dbpedia_sidecar(mapping, out)
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "owl:sameAs" in content
        assert "Metropolitan_City_of_Turin" in content
        assert "Metropolitan_City_of_Rome_Capital" in content

    def test_ttl_reparseable(self, tmp_path):
        """Il TTL emesso deve essere riparsabile da rdflib (well-formed)."""
        out = tmp_path / "agid_to_dbpedia.ttl"
        mapping = {"001": "http://dbpedia.org/resource/Metropolitan_City_of_Turin"}
        emit_agid_to_dbpedia_sidecar(mapping, out)
        from rdflib import Graph
        g = Graph()
        g.parse(str(out), format="turtle")
        # Header (~5 triple) + 1 owl:sameAs = ≥ 6 triple
        assert len(g) >= 6

    def test_includes_provenance_header(self, tmp_path):
        out = tmp_path / "agid_to_dbpedia.ttl"
        emit_agid_to_dbpedia_sidecar({}, out)  # mapping vuoto
        content = out.read_text(encoding="utf-8")
        # Header DCTERMS deve essere presente
        assert "dcterms:created" in content or "created" in content
        assert "dbpedia" in content.lower()


class TestManualOverridesIntegrity:
    """Sanity check del dizionario DBPEDIA_MANUAL_OVERRIDES."""

    def test_overrides_cover_all_metro_cities(self):
        """Le 14 città metropolitane devono essere tutte in override
        (DBpedia non le modella come dbo:Province standard)."""
        metro_codes = {
            "001", "010", "015", "027", "037", "048", "058",
            "063", "072", "080", "082", "083", "087", "092",
        }
        for code in metro_codes:
            assert code in DBPEDIA_MANUAL_OVERRIDES, (
                f"Città metropolitana {code} manca da DBPEDIA_MANUAL_OVERRIDES"
            )

    def test_overrides_cover_known_anomalies(self):
        """Anomalie nominali documentate (PA, Reggio C/E, BAT, Sud Sardegna,
        Monza, Fermo, Forlì-Cesena, Massa-Carrara, VB) devono esserci."""
        anomalies = {
            "007", "021", "022", "035", "040", "045",
            "103", "108", "109", "110", "111",
        }
        for code in anomalies:
            assert code in DBPEDIA_MANUAL_OVERRIDES, (
                f"Anomalia nominale {code} manca da DBPEDIA_MANUAL_OVERRIDES"
            )

    def test_overrides_uris_are_dbpedia(self):
        """Tutti gli URI di override devono puntare a dbpedia.org/resource/."""
        for code, uri in DBPEDIA_MANUAL_OVERRIDES.items():
            assert uri.startswith("http://dbpedia.org/resource/"), (
                f"Override {code} non punta a dbpedia.org: {uri}"
            )

    def test_overrides_cover_second_iteration_residuals(self):
        """Le 5 province scoperte alla seconda iterazione (Varese, Sondrio, Lecce,
        Lecco, Prato) devono essere in overrides — la query DBpedia non le
        restituisce perché manca `dbo:country=Italy` o equivalente."""
        residual = {"012", "014", "075", "097", "100"}
        for code in residual:
            assert code in DBPEDIA_MANUAL_OVERRIDES
