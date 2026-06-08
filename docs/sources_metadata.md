# Metadati delle fonti del progetto IDPT

> Scratchpad di lavoro per la **Sezione 2** del report.
> Centralizza per ogni fonte: URL canonico, parametri di estrazione (per i
> cubi OLAP INPS e i databrowser ISTAT), licenza ufficiale verificata, ruolo
> nel grafo IDPT e ruolo narrativo. Tutte le licenze sono state verificate
> tramite portale ufficiale o, per AGID, leggendo le triple `dct:license` nei
> TTL forniti.

---

## A. Dataset statistici primari (9 CSV)

### A.1 INPS — 5 dataset

Tutti i dataset INPS sono estratti dall'**Osservatorio statistico** dell'Istituto, area "Pensioni vigenti / Pensioni per anno di decorrenza". L'interfaccia è un **cubo OLAP JavaScript client-side** che richiede l'impostazione manuale di filtri, dimensioni di riga/colonna e statistiche prima di esportare il CSV. Non esiste un URL diretto al CSV: l'URL del cubo OLAP è il punto di accesso, i parametri di estrazione devono essere annotati per garantire riproducibilità.

**Licenza comune a tutti i 5 dataset INPS**: `IODL 2.0` — Italian Open Data Licence v2.0
URL canonico licenza: <https://www.dati.gov.it/iodl/2.0/>
Attribuzione richiesta: "Fonte: INPS — Osservatorio statistico".

---

**[1] `inps_pensioni_vigenti_provincia_2026_v1.csv`**

- **URL cubo OLAP**: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/377>
- **Filtri applicati**:
  - Anno = 2026
  - Tipo gestione = `Pensioni ai lavoratori dipendenti privati` + `Pensioni ai lavoratori dipendenti pubblici` + `Pensioni ai lavoratori autonomi e parasubordinati` + `Prestazioni assistenziali`
- **Layout cubo**:
  - Righe: `Provincia di residenza` (110 entità)
  - Colonne: `Tipo di gestione` (4 gestioni)
  - Statistiche: `Numero pensioni (SUM)`, `Importo medio mensile`, `Importo complessivo annuo (in milioni di euro) (SUM)`
- **Cosa NON è stato selezionato**: `Cumulo`, `Assicurazioni facoltative`, `Convenzioni internazionali` — voci marginali o doppi conteggi, escluse per coerenza con il perimetro IDPT (vedi sez. 4 di `PROGETTO_CONTESTO.md`). Inoltre la dimensione "Tipo di prestazione" non è disponibile a questa granularità per motivi di privacy statistica del cubo OLAP INPS.
- **Composizione**: 110 entità territoriali (107 province attuali + 2 PA Trentino-AA + 3 ex-province sarde da aggregare) × 4 gestioni × 3 misure + 7 aggregati continentali per pensioni all'estero + 1 riga "Totale".
- **Totale verificato**: 20.925.413 pensioni, ~344 mld € di importo annuo.
- **Anomalie**: numeri in formato italiano (`9.999,9`); celle `-` per privacy/non applicabilità; nomi province in MAIUSCOLO con varianti tipografiche (`MASSA CARRARA` senza trattino, `PESARO -URBINO` con spazio prima del trattino, `FORLI'-CESENA` con apostrofo dattilografico).
- **Ruolo nell'IDPT**: numeratore di **D1** (pensionati per provincia) + numeratore di **D2** (monte pensioni per provincia); base del **cubo 1** del grafo + input quota provinciale per il Plan B GDP (cubo 9).
- **Ruolo narrativo**: dataset principale del progetto, dà lo snapshot 1.1.2026 della spesa pensionistica per residenza.
- **Licenza**: IODL 2.0.

---

**[2] `inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv`**

- **URL cubo OLAP**: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/389>
- **Filtri applicati**: Anno = 2026 (nessun filtro su gestione: il cubo per regime *non* include i pubblici per costruzione)
- **Layout cubo**:
  - Righe: `Provincia sede INPS` (106 sedi)
  - Colonne: `Regime di liquidazione` (4 valori: Retributivo / Misto riforma Dini / Misto riforma Fornero / Contributivo puro)
  - Statistiche: `Numero pensioni (SUM)`, `Importo medio mensile`
- **Limite di privacy noto**: la statistica `Importo complessivo annuo (in milioni di euro)` è **soppressa** dal cubo OLAP alla cross-tab provincia × regime per motivi di privacy. Verrà ricostruita nella pipeline come stima `n × media × 13` (vedi sez. 3).
- **Composizione**: 106 sedi INPS × 4 regimi × 2 misure. Asse territoriale diverso dal dataset [1]: non è "provincia di residenza" ma "provincia della sede INPS" — verrà documentato nel grafo con la classe `idpt:SedeINPS`.
- **Copertura**: 12.873.198 pensioni = 96% del comparto Privati + Autonomi/Parasub (il cubo regime esclude i Pubblici per costruzione e i 4,42 mln di Assistenziali per natura non disaggregabili).
- **Anomalie**: tutto MAIUSCOLO, etichette regime senza spazi (`MistoriformaDini`), aggregazioni di sede diverse dalla residenza (`CAGLIARI E SUD SARDEGNA` aggregata, `FORLI` senza Cesena, `VERBANIA` = Verbano-Cusio-Ossola).
- **Ruolo nell'IDPT**: dimensione **D3** (eredità storica) per Privati + Autonomi/Parasub; base del **cubo 2**.
- **Ruolo narrativo**: cattura la stratificazione delle riforme previdenziali (Dini 1995, Fornero 2011) sul tessuto territoriale.
- **Licenza**: IODL 2.0.

---

**[3] `inps_pensioni_vigenti_serie_storica_provincia_1998_2026_v1.csv`**

- **URL cubo OLAP**: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/390>
- **Filtri applicati**: Tipo gestione = `Pensioni ai lavoratori dipendenti privati` + `Pensioni ai lavoratori dipendenti pubblici` + `Pensioni ai lavoratori autonomi e parasubordinati` + `Prestazioni assistenziali` (stessa selezione del dataset [1] per garantire confrontabilità diacronica).
- **Layout cubo**:
  - Righe: `Provincia della sede INPS` (106 sedi)
  - Colonne: `Anno` (29 valori, 1998–2026)
  - Statistiche: `Numero pensioni (SUM)`, `Importo medio mensile`
- **Limite del cubo**: l'importo complessivo annuo non è disponibile in nessuna configurazione del cubo per la serie storica → ricostruito come stima `n × media × 13` con `obsStatus=E` nella pipeline (vedi cubo 3 nella sez. 4 del report).
- **Composizione**: 106 sedi × 29 anni × 2 misure = ~6.150 osservazioni reali.
- **Anomalie temporali**:
  - BAT, Fermo, Monza-Brianza: celle `-` per 1998–2008 (province istituite nel 2009).
  - Sedi INPS sarde: aggregazione implicita post-2012 (Sassari assorbe Olbia-Tempio, Nuoro assorbe Ogliastra, Cagliari-e-Sud-Sardegna assorbe Carbonia-Iglesias + Medio Campidano). Salto numerico evidente nel CSV.
- **Verifica numerica**: totale 2026 della serie storica = 20.925.421, coincidente al 99,99996% col dataset [1].
- **Ruolo nell'IDPT**: base del **cubo 3**, prospettiva diacronica della spesa pensionistica (1998 → 2026, +37% in 28 anni). Non entra nel calcolo dell'IDPT snapshot, ma fornisce contesto narrativo.
- **Licenza**: IODL 2.0.

---

**[4] `inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv`** *(input definitivo del Plan B GDP)*

- **URL cubo OLAP**: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/388>
- **Filtri applicati**:
  - Anno = 2026
  - Tipo gestione = `Pensioni ai lavoratori dipendenti pubblici`
- **Layout cubo**:
  - Righe: `Anno di decorrenza`
  - Colonne: (nessuna)
  - Statistiche: `Numero pensioni (SUM)`, `Età media alla decorrenza`, `Importo medio mensile`, `Importo medio mensile alla decorrenza`
- **Limite strutturale**: il cubo OLAP per anno di decorrenza **non espone la dimensione "Provincia"** per costruzione. La composizione GDP × regime non è disponibile a granularità provincia × regime in nessun formato aperto INPS — origine del **Plan B** (vedi sez. 3 e sez. 4 del report).
- **Composizione**: dataset nazionale, ~46 righe (decorrenze da "anteriore al 31/12/1980" al 2025) × 4 misure. Totale: 3.171.265 pensioni GDP.
- **Ruolo nell'IDPT**: input per la stima della **composizione regime GDP nazionale** via euristica anno-di-decorrenza → regime (vedi sez. 10.6 di `PROGETTO_CONTESTO.md`); proiettata sulle 107 quote provinciali GDP del dataset [1] per generare il **cubo 9** (Plan B GDP projected).
- **Licenza**: IODL 2.0.

---

**[5] `inps_pensioni_per_anno_di_decorrenza_dipendenti_pubblici_anzianità_2026_v1.csv`** *(ispezione esplorativa preliminare)*

- **URL cubo OLAP**: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/388> (stesso cubo del dataset [4])
- **Filtri applicati**:
  - Anno = 2026
  - Tipo gestione = `Pensioni ai lavoratori dipendenti pubblici`
  - **Categoria = `Vecchiaia`** (l'unico filtro che differisce dal dataset [4])
- **Layout cubo**: identico al dataset [4].
- **Composizione**: 2.355.382 pensioni di vecchiaia GDP = 74% del totale GDP del dataset [4].
- **Ruolo nel progetto**: **ispezione preliminare** che ha guidato la scelta di adottare il dataset [4] (tutte le categorie) come input definitivo per il Plan B. Il dataset [5] è conservato nella cartella `data/` come documentazione del processo metodologico, ma **non entra nel grafo finale**.
- **Da raccontare nel report**: l'aver verificato che il dataset "vecchiaia" rappresenta il 74% del GDP totale ha confermato che usare il superset (tutte le categorie) era preferibile per coerenza col cubo 1 di residenza (che a sua volta aggrega tutte le categorie GDP).
- **Licenza**: IODL 2.0.

---

### A.2 ISTAT — 3 dataset

I dataset ISTAT sono estratti dal databrowser `esploradati.istat.it`, nuova interfaccia che ha sostituito il deprecato `dati.istat.it`. L'export è in formato **SDMX-like** (header con codici standard `FREQ` / `REF_AREA` / `SEX` / `AGE` / `TIME_PERIOD` / `OBS_STATUS` / `OBS_VALUE` + label paralleli IT; separatore `,`, decimali col punto, codifica UTF-8 con BOM, **quoting CSV non standard `quotechar="'"`** per gestire gli apostrofi nei nomi). REF_AREA contiene direttamente il codice NUTS → linking diretto al vocabolario AGID via `owl:sameAs`.

**Licenza comune a tutti i 3 dataset ISTAT**: `CC-BY 3.0 IT` — Creative Commons Attribuzione 3.0 Italia
URL canonico licenza: <https://creativecommons.org/licenses/by/3.0/it/>
Note legali ISTAT: <https://www.istat.it/note-legali/>

---

**[6] `istat_occupati_provincia_2025_v1.csv`**

- **URL databrowser**: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500LAB,1.0/LAB_OFFER/LAB_OFF_EMPLOY/DCCV_OCCUPATIT1/DCCV_OCCUPATIT1_PROVDATA/IT1,150_938_DF_DCCV_OCCUPATIT1_21,1.0>
- **Tema**: Lavoro e retribuzioni → Offerta di lavoro → Occupazione → Occupati
- **Filtri applicati**: ultimo anno disponibile (2025, media annua), solo province (escluse aree geografiche aggregate), aggregato per sesso ("totale").
- **Composizione**: 107 entità (105 province standard NUTS-3 + 2 PA Trento e Bolzano in NUTS-2 `ITD1`/`ITD2`).
- **Misura**: occupati totali 15–89 anni in migliaia.
- **Allineamento temporale**: media annua 2025 vs snapshot INPS 1.1.2026 → disallineamento di pochi mesi, dichiarato come limite minore.
- **Asimmetria NUTS-2/NUTS-3 per le PA**: gestita con sidecar `nuts_aliases.ttl` (`ITD1`↔`ITD10`, `ITD2`↔`ITD20` via `owl:sameAs`).
- **Fake-NUTS proprietari ISTAT**: il CSV usa `IT108`/`IT109`/`IT110`/`IT111` per le 4 province senza NUTS-3 Eurostat (Monza-Brianza, Fermo, BAT, Sud Sardegna) → modellati con `skos:exactMatch` nello stesso sidecar.
- **Ruolo nell'IDPT**: denominatore di **D1** (occupati per provincia); base del **cubo 5**.
- **Ruolo narrativo**: il rapporto pensionati/occupati materializza la pressione demografica previdenziale.
- **Licenza**: CC-BY 3.0 IT.

---

**[7] `istat_indicatori_demografici_provincia_2026_v1.csv`**

- **URL databrowser**: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,POP,1.0/POP_POPULATION/DCIS_INDDEMOG1/IT1,22_293_DF_DCIS_INDDEMOG1_1,1.0>
- **Tema**: Popolazione e famiglie → Indicatori demografici (rilevazione anagrafica).
- **Filtri applicati**: anno di riferimento 1.1.2026 (dato stimato preliminare; il definitivo esce mesi dopo). Allineamento temporale **perfetto** con la snapshot INPS.
- **Composizione**: 107 entità complete, con PA Trento (`ITD20`) e Bolzano (`ITD10`) in **NUTS-3 corretto** — diversamente dal cubo occupati. Stesso ente, due cubi, due codifiche territoriali per le PA: scoperta documentabile nel report come esempio di disomogeneità interna ai rilasci LOD ISTAT.
- **Indicatori inclusi (6)**: `POP014` (0–14 anni, %), `POP1564` (15–64, %), `POP65OVER` (65+, %), `OLDAGEDEPR` (dipendenza anziani), `AGEINDEX` (indice vecchiaia), `MEANAGEP` (età media).
- **Ruolo nell'IDPT**: nessuna componente entra direttamente nel calcolo; **variabili di contesto** per la narrativa territoriale del grafo (cubo 6).
- **Licenza**: CC-BY 3.0 IT.

---

**[8] `istat_natalita_speranza_di_vita_2025_v1.csv`**

- **URL databrowser**: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,POP,1.0/POP_POPULATION/DCIS_INDDEMOG1/IT1,22_293_DF_DCIS_INDDEMOG1_1,1.0> (stesso cubo del dataset [7])
- **Filtri applicati**: stesso cubo "Indicatori demografici" ma con riferimento **2025** invece che 2026, per i 2 indicatori che richiedono un anno solare chiuso e quindi non disponibili al 1.1.2026.
- **Composizione**: 107 entità, 2 indicatori.
- **Indicatori inclusi**: `BIRTHRATE` (tasso di natalità per mille, dato provvisorio), `LIFEEXP65T` (speranza di vita a 65 anni, dato stimato).
- **Disallineamento temporale**: indicatori al 2025 vs altri ISTAT al 1.1.2026. Ininfluente perché variabili di contesto.
- **Ruolo narrativo**: `LIFEEXP65T` utile per parlare di "durata" delle pensioni con gradiente Nord/Sud (es. Bolzano 22,2 anni vs probabile <20 anni al Sud).
- **Confluisce nel cubo 6** insieme al dataset [7] (unificazione decisa al check-point ontologico).
- **Licenza**: CC-BY 3.0 IT.

---

### A.3 MEF — 1 dataset CSV (+ 1 RDF di facciata come case study)

**[9] `mef_redditi_irpef_comune_2024_v1.csv`** *(+ accanto `mef_redditi_irpef_comune_2024_v1.rdf` come case study negativo)*

- **URL diretto del CSV (ZIP)**: <https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800>
- **URL pagina indice dataset**: <https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?search_class%5b0%5d=cCOMUNE&opendata=yes>
- **Pagina ufficiale "Open data comunale IRPEF"** (descrizione e licenza): <https://www.finanze.gov.it/it/statistiche-fiscali/open-data-comunale-principali-variabili-irpef/>
- **Tema**: dichiarazioni IRPEF per comune, anno di imposta 2024 (redditi prodotti 2023, dichiarati 2024).
- **Composizione**: 7.897 comuni × 53 colonne (per ogni voce di reddito, doppia colonna "Frequenza" + "Ammontare in euro").
- **Variabili utilizzate per il grafo IDPT** (5): `v2` Reddito da lavoro dipendente, `v4` Reddito da lavoro autonomo, `v5` Reddito imprenditore contabilità ordinaria, `v6` Reddito imprenditore contabilità semplificata, `v7` Reddito da partecipazione — componenti del **monte redditi da lavoro** (denominatore di **D2**).
- **Bonus per validazione cross-fonte**: `v3` Reddito da pensione → triangolazione col dataset [1] INPS.
- **Anomalie**:
  - **NA-bug pandas**: 92 comuni di Napoli con `Sigla="NA"` interpretati come `NaN` da default pandas → fix con `keep_default_na=False`.
  - 1 riga sentinella con `Codice Istat=0`, `Sigla=0`, `Regione=Mancante/errata` (placeholder MEF per dichiarazioni con territorio non assegnato) → da filtrare prima dell'aggregazione.
- **Disallineamento temporale**: redditi 2024 vs pensioni 1.1.2026 (~3 anni) → limite dichiarato nel report.
- **Ruolo nell'IDPT**: aggregazione per provincia di `v2 + v4 + v5 + v6 + v7` = denominatore D2; base del **cubo 7**.
- **Licenza**: `CC-BY 3.0` (generica, *non* la versione "Italia") — dichiarata sulla pagina "Open data comunale" del MEF: *"I dati sono rilasciati con licenza Creative Commons 3.0 e distribuiti utilizzando le tecnologie digitali correnti e gli standard Web più diffusi"*.
- **URL canonico licenza**: <https://creativecommons.org/licenses/by/3.0/>

**Sidecar RDF (case study negativo)**: lo stesso MEF pubblica anche `mef_redditi_irpef_comune_2024_v1.rdf` accanto al CSV. È un "RDF di facciata" (vedi sez. 9 di `PROGETTO_CONTESTO.md` e sez. dedicata del report): namespace `http://www1.finanze.gov.it/fakeurl#`, variabili `v1..v22` senza URI semantiche, modellazione "wide" senza `qb:Observation`, data malformata `2026-23-04`. Stessa licenza CC-BY 3.0. Conservato nel progetto come oggetto di discussione, **non usato come fonte di dati**.

---

## B. Vocabolari controllati — 2 file TTL

Pubblicati nel repository ufficiale AgID `italia/dati-semantic-assets` su GitHub, deserializzati nel TTL come istanze `dcatapit:Dataset` complete di metadati e licenza esplicita.

**Licenza comune ai 2 vocabolari**: `CC-BY 4.0` — Creative Commons Attribuzione 4.0 Internazionale
URL canonico licenza (vocabolario AGID): <https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40>
Verificato direttamente: presenza di triple `dct:license <https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40>` nei file TTL.

---

**[10] `data/provinces.ttl` — Vocabolario Controllato Province d'Italia**

- **URL download raw**: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/provinces/provinces.ttl>
- **URL canonico del vocabolario**: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces>
- **Contenuto per provincia**: URI canonica, `skos:prefLabel` IT/EN, `skos:notation` (codice ISTAT a 3 cifre), `clv:acronym` (sigla auto), `owl:sameAs` verso codice NUTS (eventualmente multipli per province con NUTS storici), `clv:situatedWithin` (regione di appartenenza), `clv:hasRankOrder` (3 per ordinaria, 4 per metropolitana).
- **Dimensioni**: ~2.712 triple totali, 107 province + 116 link `owl:sameAs` verso NUTS (9 NUTS storici extra per le province polinominate).
- **Ruolo nel grafo IDPT**: **ancora semantica** territoriale — riuso integrale delle URI canoniche AGID per tutte le 107 province; il pattern OntoPiA porta multi-typing gratuito (`clv:Province` + `clv:AdminUnitComponent` + `skos:Concept` + `clv:Feature`).
- **Licenza**: CC-BY 4.0.

---

**[11] `data/regions.ttl` — Vocabolario Controllato Regioni d'Italia**

- **URL download raw**: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/regions/regions.ttl>
- **URL canonico del vocabolario**: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/regions>
- **Dimensioni**: ~477 triple, 20 regioni.
- **Ruolo nel grafo IDPT**: ancora di livello superiore per le query di aggregazione regionale (es. q10 "% regime retributivo per regione").
- **Licenza**: CC-BY 4.0.

---

## C. Geometrie per la visualizzazione (1 file GeoJSON)

**[12] `data/limits_IT_provinces.geojson`**

- **URL download diretto**: <https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson>
- **Repository**: <https://github.com/openpolis/geojson-italy>
- **Origine**: geometrie ufficiali ISTAT dei confini provinciali, ridistribuite da Openpolis in formato GeoJSON (WGS84).
- **Ruolo nel progetto**: layer cartografico per le mappe coropletiche Folium (`output/visualizations/idpt_map.html` e `idpt_components.html`). Il match province IDPT ↔ poligoni avviene sul campo `codice_istat`.
- **Ruolo nel grafo RDF**: nessuno — file di puro rendering, non entra fra le triple. Da menzionare nella sez. 5 del report come dipendenza visualizzativa.
- **Licenza**: **CC-BY** — derivata dalla licenza ISTAT originale dei confini amministrativi, mantenuta da Openpolis sui propri file. Attribuzione richiesta: ISTAT + Openpolis.

---

## D. Linking esterno verso il LOD Cloud (1 sidecar generato)

**[13] `output/mappings/agid_to_dbpedia.ttl` — 107 `owl:sameAs` AGID → DBpedia**

- **Origine target**: <https://dbpedia.org/sparql>
- **Procedura**: query SPARQL su DBpedia per province italiane + match esatto su `prefLabel` + reconciliation manuale con 25 override (14 città metropolitane "Metropolitan City of …" + 11 anomalie nominali tipo "Reggio nell'Emilia" ↔ "Reggio Emilia"). Implementata in `scripts/generate_agid_to_dbpedia.py`.
- **Composizione**: 107 triple `owl:sameAs` (1 per provincia AGID verso 1 risorsa DBpedia).
- **Ruolo nel grafo IDPT**: realizza la **5ª stella** della scala Berners-Lee (linking esterno verso una fonte LOD globale).
- **Licenza DBpedia**: `CC-BY-SA 3.0` (dataset DBpedia ereditato da Wikipedia).
- **URL canonico licenza**: <https://creativecommons.org/licenses/by-sa/3.0/>
- **Compatibilità nel deliverable**: l'asserzione `owl:sameAs` non duplica i contenuti DBpedia ma li referenzia; non sussiste obbligo "share-alike" sulla nostra opera, che resta licenziabile CC-BY 4.0. Attribuzione DBpedia mantenuta come `dcterms:source` nel sidecar.

---

## Riepilogo licenze (per la tabella della Sezione 2)

| Fonte | Dataset | Licenza | URL canonico licenza |
|---|---|---|---|
| INPS | [1]–[5] (5 CSV pensionistici) | IODL 2.0 | <https://www.dati.gov.it/iodl/2.0/> |
| ISTAT | [6]–[8] (3 CSV occupazione + demografia) | CC-BY 3.0 IT | <https://creativecommons.org/licenses/by/3.0/it/> |
| MEF — Dip. Finanze | [9] CSV redditi IRPEF (+ RDF di facciata) | CC-BY 3.0 | <https://creativecommons.org/licenses/by/3.0/> |
| AGID — OntoPiA | [10]–[11] vocabolari TTL province + regioni | CC-BY 4.0 | <https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40> |
| Openpolis (deriv. ISTAT) | [12] GeoJSON province | CC-BY | <https://github.com/openpolis/geojson-italy> |
| DBpedia (linking) | [13] sidecar `agid_to_dbpedia.ttl` | CC-BY-SA 3.0 | <https://creativecommons.org/licenses/by-sa/3.0/> |

**Compatibilità del deliverable finale**: la scelta `CC-BY 4.0` per il grafo IDPT (decisione di sez. 4 di `PROGETTO_CONTESTO.md`) è compatibile con tutte e 5 le licenze sorgente — CC-BY 4.0 è la più ampia e si conforma agli obblighi di attribuzione comuni a tutte. L'attribuzione composita è dichiarata in `dcterms:rights` del `dcatapit:Dataset` finale.

---

*Ultima verifica: 2 giugno 2026 — licenze AGID confermate via lettura diretta dei TTL (`dct:license A21_CCBY40`), licenze INPS/ISTAT/MEF/DBpedia confermate via portale ufficiale.*
