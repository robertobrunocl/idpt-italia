"""idpt_vocab.py — Costanti URI del namespace idpt: per le Recipe del progetto.

Centralizza tutte le URI usate nelle Recipe (cubi, DSD, dimensioni, misure,
code-list, istanze code-list) per evitare typo. Coerente con la modellazione
formale documentata in PROGETTO_CONTESTO.md sez. 10.10–10.12 e con i TTL di
vocabolario in ``output/vocabularies/``.

Pattern: ogni costante è una stringa URI completa. Le Recipe importano questo
modulo come ``import idpt_vocab as V`` e usano ``V.CUBE_OCCUPATI_ISTAT`` ecc.

Namespace ``idpt:`` placeholder. Sarà sostituito con
``https://robertobrunocl.github.io/idpt-italia/`` al deploy GitHub Pages (decisione
δ+β del Blocco B di check-point ontologico, sez. 4 di PROGETTO_CONTESTO.md).
"""
from __future__ import annotations

# =============================================================================
# Namespace
# =============================================================================

IDPT_NS = "https://robertobrunocl.github.io/idpt-italia/"
AGIDP_NS = (
    "https://w3id.org/italia/controlled-vocabulary/"
    "territorial-classifications/provinces/"
)
NUTS_NS = "http://nuts.geovocab.org/id/"

# SDMX-RDF (W3C Data Cube companion)
SDMX_ATTRIBUTE_NS = "http://purl.org/linked-data/sdmx/2009/attribute#"
SDMX_CODE_NS      = "http://purl.org/linked-data/sdmx/2009/code#"
SDMX_CONCEPT_NS   = "http://purl.org/linked-data/sdmx/2009/concept#"

SDMX_ATTR_OBS_STATUS  = SDMX_ATTRIBUTE_NS + "obsStatus"
SDMX_ATTR_UNIT_MEASURE = SDMX_ATTRIBUTE_NS + "unitMeasure"
SDMX_CODE_OBS_STATUS_A = SDMX_CODE_NS + "obsStatus-A"
SDMX_CODE_OBS_STATUS_E = SDMX_CODE_NS + "obsStatus-E"
SDMX_CODE_OBS_STATUS_P = SDMX_CODE_NS + "obsStatus-P"
SDMX_CODE_OBS_STATUS_M = SDMX_CODE_NS + "obsStatus-M"


# =============================================================================
# Cubi qb:DataSet (9)
# =============================================================================

CUBE_PENSIONI_VIGENTI_RESIDENZA = IDPT_NS + "cubo-pensioni-vigenti-residenza"
CUBE_PENSIONI_REGIME_SEDE       = IDPT_NS + "cubo-pensioni-regime-sede"
CUBE_PENSIONI_SERIE_STORICA_SEDE = IDPT_NS + "cubo-pensioni-serie-storica-sede"
CUBE_PENSIONI_DECORRENZA_GDP    = IDPT_NS + "cubo-pensioni-decorrenza-gdp"
CUBE_OCCUPATI_ISTAT             = IDPT_NS + "cubo-occupati-istat"
CUBE_INDICATORI_DEMOGRAFICI_ISTAT = IDPT_NS + "cubo-indicatori-demografici-istat"
CUBE_REDDITI_MEF                = IDPT_NS + "cubo-redditi-mef"
CUBE_IDPT_COMPUTED              = IDPT_NS + "cubo-idpt-computed"
CUBE_PLAN_B_GDP_PROJECTED       = IDPT_NS + "cubo-plan-b-gdp-projected"


# =============================================================================
# DataStructureDefinition (9)
# =============================================================================

DSD_PENSIONI_VIGENTI_RESIDENZA = IDPT_NS + "dsd-pensioni-vigenti-residenza"
DSD_PENSIONI_REGIME_SEDE       = IDPT_NS + "dsd-pensioni-regime-sede"
DSD_PENSIONI_SERIE_STORICA_SEDE = IDPT_NS + "dsd-pensioni-serie-storica-sede"
DSD_PENSIONI_DECORRENZA_GDP    = IDPT_NS + "dsd-pensioni-decorrenza-gdp"
DSD_OCCUPATI_ISTAT             = IDPT_NS + "dsd-occupati-istat"
DSD_INDICATORI_DEMOGRAFICI_ISTAT = IDPT_NS + "dsd-indicatori-demografici-istat"
DSD_REDDITI_MEF                = IDPT_NS + "dsd-redditi-mef"
DSD_IDPT_COMPUTED              = IDPT_NS + "dsd-idpt-computed"
DSD_PLAN_B_GDP_PROJECTED       = IDPT_NS + "dsd-plan-b-gdp-projected"


# =============================================================================
# Dimension properties (10)
# =============================================================================

PROVINCIA               = IDPT_NS + "provincia"
SEDE_INPS               = IDPT_NS + "sedeINPS"
AREA_GEOGRAFICA         = IDPT_NS + "areaGeografica"
ANNO_RIFERIMENTO        = IDPT_NS + "annoRiferimento"
ANNO_DECORRENZA         = IDPT_NS + "annoDecorrenza"
TIPO_GESTIONE           = IDPT_NS + "tipoGestione"
REGIME_LIQUIDAZIONE     = IDPT_NS + "regimeLiquidazione"
INDICATORE_DEMOGRAFICO  = IDPT_NS + "indicatoreDemografico"
VOCE_REDDITO            = IDPT_NS + "voceReddito"
COMPONENTE_IDPT         = IDPT_NS + "componenteIDPT"


# =============================================================================
# Measure properties (9)
# =============================================================================

NUMERO_PENSIONI            = IDPT_NS + "numeroPensioni"
IMPORTO_MEDIO_MENSILE      = IDPT_NS + "importoMedioMensile"
IMPORTO_ANNUO_COMPLESSIVO  = IDPT_NS + "importoAnnuoComplessivo"
ETA_MEDIA_DECORRENZA       = IDPT_NS + "etaMediaDecorrenza"
NUMERO_OCCUPATI            = IDPT_NS + "numeroOccupati"
VALORE_INDICATORE          = IDPT_NS + "valoreIndicatore"
FREQUENZA_DICHIARANTI      = IDPT_NS + "frequenzaDichiaranti"
AMMONTARE_TOTALE           = IDPT_NS + "ammontareTotale"
VALORE_IDPT                = IDPT_NS + "valoreIDPT"
VALORE_GREZZO_IDPT         = IDPT_NS + "valoreGrezzoIDPT"

# Attributo qb a livello DataSet (metodo di normalizzazione del cubo 8).
METODO_NORMALIZZAZIONE     = IDPT_NS + "metodoNormalizzazione"


# =============================================================================
# Code-list (6 ConceptScheme)
# =============================================================================

CS_TIPI_GESTIONE_INPS       = IDPT_NS + "tipi-gestione-inps"
CS_REGIMI_LIQUIDAZIONE      = IDPT_NS + "regimi-liquidazione"
CS_INDICATORI_DEMOGRAFICI   = IDPT_NS + "indicatori-demografici"
CS_VOCI_REDDITO_MEF         = IDPT_NS + "voci-reddito-mef"
CS_COMPONENTI_IDPT          = IDPT_NS + "componenti-idpt"
CS_AREE_GEOGRAFICHE         = IDPT_NS + "aree-geografiche"


# =============================================================================
# Istanze code-list più usate (le altre via lookup notation→URI nelle Recipe)
# =============================================================================

# Aree geografiche
AREA_ITALIA = IDPT_NS + "area-italia"

# Tipi gestione INPS
GESTIONE_PRIVATI            = IDPT_NS + "gestione-privati"
GESTIONE_PUBBLICI           = IDPT_NS + "gestione-pubblici"
GESTIONE_AUTONOMI_PARASUB   = IDPT_NS + "gestione-autonomi-parasub"
GESTIONE_ASSISTENZIALI      = IDPT_NS + "gestione-assistenziali"
GESTIONE_TOTALE             = IDPT_NS + "gestione-totale"

# Regimi liquidazione
REGIME_RETRIBUTIVO          = IDPT_NS + "regime-retributivo"
REGIME_MISTO_DINI           = IDPT_NS + "regime-misto-dini"
REGIME_MISTO_FORNERO        = IDPT_NS + "regime-misto-fornero"
REGIME_CONTRIBUTIVO_PURO    = IDPT_NS + "regime-contributivo-puro"

# Componenti IDPT
COMP_PRESSIONE_DEMOGRAFICA  = IDPT_NS + "componente-pressione-demografica"
COMP_PESO_ECONOMICO         = IDPT_NS + "componente-peso-economico"
COMP_EREDITA_STORICA        = IDPT_NS + "componente-eredita-storica"
IDPT_AGGREGATO              = IDPT_NS + "idpt-aggregato"


# =============================================================================
# Pattern URI per le observation (template f-string compatibili)
# =============================================================================

# Cubo 1 — pensioni-vigenti-residenza: provincia × gestione × anno
PATTERN_OBS_VIGENTI = IDPT_NS + "obs-vigenti-{codice_istat}-{anno}-{gestione_short}"
# Cubo 2 — pensioni-regime-sede: sede × gestione × regime × anno × measureType
PATTERN_OBS_REGIME  = IDPT_NS + "obs-regime-{sede_slug}-{anno}-{gestione_short}-{regime_short}-{measure_short}"
# Cubo 3 — pensioni-serie-storica-sede: sede × gestione × anno × measureType
PATTERN_OBS_STORICA = IDPT_NS + "obs-storica-{sede_slug}-{anno}-{gestione_short}-{measure_short}"
# Cubo 4 — decorrenza-gdp: area × anno-decorrenza
PATTERN_OBS_DECORRENZA = IDPT_NS + "obs-decorrenza-{area_short}-{anno_decorrenza}"
# Cubo 5 — occupati-istat: provincia × anno
PATTERN_OBS_OCCUPATI = IDPT_NS + "obs-occupati-{codice_istat}-{anno}"
# Cubo 6 — indicatori-demografici: provincia × indicatore × anno
PATTERN_OBS_INDICATORI = IDPT_NS + "obs-indicatori-{codice_istat}-{indicatore_short}-{anno}"
# Cubo 7 — redditi-mef: provincia × voce × anno
PATTERN_OBS_REDDITI = IDPT_NS + "obs-redditi-{codice_istat}-{voce_short}-{anno}"
# Cubo 8 — idpt-computed: provincia × componente × anno
PATTERN_OBS_IDPT = IDPT_NS + "obs-idpt-{codice_istat}-{componente_short}-{anno}"
# Cubo 9 — plan-b-gdp-projected: provincia × regime × anno
PATTERN_OBS_PLAN_B = IDPT_NS + "obs-plan-b-{codice_istat}-{regime_short}-{anno}"


# =============================================================================
# Licenze (più frequenti)
# =============================================================================

LICENSE_CC_BY_4_0 = "https://creativecommons.org/licenses/by/4.0/"
LICENSE_CC_BY_3_0_IT = "https://creativecommons.org/licenses/by/3.0/it/"
LICENSE_IODL_2_0 = "https://www.dati.gov.it/iodl/2.0/"
