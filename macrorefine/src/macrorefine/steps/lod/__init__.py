"""Step custom LOD-aware del progetto idpt-italia.

Questo sotto-pacchetto raccoglie gli step macrorefine specializzati per il
caso d'uso "Linked Open Data delle pensioni italiane". Sono separati dai
built-in (NormalizeColumnNames, FillMissing, ecc.) perché incorporano
conoscenza di dominio:

- Parsing del formato numerico italiano (separatore migliaia `.`, decimali `,`)
- Stima dell'importo annuo come `numero × media_mensile × 13`
- Linking di dati ISTAT/INPS/MEF al vocabolario AGID OntoPiA tramite NUTS,
  sigla provincia, nome (fuzzy + dizionario manuale) o nome sede INPS
- Aggregazioni provinciali "italiane" (Sardegna pre/post riforma 2016)
- Proiezione della composizione regime nazionale GDP sulle 107 province
  (Plan B documentato in PROGETTO_CONTESTO.md sez. 10.14)

Tutti gli step seguono i pattern di macrorefine: immutabilità del Dataset,
StepRecord con params + metrics, History come audit trail (poi convertibile
in PROV-O minimale).
"""
from macrorefine.steps.lod.aggregate import (
    AggregateMEFRedditiByProvincia,
    AggregateSardiniaProvinces,
    UnpivotINPSPensioniVigenti,
    UnpivotINPSRegimeSede,
    UnpivotINPSSerieStorica,
)
from macrorefine.steps.lod.emit import EmitQbObservations
from macrorefine.steps.lod.enrich import EnrichWithStaticMapping
from macrorefine.steps.lod.estimate import EstimateAnnualAmount
from macrorefine.steps.lod.link import (
    LinkProvinceToAGID_byName,
    LinkProvinceToAGID_byNUTS,
    LinkProvinceToAGID_bySigla,
    LinkSedeINPS,
)
from macrorefine.steps.lod.parse import ParseItalianNumbers
from macrorefine.steps.lod.project import ProjectGDPRegimeComposition

__all__ = [
    "ParseItalianNumbers",
    "EstimateAnnualAmount",
    "LinkProvinceToAGID_byNUTS",
    "LinkProvinceToAGID_bySigla",
    "LinkProvinceToAGID_byName",
    "LinkSedeINPS",
    "AggregateSardiniaProvinces",
    "AggregateMEFRedditiByProvincia",
    "UnpivotINPSPensioniVigenti",
    "UnpivotINPSRegimeSede",
    "UnpivotINPSSerieStorica",
    "ProjectGDPRegimeComposition",
    "EmitQbObservations",
    "EnrichWithStaticMapping",
]
