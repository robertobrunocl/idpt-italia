# Atlante della dipendenza previdenziale italiana

**IDPT come Linked Open Data 5★**

Roberto Bruno — anno accademico 2025/2026

---

## Indice

1. **Abstract**
2. **Dataset di partenza**
   - 2.1 INPS — quattro cubi dell'Osservatorio statistico (licenza IODL 2.0)
   - 2.2 ISTAT — tre estrazioni dal databrowser `esploradati.istat.it` (licenza CC-BY 3.0 IT)
   - 2.3 MEF — un CSV affidabile (licenza CC-BY 3.0)
   - 2.4 Ancore semantiche AGID + geometrie ausiliarie (licenze CC-BY 4.0 e CC-BY)
   - 2.5 Tabella riepilogativa delle licenze
3. **Elaborazione dei dataset**
   - 3.1 macrorefine: motore e architettura della pipeline
   - 3.2 Inventario dei 13 step custom LOD-aware
   - 3.3 Le anomalie tecniche risolte
   - 3.4 Le quattro Recipe "facili" — cubi 1, 5, 6, 7
   - 3.5 Le quattro Recipe "difficili" — cubi 2, 3, 4, 9
   - 3.6 Audit trail e validazione tabellare
4. **Trasformazione dei dataset — modellazione ontologica e RDF**
   - 4.1 I nove vocabolari riusati — perché ognuno è lì
   - 4.2 Una sola classe propria: `idpt:SedeINPS`
   - 4.3 Le sei code-list SKOS proprie
   - 4.4 Le nove DSD dei cubi qb
   - 4.5 Il pattern "osservazione derivata" uniforme
   - 4.6 Interlinking — i tre sidecar TTL
   - 4.7 Il cubo 8 IDPT computed — il cuore narrativo
   - 4.8 DCAT-AP_IT del deliverable finale
   - 4.9 Il caso di studio negativo: "RDF di facciata" del MEF
5. **Visualizzazione e interrogazione**
   - 5.1 Mappe coropletiche IDPT
   - 5.2 Interrogazione via SPARQL — 12 query di demo
   - 5.3 Stack di pubblicazione
   - 5.4 Limiti e prospettive
6. **Licenza del deliverable e compatibilità con le sorgenti**

---

## 1. Abstract

### Domanda di ricerca

Il progetto risponde a una domanda di **data journalism a base semantica**: *quali territori italiani sono più dipendenti dal sistema pensionistico, e quanto è sostenibile questa dipendenza?*

La domanda è il **vettore** del lavoro, non il suo fine. Il fine è la **pratica del Linked Open Data**: portare nove dataset pubblici italiani di basso livello (CSV statistici INPS, ISTAT, MEF + vocabolari controllati AGID OntoPiA) a un grafo RDF **5★** sulla scala di Berners-Lee, con riuso massimo di vocabolari standard, ancoraggio al contesto della PA italiana e linking esterno al LOD Cloud.

### L'indice IDPT

Per rispondere alla domanda di ricerca ho costruito l'**Indice di Dipendenza Previdenziale Territoriale (IDPT)**, calcolato a livello provinciale come media aritmetica di tre componenti normalizzate in [0,1]:

- **D1 — Pressione demografica previdenziale**: numero di pensioni vigenti / numero di occupati. Misura quanto la base produttiva di un territorio sostiene la sua base assistita. *Nota terminologica*: il dato INPS conta pensioni (record amministrativi), non persone titolari; una persona può ricevere più pensioni (es. vecchiaia + reversibilità).
- **D2 — Peso economico delle pensioni**: monte pensioni € / monte redditi da lavoro €. Misura quanto pesa la spesa pensionistica sul reddito complessivo del territorio.
- **D3 — Eredità storica delle riforme**: % pensioni in regime retributivo pre-Riforma Dini 1995 sul totale. Misura il "peso del passato" delle stratificazioni normative.

Le tre componenti grezze sono **normalizzate min-max** sulle 107 province e **aggregate via media aritmetica** in un valore IDPT in [0,1]. La scelta della media aritmetica (anziché pesata) è metodologica: dichiara "le tre dimensioni contano uguale" senza introdurre pesi soggettivi, e poiché i tre componenti normalizzati sono materializzati separatamente nel grafo, un consumer SPARQL può rifare l'aggregato con pesi diversi se preferisce. La normalizzazione min-max è la trasformazione più trasparente; la sua sensibilità agli outlier (Reggio Calabria in alto, Bolzano in basso) è dichiarata fra i limiti.

### Il deliverable in cifre

| Componente | Valore |
|---|---|
| Dataset di partenza | 9 CSV + 2 vocabolari AGID |
| Pipeline | macrorefine + 13 step custom LOD-aware + 9 Recipe |
| Triple totali | ~120.000 (grafo Fuseki, incl. vocabolario AGID) |
| `qb:Observation` | 13.312 in 9 `qb:DataSet` |
| Linking esterno | 107 `owl:sameAs` AGID → DBpedia |
| Classi proprie | 1 sola (`idpt:SedeINPS`) |
| Vocabolari standard riusati | 9 (qb, SKOS, OntoPiA CLV, SDMX, OWL-Time, DCAT-AP_IT, dcterms+foaf+vcard, PROV-O, owl:sameAs) |
| Pattern "obs derivata" (4 punti) | 4.399 osservazioni stimate |
| Query SPARQL di demo | 12 |

Il deliverable è impacchettato come `dcatapit:Dataset` conforme al profilo italiano AGID di DCAT.

### Risultato sostantivo

**Divario Nord/Sud netto, di circa 20× fra estremi**:

| Top 5 (più dipendenti) | Bottom 5 (meno dipendenti) |
|---|---|
| Reggio di Calabria 0,675 | Bolzano/Bozen 0,034 |
| Taranto 0,651 | Milano 0,100 |
| Catanzaro 0,627 | Trento 0,104 |
| Oristano 0,580 | Prato 0,121 |
| Nuoro 0,552 | Padova 0,141 |

Nove province su dieci nella top sono al Sud, dove la combinazione di occupazione contenuta, demografia anziana ed eredità retributiva di funzione pubblica produce una dipendenza pensionistica nettamente più alta. In fondo le PA alpine e le metropoli del triangolo industriale.

Sul piano della pratica LOD il lavoro fa emergere **scoperte tecniche raccontabili** (NUTS storici multipli preservati come `owl:sameAs` nel TTL AGID, "fake-NUTS" proprietari ISTAT `IT108`–`IT111` modellati come `skos:exactMatch`, discrepanza esatta di 11.991 pensioni Pubblici residenti all'estero fra cubo 4 nazionale e cubo 9 provinciale) e culmina in un **case study negativo**: l'RDF pubblicato dal MEF, autoetichettato "5-star RDF format" ma di fatto un "RDF di facciata" (namespace `fakeurl`, variabili anonime `v1..v22`, modellazione wide senza `qb:Observation`, data malformata), in netto contrasto col TTL AGID delle province pubblicato dalla stessa PA italiana con cura LOD-grade.

### Metodologia

Il progetto adotta una sequenza esplicita "**ontologia prima del codice**": tutte le decisioni di modellazione (vocabolari, classi, code-list, DSD, pattern di derivazione, layout file e grafi nominati Fuseki) sono state congelate **prima** della scrittura di una singola riga di pipeline.

La validazione è strutturata su due livelli ortogonali:

- **172 unit test pytest** sugli step LOD-aware di macrorefine, per la pipeline tabellare.
- **33 check SPARQL post-emissione** (10 vocabolari + 9 cubi + 14 DCAT-AP_IT) per la conformità del grafo RDF al modello ontologico atteso.

Il deliverable — repository GitHub + grafo + landing page GitHub Pages con mappa coropletica embedded + 12 query SPARQL di demo — è riproducibile end-to-end, rilasciato sotto licenza **CC-BY 4.0** (vedi sez. 6 per il dettaglio sulla compatibilità con le licenze sorgente).

---

## 2. Dataset di partenza

L'IDPT richiede di attraversare tre ecosistemi open data italiani (INPS, ISTAT, MEF) + l'ancora del vocabolario controllato AGID OntoPiA. In totale sono stati acquisiti:

- **9 dataset statistici**: 4 cubi OLAP INPS, 3 estrazioni ISTAT, 1 CSV MEF comunale, 1 GeoJSON di geometrie provinciali.
- **2 vocabolari controllati AGID** in Turtle (province + regioni).

Per ciascuna fonte la sezione dichiara URL canonico, parametri di estrazione, licenza ufficiale, composizione e ruolo nell'IDPT.

### 2.1 INPS

Le quattro estrazioni INPS derivano tutte dall'**Osservatorio statistico** (area pensioni vigenti + decorrenza), licenza comune **IODL 2.0** ([Italian Open Data Licence v2.0](https://www.dati.gov.it/iodl/2.0/) — [INPS Open Data](https://www.inps.it/it/it/dati-e-bilanci/open-data.html)). L'INPS distribuisce questi dati come **cubi OLAP JavaScript client-side**: non esiste un URL diretto al CSV finale, l'utente imposta manualmente filtri, righe, colonne e statistiche. Per riproducibilità, i parametri di estrazione sono perciò dichiarati per ciascun dataset alla stregua di un URL canonico.

**[1] Pensioni vigenti per provincia di residenza, 2026** — file `inps_pensioni_vigenti_provincia_2026_v1.csv`. Il dataset principale del progetto. Cubo OLAP: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/377>. **Filtri impostati**: anno 2026; tipo gestione = Privati + Pubblici + Autonomi/Parasubordinati + Assistenziali (escluse `Cumulo`, `Assicurazioni facoltative`, `Convenzioni internazionali`, fuori dal perimetro IDPT). **Layout**: righe = provincia di residenza × colonne = tipo di gestione × statistiche = `Numero pensioni (SUM)` + `Importo medio mensile` + `Importo complessivo annuo (mln €)`. **Composizione**: 110 entità (107 province + 2 PA + 3 ex-province sarde da aggregare) × 4 gestioni × 3 misure, più 7 aggregati continentali per pensioni all'estero e una riga "Totale". Totale verificato: **20.925.413 pensioni**, ~344 mld €/anno. **Anomalie**: numeri in formato italiano (`9.999,9`), celle `-` per privacy, nomi province in MAIUSCOLO con varianti tipografiche (`MASSA CARRARA` senza trattino, `PESARO -URBINO` con spazio, `FORLI'-CESENA` con apostrofo). Risoluzione nella sez. 3. **Ruolo nell'IDPT**: numeratore D1 (numero di pensioni vigenti) + numeratore D2 (monte pensioni); alimenta il **cubo 1** del grafo e fornisce la quota provinciale GDP che il Plan B proietta sulla composizione regime nazionale (cubo 9).

**[2] Pensioni vigenti per regime di liquidazione e sede INPS, 2026** — file `inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv`. Cubo OLAP: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/389>. **Filtri impostati**: anno 2026 (nessun filtro su gestione: il cubo per regime esclude i Pubblici per costruzione). **Layout**: righe = provincia sede INPS × colonne = regime di liquidazione × statistiche = `Numero pensioni (SUM)` + `Importo medio mensile`. La misura `Importo complessivo annuo` è **soppressa per privacy** alla cross-tab provincia × regime; viene ricostruita come stima `n × importo_medio × 13` con `obsStatus=E` + `prov:wasDerivedFrom` (sez. 3 e 4.5). **Composizione**: 106 sedi territoriali (asse diverso dalla "residenza" del dataset [1]: `CAGLIARI E SUD SARDEGNA` aggregata, `FORLI` senza Cesena, `VERBANIA` come Verbano-Cusio-Ossola) × 4 regimi (Retributivo, Misto Dini, Misto Fornero, Contributivo puro) × 2 misure. Copertura: 12.873.198 pensioni = 96% del segmento Privati + Autonomi/Parasub del dataset [1]. Restano fuori i Pubblici (oggetto del Plan B) e gli Assistenziali (non disaggregabili per regime). **Anomalie**: come dataset [1] in MAIUSCOLO, più etichette regime senza spazi (`MistoriformaDini`, `Contributivopuro`). **Ruolo nell'IDPT**: dimensione D3 (eredità storica) per il segmento Privati + Autonomi/Parasub; alimenta il **cubo 2**.

**[3] Pensioni vigenti per sede INPS, serie storica 1998–2026** — file `inps_pensioni_vigenti_serie_storica_provincia_1998_2026_v1.csv`. Cubo OLAP: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/390>. **Filtri impostati**: stesse 4 gestioni del dataset [1], per confrontabilità diacronica. **Layout**: righe = provincia della sede INPS × colonne = anno (29 valori, 1998–2026) × statistiche = `Numero pensioni (SUM)` + `Importo medio mensile`. L'importo complessivo annuo non è disponibile: ricostruito come stima `n × importo_medio × 13` su 6.150 osservazioni. **Composizione**: 106 sedi INPS (asse identico al dataset [2], non al [1]). **Anomalie temporali**: celle `-` per BAT, Fermo, Monza-Brianza negli anni 1998–2008 (province istituite nel 2009); salto numerico per le sedi sarde dopo il 2011 (aggregazione retroattiva di Olbia-Tempio, Ogliastra, Carbonia-Iglesias, Medio Campidano sulle sedi attuali). Verifica coerenza: somma 2026 = 20.925.421 pensioni, coincide al 99,99996% col dataset [1]. **Ruolo nell'IDPT**: alimenta il **cubo 3**; non entra nell'IDPT snapshot 2026 ma fornisce la prospettiva diacronica (crescita 15,2 → 20,9 mln pensioni in 28 anni, +37%).

**[4] Pensioni Dipendenti Pubblici per anno di decorrenza, 2026** — file `inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv`. Cubo OLAP: <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/388>. **Filtri impostati**: anno 2026; tipo gestione = `Pensioni ai lavoratori dipendenti pubblici`. **Layout**: righe = anno di decorrenza × statistiche = `Numero pensioni (SUM)` + `Età media alla decorrenza` + `Importo medio mensile` (+ alla decorrenza). **Limite strutturale**: la dimensione "Provincia" non è disponibile per costruzione su questo cubo; nessun rilascio INPS espone la composizione GDP × regime × provincia in formato aperto. Il progetto risolve il vuoto con il **Plan B**: stima la composizione regime GDP nazionale via euristica anno-di-decorrenza → regime (calibrata sulle riforme Dini 1995 e Fornero 2011) e la proietta sulle 107 quote provinciali GDP del dataset [1]. **Composizione**: dataset nazionale, 46 righe (decorrenze da "anteriore al 31/12/1980" al 2025), 4 misure. Totale verificato: **3.171.265 pensioni GDP**. **Ruolo nell'IDPT**: input del **cubo 4** (decorrenza GDP nazionale) e, tramite l'euristica, del **cubo 9** (Plan B GDP proiettato per provincia × regime).

#### Asimmetria territoriale fra i quattro cubi INPS — limite accettato

I quattro dataset INPS non hanno tutti lo stesso asse territoriale:

- Dataset [1] usa **provincia di residenza del titolare** (110 entità: 107 province + 2 PA + 3 ex-province sarde).
- Dataset [2] e [3] usano **provincia della sede INPS** che gestisce la pratica (106 entità con aggregazioni diverse: `CAGLIARI E SUD SARDEGNA` accorpa due province AGID, `FORLI` copre Forlì+Cesena ma è etichettata solo "Forlì", `VERBANIA` = Verbano-Cusio-Ossola).
- Dataset [4] è nazionale, non pone il problema.

I due assi misurano fenomeni semanticamente diversi ("dove vive chi riceve la pensione" vs "quale ufficio INPS la eroga") e non sono ricavabili l'uno dall'altro: l'INPS non pubblica la tabella di transito dei singoli titolari. **Accettiamo l'asimmetria come limite dichiarato**: la composizione regime × sede del cubo 2 viene attribuita alle province AGID corrispondenti — approssimazione ragionevole perché la maggioranza dei pensionati riceve la pensione tramite la sede della propria provincia di residenza, ma l'imperfezione esiste.

Conseguenza per la modellazione semantica: nella sez. 4 introdurremo una **classe propria `idpt:SedeINPS`** distinta dalle 107 `clv:Province` AGID, con due ObjectProperty (`correspondsToProvinceAGID` per il caso 1-a-1 e `aggregatesProvince` per il caso 1-a-N di Cagliari + Sud Sardegna). Preservare i due assi come entità semantiche distinte è più onesto che appiattire la sede sulla residenza, e l'asimmetria diventa interrogabile via SPARQL.

### 2.2 ISTAT

Le tre estrazioni ISTAT vengono dal databrowser `esploradati.istat.it`, sotto licenza **CC-BY 3.0 IT** ([CC-BY 3.0 IT](https://creativecommons.org/licenses/by/3.0/it/), [note legali ISTAT](https://www.istat.it/note-legali/)). Tutti gli export usano il formato SDMX-like con quoting CSV non standard `quotechar="'"` (richiede gestione esplicita nella pipeline).

Curiosità importante per il framing LOD: **lo stesso ente adotta in due cubi diversi due codifiche territoriali per le PA di Trento e Bolzano**. Il cubo Forze di Lavoro (dataset [5]) usa NUTS-2 `ITD1`/`ITD2`; il cubo Indicatori demografici (dataset [6] e [7]) usa NUTS-3 `ITD10`/`ITD20`, coerente con AGID. La disomogeneità si riconcilia a posteriori con il sidecar `nuts_aliases.ttl` (sez. 4). Una seconda asimmetria: per le 4 province senza NUTS-3 Eurostat (Monza-Brianza, Fermo, BAT, Sud Sardegna) ISTAT usa codici proprietari `IT108`–`IT111`, modellati come `skos:exactMatch` (sez. 4).

**[5] Occupati per provincia, media annua 2025** — file `istat_occupati_provincia_2025_v1.csv`. Databrowser: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500LAB,1.0/LAB_OFFER/LAB_OFF_EMPLOY/DCCV_OCCUPATIT1/DCCV_OCCUPATIT1_PROVDATA/IT1,150_938_DF_DCCV_OCCUPATIT1_21,1.0>. **Filtri impostati**: ultimo anno disponibile (2025, media annua); solo province; aggregato per sesso. **Composizione**: 107 entità (105 in NUTS-3 + 2 PA in NUTS-2), 1 misura "occupati 15–89 anni (migliaia)". Disallineamento temporale con lo snapshot INPS 1.1.2026: pochi mesi. **Ruolo nell'IDPT**: denominatore D1 (occupati); alimenta il **cubo 5**.

**[6] Indicatori demografici provinciali, 1.1.2026** — file `istat_indicatori_demografici_provincia_2026_v1.csv`. Databrowser: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,POP,1.0/POP_POPULATION/DCIS_INDDEMOG1/IT1,22_293_DF_DCIS_INDDEMOG1_1,1.0>. **Filtri impostati**: anno di riferimento 1.1.2026 (stima preliminare). Allineamento temporale perfetto con lo snapshot INPS. **Composizione**: 107 entità (PA in NUTS-3 corretto), 6 indicatori — `POP014`, `POP1564`, `POP65OVER`, `OLDAGEDEPR`, `AGEINDEX`, `MEANAGEP` (riusati come `skos:notation` nella code-list SKOS del progetto). **Ruolo nell'IDPT**: nessuna componente del numero, ma variabili di contesto territoriale. Alimenta il **cubo 6** insieme al dataset [7].

**[7] Tasso di natalità e speranza di vita a 65 anni, 2025** — file `istat_natalita_speranza_di_vita_2025_v1.csv`. Stesso databrowser del dataset [6]. **Filtri impostati**: 2 indicatori non disponibili al 1.1.2026 perché misurati su base annua chiusa, rilasciati con riferimento 2025. **Composizione**: 107 entità, 2 indicatori — `BIRTHRATE` (tasso di natalità per mille, provvisorio) e `LIFEEXP65T` (speranza di vita a 65 anni, stimato). **Ruolo narrativo**: `LIFEEXP65T` è la variabile "durata della pensione" provincia per provincia, con noto gradiente Nord/Sud (Bolzano >22 anni, province meridionali <20). Confluisce nel **cubo 6** con il dataset [6] — unificati per coerenza di fonte, granularità e natura.

### 2.3 MEF

**[8] Redditi e variabili IRPEF su base comunale, anno di imposta 2024** — file `mef_redditi_irpef_comune_2024_v1.csv`. Dipartimento delle Finanze (MEF). **URL CSV (ZIP)**: <https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800>. **Pagina ufficiale**: <https://www.finanze.gov.it/it/statistiche-fiscali/open-data-comunale-principali-variabili-irpef/>. **Licenza**: **CC-BY 3.0** ([generica, non IT](https://creativecommons.org/licenses/by/3.0/)) — dichiarazione testuale del MEF: *"I dati sono rilasciati con licenza Creative Commons 3.0"*. **Composizione**: 7.897 comuni × 53 colonne (per ogni voce di reddito: doppia colonna "Frequenza" + "Ammontare in euro"). **Granularità**: comunale, riaggregabile a provincia via `Sigla Provincia` con group-by. **Granularità temporale**: anno di imposta 2024 (redditi prodotti nel 2023, dichiarati nel 2024), disallineato di ~3 anni dallo snapshot INPS — limite minore dichiarato. **Variabili usate** (5 su 53): `v2` Reddito da lavoro dipendente, `v4` Autonomo, `v5` Imprenditore contabilità ordinaria, `v6` Semplificata, `v7` Partecipazione — componenti del **monte redditi da lavoro** (denominatore D2). Più `v3` Reddito da pensione come **validazione cross-fonte** col dataset INPS [1]. **Anomalie**: NA-bug pandas sui 92 comuni di Napoli con `Sigla="NA"` interpretata come `NaN`; riga sentinella `Codice Istat=0` da filtrare. **Ruolo nell'IDPT**: denominatore D2 dopo aggregazione `Sigla Provincia` → 107 province; alimenta il **cubo 7**.

Lo stesso URL distribuisce, accanto al CSV, anche un file RDF/XML con lo stesso contenuto. **Non è stato usato come fonte di dati** ma è conservato nella cartella `data/` come **caso di studio negativo** della pratica LOD nelle PA italiane: namespace `fakeurl`, variabili anonime `v1..v22`, modellazione wide senza `qb:Observation`, data malformata `2026-23-04`. Discussione completa in sez. 4.9 come contrappunto al lavoro AGID-grade del resto del grafo.

### 2.4 Ancore semantiche AGID + geometrie ausiliarie

Tre risorse non statistiche: due vocabolari AGID per l'ancoraggio semantico territoriale + un GeoJSON Openpolis per il rendering cartografico.

**[9] Vocabolario Controllato Province d'Italia — AGID OntoPiA** — file `data/provinces.ttl`. **URL canonico**: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces>. **Raw TTL**: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/provinces/provinces.ttl>. **Licenza**: **CC-BY 4.0** ([codice AGID `A21_CCBY40`](https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40)), verificata direttamente nelle triple `dct:license` del file. **Contenuto per provincia**: URI canonica, `skos:prefLabel` IT/EN, `skos:notation` (codice ISTAT a 3 cifre), `clv:acronym` (sigla 2 lettere), `owl:sameAs` verso NUTS Eurostat (eventualmente multipli), `clv:situatedWithin` (regione), `clv:hasRankOrder` (3 ordinaria, 4 città metropolitana). **Dimensioni**: 107 province + 116 link verso NUTS (9 NUTS storici extra per le polinominate: Bergamo, Udine, Sassari, Nuoro, Rimini, Sud Sardegna), ~2.712 triple. **Ruolo nel grafo**: ancora semantica primaria. Riusiamo le 107 URI AGID per identificare le province; il multi-typing OntoPiA (`clv:Province` + `clv:AdminUnitComponent` + `skos:Concept` + `clv:Feature`) viene ereditato gratis. È anche il pivot del linking esterno: dai suoi `owl:sameAs` NUTS si arriva al LOD Cloud europeo, e i 107 `owl:sameAs` verso DBpedia (sez. 4) chiudono la quintupla identità di ogni provincia.

**[10] Vocabolario Controllato Regioni d'Italia — AGID OntoPiA** — file `data/regions.ttl`. **URL canonico**: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/regions>. **Raw TTL**: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/regions/regions.ttl>. **Licenza**: **CC-BY 4.0**. Struttura analoga al [9]: 20 regioni, ~477 triple. **Ruolo nel grafo**: ancora di livello superiore per query SPARQL di aggregazione regionale (es. q10 % retributivo per regione).

**[11] Geometrie provinciali ISTAT, ridistribuite da Openpolis** — file `data/limits_IT_provinces.geojson`. **Download**: <https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson>. **Repository**: <https://github.com/openpolis/geojson-italy>. **Licenza**: **CC-BY** (ereditata da ISTAT, mantenuta da Openpolis). Attribuzione doppia ISTAT + Openpolis. **Origine**: confini amministrativi ufficiali ISTAT ridistribuiti in GeoJSON (proiezione WGS84). Match IDPT ↔ poligoni sul campo `codice_istat`. **Ruolo nel progetto**: layer cartografico per le mappe Folium (sez. 5). **Ruolo nel grafo RDF**: nessuno — file di puro rendering, non entra fra le triple. Documentato per completezza di provenance.

### 2.5 Tabella riepilogativa delle licenze

| Fonte | # dataset | Licenza | URL canonico |
|---|---|---|---|
| INPS — Osservatorio statistico | 4 cubi OLAP | IODL 2.0 | <https://www.dati.gov.it/iodl/2.0/> |
| ISTAT — `esploradati.istat.it` | 3 estrazioni | CC-BY 3.0 IT | <https://creativecommons.org/licenses/by/3.0/it/> |
| MEF — Dip. Finanze | 1 CSV (+ 1 RDF di facciata) | CC-BY 3.0 | <https://creativecommons.org/licenses/by/3.0/> |
| AGID — OntoPiA | 2 vocabolari TTL | CC-BY 4.0 | <https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40> |
| Openpolis (deriv. ISTAT) | 1 file GeoJSON | CC-BY | <https://github.com/openpolis/geojson-italy> |

La compatibilità di queste cinque licenze sorgente con la licenza scelta per il deliverable finale del progetto (CC-BY 4.0) è discussa in sez. 6.

---

## 3. Elaborazione dei dataset

Prima di poter trasformare i dati in RDF e modellarli ontologicamente — che è materia della sez. 4 — è stato necessario portare le nove fonti tabellari della sez. 2 a una rappresentazione *coerente, pulita e armonizzata* a livello di tabella. In questa sezione "elaborazione" significa esattamente questo: data cleaning, normalizzazione, aggregazione, unpivot, stima delle misure soppresse o non pubblicate. Le anomalie tecniche che la sez. 2 ha citato in chiusura di ogni scheda dataset — formato italiano dei numeri, quoting non standard, soppressioni per privacy, asimmetrie territoriali, ex-province sarde, fake-NUTS, bug `pandas`, sentinelle MEF — vengono qui risolte una alla volta, dichiarando per ognuna il pattern algoritmico adottato. La distinzione metodologica fra **elaborazione** (qui) e **trasformazione semantica** (sez. 4) attraversa l'intera architettura del progetto: tutto il lavoro tabellare è chiuso prima che venga emessa la prima tripla RDF.

### 3.1 macrorefine: motore e architettura della pipeline

L'elaborazione è stata realizzata interamente con **macrorefine**, libreria Python di data cleaning a pipeline sviluppata appositamente per il progetto. macrorefine ha un'architettura concettualmente semplice ma rigorosa: un `Dataset` *immutabile* che incapsula un DataFrame `pandas`, una `Pipeline` *fluente* che concatena `Step` componibili, una `Recipe` riusabile che è una fabbrica di pipeline parametrizzate per uno specifico CSV sorgente. Ogni `Step` produce un nuovo `Dataset` (mai mutazione in-place) e registra un `StepRecord(name, params, metrics)` in una `History` immutabile associata al `Dataset`: di ogni step restano tracciati nome, parametri passati e metriche di output (es. righe lette / righe scritte / righe scartate, conteggio di match riusciti contro vocabolari esterni, totali preservati nelle aggregazioni). Questo audit trail strutturato è la "materia prima" che la sez. 4 trasformerà in lineage PROV-O minimale del grafo RDF.

Sono stati pertanto sviluppati **13 step custom LOD-aware** organizzati nel sottomodulo `macrorefine/src/macrorefine/steps/lod/`.

### 3.2 Inventario dei 13 step custom LOD-aware

Gli step sono raggruppati per famiglia funzionale in cinque file Python: `parse.py`, `link.py`, `aggregate.py`, `enrich.py`, `estimate.py`, `project.py`. La tabella seguente fornisce per ognuno la famiglia, il file di residenza e il problema che risolve. Un quattordicesimo step, `EmitQbObservations` in `emit.py`, è di pertinenza della trasformazione semantica e viene presentato nella sez. 4.

| Step | Famiglia | File | Problema risolto |
|---|---|---|---|
| `ParseItalianNumbers` | Parsing | `parse.py` | Numeri formato italiano (`9.999,9`) + sentinella `-` per privacy nei CSV INPS |
| `LinkProvinceToAGID_byNUTS` | Linking | `link.py` | Match province ISTAT (NUTS in `REF_AREA`) → URI AGID via SPARQL su `provinces.ttl`, gestione NUTS storici multipli + fake-NUTS `IT108`–`IT111` + alias `ITD1`↔`ITD10` PA |
| `LinkProvinceToAGID_bySigla` | Linking | `link.py` | Match comuni MEF → URI AGID tramite `clv:acronym` (sigla 2 lettere) |
| `LinkProvinceToAGID_byName` | Linking | `link.py` | Match nomi INPS → URI AGID tramite pipeline normalize → match diretto → dizionario `SETTLED_ALIASES` → fuzzy `rapidfuzz` (soglia 90) |
| `LinkSedeINPS` | Linking | `link.py` | Risoluzione delle 106 sedi INPS → URI `idpt:sede-inps-*` + emissione sidecar `inps_to_agid.ttl` |
| `AggregateSardiniaProvinces` | Aggregazione | `aggregate.py` | Aggregazione 8 ex-province sarde → 5 province AGID attuali (snapshot 2026) con somma su conteggi + media pesata sugli importi |
| `AggregateMEFRedditiByProvincia` | Aggregazione | `aggregate.py` | Group-by 7.897 comuni MEF → 107 province su `Sigla Provincia`, somma di 5 voci di reddito, unpivot wide→long |
| `UnpivotINPSPensioniVigenti` | Unpivot | `aggregate.py` | Wide→long del cubo 1: 5 gestioni × 3 misure (44 colonne wide → tabella long) |
| `UnpivotINPSRegimeSede` | Unpivot | `aggregate.py` | Wide→long stile B del cubo 2: 4 regimi × 3 measureType (`qb:measureType` come dimensione) |
| `UnpivotINPSSerieStorica` | Unpivot | `aggregate.py` | Wide→long stile B del cubo 3: 29 anni × 3 measureType, scarto righe `-` BAT/Fermo/Monza pre-2009 |
| `EnrichWithStaticMapping` | Enrichment | `enrich.py` | Lookup statici per arricchire colonne via dizionario (es. URI indicatore demografico + unità di misura per il cubo 6) |
| `EstimateAnnualAmount` | Stima | `estimate.py` | Ricostruzione importo annuo come `n × importo_medio × 13` per i cubi 2 e 3 con marcatura `obsStatus=E` |
| `ProjectGDPRegimeComposition` | Proiezione | `project.py` | Plan B GDP: euristica decorrenza→regime sul cubo 4 nazionale + proiezione sulle 107 quote provinciali GDP del cubo 1 |

A questi 13 step custom si aggiunge **un singolo script standalone**, `scripts/generate_agid_to_dbpedia.py`, che gestisce il linking esterno verso DBpedia: una query SPARQL remota (`https://dbpedia.org/sparql`) per estrarre tutte le province italiane, un match esatto su `prefLabel` normalizzata seguito da reconciliation manuale con 25 override hardcoded (14 città metropolitane "Metropolitan City of …" + 11 anomalie nominali tipo "Reggio nell'Emilia" ↔ "Reggio Emilia"), un'emissione finale di 107 triple `owl:sameAs` nel sidecar `output/mappings/agid_to_dbpedia.ttl`. Lo script è tenuto separato dagli step macrorefine perché ha bisogno di rete esterna e quindi va eseguito una volta in locale con un risultato versionato su git, mentre la pipeline macrorefine è offline e riproducibile.

### 3.3 Le anomalie tecniche risolte

Questa sotto-sezione racconta come ciascuna anomalia citata nella sez. 2 è stata risolta a livello di codice.

**Numeri in formato italiano (4 CSV INPS).** I CSV INPS usano `1.234,56` (punto migliaia, virgola decimali) e `-` per celle soppresse per privacy. Lo step `ParseItalianNumbers` (regex `^[\d.,\s\-]+$`, rimozione punti di migliaia, sostituzione virgola → punto, conversione a float, mappatura `-` → `NaN`) sostituisce `pandas.to_numeric(decimal=",")`, che non distinguerebbe il `-` "soppresso per privacy" (semanticamente diverso da NaN di valore mancante) da un errore di import. La sentinella `-` viene tracciata nelle metriche `StepRecord` come `count_suppressed` e successivamente mappata a `obsStatus=M` (Missing).

**Template OLAP sporco (CSV INPS).** I CSV INPS contengono righe non tabellari nell'header (titolo cubo, filtri, fonte, timestamp) e righe di totale finali. `pandas.read_csv` perde silenziosamente 28 righe — verificato. La lettura passa al modulo `csv.reader` con scansione esplicita: salta le righe iniziali finché non incontra l'header tabellare atteso, scarta la riga "Totale" finale, filtra le 7 righe di aggregati continentali (Europa, Asia, …, Oceania) che sono fuori dal perimetro IDPT (pensioni con residenza italiana).

**Quoting CSV non standard (CSV ISTAT).** ISTAT usa l'apice singolo come `quotechar` per gestire gli apostrofi nei nomi di provincia (`Valle d'Aosta`, `Reggio nell'Emilia`). Il default di `pandas.read_csv` (`quotechar='"'`) spezza i campi alla prima virgola interna; passare `quotechar="'"` a `pandas` fa errore perché alcune righe contengono apici non quotati per gli accenti. La soluzione è un helper `read_istat_csv()` su `csv.reader` stdlib con `quotechar="'"` esplicito, riusato dalle Recipe dei cubi 5 e 6.

**NA-bug pandas su CSV MEF.** `pandas.read_csv` converte di default `NA` (sigla di Napoli) in `numpy.nan`, perdendo l'identificatore territoriale dei 92 comuni napoletani: l'aggregazione per provincia produce un cluster "comuni senza provincia". Fix di una riga: `keep_default_na=False`. Il MEF distribuisce inoltre **una riga sentinella** con `Codice Istat=0` / `Sigla=0` / `Regione=Mancante/errata`, filtrata esplicitamente dalla Recipe del cubo 7 prima dell'aggregazione.

**Aggregazione retroattiva delle ex-province sarde.** La serie storica INPS mostra una discontinuità: 4 ex-province sarde (Olbia-Tempio, Carbonia-Iglesias, Medio Campidano, Ogliastra) presenti dal 2005 al 2011, scomparse dal 2012 e assorbite dalle 3 sedi INPS attuali. Lo step `AggregateSardiniaProvinces` lavora in due modalità: **snapshot** (cubo 1) aggrega 8 ex-province → 5 attuali preservando i totali al singolo intero; **mark serie storica** (cubo 3) ricostruisce le 84 osservazioni 2005-2011 sulle 3 sedi attuali e le marca con `obsStatus=E` + `prov:wasDerivedFrom`. Somme su conteggi dirette, medie su importi pesate sul numero di pensioni per non distorcere gli aggregati.

**Aggregazione 7.897 comuni MEF → 107 province.** `AggregateMEFRedditiByProvincia` fa `groupby('Sigla Provincia').sum()` sulle 10 colonne di interesse (5 voci × 2 misure) + unpivot wide→long che ribalta `v2/v4/v5/v6/v7` da colonne a righe della code-list `idpt:voci-reddito-mef`. Il match Sigla → URI AGID via `LinkProvinceToAGID_bySigla` usa `clv:acronym` come chiave esatta (sigla a 2 lettere univoca nel vocabolario AGID). Risultato: 535 righe (107 × 5 voci) pronte per l'emissione `qb:Observation`.

**Riconciliazione nominale INPS → AGID.** Il `LinkProvinceToAGID_byName` risolve il caso più delicato: i CSV INPS portano i nomi delle province in italiano, talora in maiuscolo, con varianti tipografiche storiche e abbreviazioni che non corrispondono allo `skos:prefLabel@it` del vocabolario AGID. La pipeline interna è a quattro stadi: (1) normalizzazione (lowercase, NFKD con drop dei combining accent, fix degli spazi attorno ai trattini, collasso del whitespace multiplo); (2) match diretto sul nome AGID normalizzato; (3) dizionario manuale `SETTLED_ALIASES` che risolve le tredici anomalie tipografiche strutturali ricorrenti nei CSV — nomi in maiuscolo, apostrofi e spazi spurî attorno ai trattini, denominazioni estese delle due PA, e varianti come `Reggio Calabria` → `Reggio di Calabria` o `Pesaro -Urbino` (trattino) → `Pesaro e Urbino` (congiunzione AGID); (4) fallback fuzzy via `rapidfuzz` (soglia 90) per gli eventuali residui. Le metriche `StepRecord` distinguono `matched_via_direct`, `matched_via_alias` e `matched_via_fuzzy` per l'audit a posteriori.

**Stima dell'importo annuo soppresso (cubi 2 e 3).** Il cubo OLAP INPS sopprime la statistica `Importo complessivo annuo` per privacy quando si scende a granularità provincia × regime (cubo 2) o sede × anno (cubo 3); abbiamo già menzionato il problema nella sez. 2. Lo step `EstimateAnnualAmount` ricostruisce l'importo come `numero_pensioni × importo_medio_mensile × 13` (12 mensilità più tredicesima), aggiunge una colonna `_status="estimated"`, e popola una colonna `_derived_from` con la coppia delle due osservazioni primarie da cui la stima è derivata (necessaria per emettere `prov:wasDerivedFrom` nella sez. 4). Il moltiplicatore 13 è una convenzione INPS pubblica per le pensioni annue; il pattern di derivazione esplicita preserva la separazione semantica fra dato primario e stima.

**Plan B GDP — la trasformazione più articolata.** Lo step `ProjectGDPRegimeComposition` colma in due fasi il vuoto descritto nella sez. 2.1 a proposito del dataset [4]: l'INPS non pubblica la composizione per regime delle pensioni dei dipendenti pubblici (GDP) a livello provinciale, e il Plan B la ricostruisce stimando la composizione nazionale e proiettandola sulle 107 quote provinciali.

*Fase 1 — composizione regime nazionale.* Lo step legge il CSV di decorrenza GDP nazionale (46 righe, da "anteriore al 31/12/1980" al 2025) e applica un'euristica anno-di-decorrenza → regime di liquidazione, le cui soglie sono calibrate sulle due grandi riforme previdenziali italiane:

- decorrenza **prima del 1996** → **retributivo puro** (sistema pre-Riforma Dini 1995);
- decorrenza **1996–2011** → **misto-Dini** (retributivo per l'anzianità maturata fino al 1995, contributivo per il resto);
- decorrenza **dal 2012** → **misto-Fornero** (retributivo fino al 2011, contributivo per il resto) o, raramente, **contributivo puro** (riservato a chi ha iniziato a contribuire dopo il 1996 — caso quasi assente nel 2026 perché tali coorti non hanno ancora raggiunto l'età pensionabile).

Sul CSV reale le quote nazionali risultano **13,85% retributivo, 34,23% misto-Dini, 51,92% misto-Fornero, 0% contributivo puro**.

*Fase 2 — proiezione provinciale.* Lo step legge via SPARQL il cubo 1 già emesso, estrae per ogni provincia il numero di pensioni `gestione-pubblici`, lo moltiplica per le quattro percentuali nazionali e genera **428 osservazioni stimate** (107 province × 4 regimi), con il totale provinciale preservato al singolo intero.

*Validazione.* Il totale nazionale ricomposto sulle 107 province (3.159.266) differisce di esattamente **11.991 pensioni** dal totale GDP del cubo 4 (3.171.257). Lo scarto è interamente spiegato dalle pensioni dei dipendenti pubblici residenti all'estero — Europa 7.833, Asia 381, Africa 1.941, America Settentrionale 745, America Centrale 300, America Meridionale 607, Oceania 184 (totale 11.991) — che il cubo 1 esclude per coerenza con la decisione "pensioni estere fuori dall'IDPT". La differenza è quindi riconciliata al singolo intero e dichiarata, non nascosta.

### 3.4 Le quattro Recipe a pipeline lineare — cubi 1, 5, 6, 7

Una `Recipe` macrorefine è la fabbrica che orchestra gli step custom per produrre la tabella pulita di un cubo, pronta per l'emissione `qb:Observation`. Le quattro Recipe di questa sottosezione condividono la forma più semplice — pipeline lineare, stile A qb (più misure per osservazione), nessuna stima né proiezione — e sono presentate dalla più elementare alla più articolata.

**Cubo 5 — Occupati ISTAT** (`cubo5_occupati_istat.py`). È il cubo più semplice del progetto, e per questo il primo a essere costruito: prende l'unica estrazione ISTAT degli occupati per provincia e la trasforma in 107 osservazioni, una per territorio. Non c'è nulla da pulire o da stimare — il valore arriva già pronto — così questa Recipe si è prestata da banco di prova per collaudare lo step di emissione prima di applicarlo ai cubi più complessi.

- `RenameColumns` — uniforma i nomi grezzi delle colonne ISTAT
- `CastTypes` — converte il numero di occupati in valore numerico
- `LinkProvinceToAGID_byNUTS` — aggancia ogni riga alla provincia AGID tramite il codice NUTS
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 107/107 province risolte, 107 osservazioni con la sola misura `numeroOccupati`.

**Cubo 7 — Redditi MEF** (`cubo7_redditi_mef.py`). Costruisce il denominatore della componente economica D2, cioè il monte dei redditi da lavoro di ogni provincia. La difficoltà non è concettuale ma di scala e di insidie tecniche: il CSV IRPEF è a livello comunale (7.897 righe) e nasconde una trappola, la sigla `NA` di Napoli che pandas scambierebbe per un valore mancante. La pipeline legge, ripulisce e aggrega fino alle 107 province.

- `read_csv(keep_default_na=False)` — legge il CSV preservando la sigla `NA` di Napoli
- `DropRows` — scarta la riga sentinella malformata (`Codice Istat=0`)
- `AggregateMEFRedditiByProvincia` — somma i comuni nelle province tenendo le 5 voci di reddito da lavoro
- `LinkProvinceToAGID_bySigla` — collega ogni provincia all'URI AGID tramite la sigla
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 535 osservazioni (107 province × 5 voci di reddito), 107/107 sigle risolte.

**Cubo 6 — Indicatori demografici ISTAT** (`cubo6_indicatori_demografici_istat.py`). Raccoglie le variabili di contesto territoriale — indice di vecchiaia, natalità, speranza di vita a 65 anni e altre — che descrivono i territori senza entrare nell'indice. La particolarità sta nelle fonti: i dati arrivano da due estrazioni ISTAT con anni di riferimento diversi (gli indicatori al 1.1.2026 e i due indicatori a base annua del 2025), unificate in un solo cubo tenendo l'anno come dimensione esplicita.

- `read_istat_csv` — legge i CSV ISTAT gestendone il quoting non standard
- unione dei due CSV — fonde le estrazioni 2026 e 2025 con `annoRiferimento` distinto
- `LinkProvinceToAGID_byNUTS` — risolve le province, PA comprese, via codice NUTS
- `EnrichWithStaticMapping` — aggiunge a ogni riga l'URI SKOS dell'indicatore e l'unità di misura
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 856 osservazioni (642 per il 2026, 214 per il 2025), validazione 7/7.

**Cubo 1 — Pensioni vigenti per residenza INPS** (`cubo1_vigenti_residenza.py`). È il cubo cardine: dal CSV principale INPS ricava il numeratore di D1 (numero di pensioni) e di D2 (monte pensioni), per provincia di residenza e tipo di gestione. Pur restando lineare, è la Recipe più impegnativa del gruppo, perché prima di ribaltare la tabella e agganciarla all'anagrafe AGID deve domare le idiosincrasie del dato INPS: i numeri in formato italiano e le otto ex-province sarde da ricondurre alle cinque attuali.

- `csv.reader` — legge il template OLAP INPS, che non è una tabella pulita
- `ParseItalianNumbers` — converte i numeri in formato italiano e marca le celle soppresse
- `AggregateSardiniaProvinces` — aggrega le 8 ex-province sarde nelle 5 attuali
- `UnpivotINPSPensioniVigenti` — ribalta gestioni e misure da colonne a righe
- `LinkProvinceToAGID_byName` — riconcilia i nomi INPS con le province AGID
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 535 osservazioni (107 province × 5 gestioni, inclusa la `gestione-totale`); 505 match diretti, 30 via dizionario di alias.

### 3.5 Le quattro Recipe con stile B qb e pattern di derivazione — cubi 2, 3, 4, 9

Le quattro Recipe rimanenti sono più articolate. Tre adottano lo stile B qb — la dimensione `qb:measureType` indica, osservazione per osservazione, quale misura si sta esprimendo — e tutte introducono il pattern dell'osservazione derivata visto nella sez. 3.3: stima dell'importo annuo soppresso, aggregazione retroattiva sarda, proiezione Plan B. Anche qui procediamo dalla più semplice alla più complessa.

**Cubo 4 — Decorrenza GDP nazionale** (`cubo4_decorrenza_gdp.py`). Unico cubo del grafo a granularità nazionale, fotografa le pensioni dei dipendenti pubblici per anno di decorrenza e fa da materia prima alla stima del Plan B (cubo 9). La pipeline è breve; l'unica scelta di metodo riguarda la coorte più vecchia, "anteriore al 31/12/1980", che invece di essere scartata viene aggregata sull'anno 1980 e marcata come stima, per non rompere il pattern uniforme delle osservazioni derivate.

- `read CSV` — legge il CSV di decorrenza GDP nazionale
- `ParseItalianNumbers` — converte i numeri in formato italiano
- aggregazione coorte pre-1980 — accorpa la decorrenza più vecchia sull'anno 1980 (`obsStatus=E`)
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 46 osservazioni (45 primarie più 1 aggregata stimata).

**Cubo 9 — Plan B GDP proiettato** (`cubo9_plan_b_gdp_projected.py`). Qui il pattern dell'osservazione derivata, introdotto nella sez. 3.3, viene applicato su scala. Il cubo ricostruisce la componente D3 per il settore pubblico — di cui l'INPS non pubblica la composizione provinciale per regime — proiettando la composizione nazionale stimata dal cubo 4 sulle quote di pensioni pubbliche di ogni provincia, lette dal cubo 1. Ogni osservazione è dichiaratamente una stima e conserva il doppio riferimento alle fonti da cui deriva.

- `_load_pubblici_per_provincia` — legge via SPARQL le quote provinciali di pensioni pubbliche dal cubo 1
- `ProjectGDPRegimeComposition` — proietta la composizione regime nazionale (cubo 4) su ciascuna provincia
- `EmitQbObservations` — emette le osservazioni con `obsStatus=E` e doppia `prov:wasDerivedFrom`

**Esito:** 428 osservazioni (107 province × 4 regimi), 856 link di provenance.

**Cubo 2 — Pensioni per regime e sede INPS** (`cubo2_regime_sede.py`). Prima Recipe a usare lo stile B, in cui ogni misura diventa un'osservazione a sé: per ciascuna coppia (sede, regime) il grafo registra separatamente numero di pensioni, importo medio e importo annuo complessivo. Quest'ultimo è soppresso per privacy nel dato sorgente, quindi viene ricostruito come stima (numero × importo medio × 13 mensilità). È anche la Recipe in cui nasce la classe propria `idpt:SedeINPS`, materializzata nel sidecar di linking.

- `UnpivotINPSRegimeSede` — genera le 848 osservazioni primarie (sede × regime × misura)
- `EstimateAnnualAmount` — ricostruisce l'importo annuo soppresso, 424 osservazioni stimate
- `LinkSedeINPS` — crea le istanze `idpt:SedeINPS` ed emette `inps_to_agid.ttl`
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 1.272 osservazioni (848 primarie + 424 stimate); la gestione Pubblici, assente dal cubo OLAP INPS, è esclusa anche dalla DSD.

**Cubo 3 — Serie storica per sede INPS** (`cubo3_serie_storica_sede.py`). Il cubo più grande del grafo: estende lo stile B ai 29 anni della serie storica 1998–2026. Oltre alla consueta stima dell'importo annuo, deve gestire due discontinuità della storia amministrativa italiana — le tre province nate nel 2009, per le quali le osservazioni precedenti semplicemente non esistono, e le ex-province sarde, i cui dati 2005–2011 vengono ricondotti retroattivamente alle sedi attuali e marcati come stima.

- `csv.reader` — legge il template OLAP INPS
- `ParseItalianNumbers` — converte i numeri in formato italiano
- `UnpivotINPSSerieStorica` — ribalta i 29 anni da colonne a righe
- `AggregateSardiniaProvinces` (modalità serie storica) — ricostruisce il 2005–2011 sardo sulle sedi attuali
- `EstimateAnnualAmount` — ricostruisce l'importo annuo soppresso
- `LinkSedeINPS` — risolve le sedi INPS
- `EmitQbObservations` — genera le osservazioni RDF

**Esito:** 9.105 osservazioni (5.986 primarie, 3.035 importo annuo stimato, 84 aggregazione Sardegna retroattiva), coperte da un'unica DSD.

### 3.6 Audit trail e validazione tabellare

L'intera elaborazione è coperta da **172 unit test pytest** (`macrorefine/tests/`) che esercitano gli step custom su micro-fixture rappresentative e da test di integrazione end-to-end sui CSV reali del progetto. Le verifiche di integrazione sono particolarmente rilevanti per la riproducibilità: per il cubo 1 viene controllato che la pipeline porti 110 → 107 entità territoriali dopo l'aggregazione sarda e che 107/107 vengano risolte da `LinkProvinceToAGID_byName`; per il cubo 7 che 7.897 comuni MEF vengano aggregati su 107 province con preservazione esatta delle 5 voci di reddito; per il cubo 9 che la conservazione dei totali GDP per provincia mostri `max diff = 0` rispetto al cubo 1 in input.

Accanto ai test, la `History` immutabile che macrorefine associa a ogni `Dataset` conserva il tracciamento step-per-step dell'intera pipeline — nome, parametri e metriche di ciascuna trasformazione applicata. È questo audit trail strutturato, disponibile a livello tabellare grazie alla scelta architetturale di macrorefine, che la sez. 4 rifonde nelle triple PROV-O minimali del grafo RDF (`prov:wasDerivedFrom` su ogni osservazione stimata + `dcterms:source` sui `qb:DataSet`). La distinzione "audit trail tabellare" (qui) vs "lineage semantico" (sez. 4) è meno una distinzione di sostanza che di livello di astrazione: la stessa provenance esiste a entrambi i livelli, con il livello RDF che la espone come triple interrogabili via SPARQL.

Le 172 verifiche tabellari sono solo il primo livello di validazione del progetto. Sopra di loro, nella sez. 4, troveranno posto i 33 check SPARQL post-emissione (10 sui vocabolari + 9 sui cubi + 14 sul DCAT-AP_IT del deliverable), che validano la conformità del grafo RDF rispetto al modello ontologico atteso. Le due famiglie di test sono complementari e ortogonali: i test tabellari verificano che la pipeline produca le tabelle corrette; i test SPARQL verificano che il grafo emesso dalle tabelle sia conforme allo schema ontologico atteso.

---

## 4. Trasformazione dei dataset — modellazione ontologica e RDF

Con la sezione 4 entriamo nel cuore del progetto: la **pratica del Linked Open Data**. Le tabelle pulite della sezione 3 vengono qui modellate ontologicamente e materializzate come grafo RDF, dove ogni decisione tecnica pesa sul giudizio "LOD ben fatto vs LOD di facciata".

Tre principi guidano l'intera modellazione:

- **Massimo riuso di vocabolari standard**: 9 vocabolari riusati a fronte di una sola classe propria su tutto il grafo.
- **Un cubo per fenomeno omogeneo**: 9 `qb:DataSet` separati invece di un cubo unico "tuttologo" (anti-pattern conclamato).
- **Pattern uniforme per le osservazioni derivate**: `sdmx-attribute:obsStatus sdmx-code:obsStatus-E` + `prov:wasDerivedFrom` applicato in 4 punti del grafo, su 4.399 osservazioni stimate totali.

Il risultato è un grafo RDF di circa **120.000 triple** distribuite su **6 grafi nominati** in Apache Jena Fuseki (`graph:agid`, `graph:vocabularies`, `graph:linking`, `graph:observations`, `graph:idpt-computed`, `graph:metadata`): le ~117.000 triple prodotte dal progetto più le ~3.200 del vocabolario controllato AGID, riusato in sola lettura in `graph:agid`. Le **13.312 `qb:Observation`** totali coprono 107 province × 29 anni × 9 cubi a seconda della DSD applicabile, materializzati come **107 `owl:sameAs` verso DBpedia** che chiudono la quintupla identità di ogni provincia nel LOD Cloud.

Uno **schema dell'architettura** dei 6 grafi nominati, con le relazioni principali (`dcterms:hasPart`, `prov:wasDerivedFrom`, `qb:structure`), è disponibile come immagine vettoriale interattiva nella landing page del sito (sez. "Architettura del grafo") all'URL <https://robertobrunocl.github.io/idpt-italia/graph_architecture.svg>.

### 4.1 I nove vocabolari riusati — perché ognuno è lì

Il primo lavoro della modellazione è stato selezionare i vocabolari da riusare. Il riuso massiccio di standard esterni è la metrica sostantiva del lavoro LOD: si misura sulla *parsimonia delle classi proprie* e sulla *densità di linking semantico*. La tabella seguente mappa i nove vocabolari al loro ruolo nel grafo; le note che la seguono, organizzate in quattro tier, ne giustificano l'adozione una alla volta. Le alternative valutate e scartate sono raccolte in chiusura di sottosezione.

| Vocabolario | Prefisso | Ruolo nel grafo |
|---|---|---|
| RDF Data Cube | `qb:` | struttura dei 9 cubi statistici: DSD, DataSet, Observation |
| SKOS | `skos:` | le 6 code-list controllate (gestioni, regimi, voci, indicatori, componenti, aree) |
| OntoPiA CLV + Vocabolari AGID | `clv:` | ancora territoriale: le 107 province come URI canoniche |
| SDMX content vocabulary | `sdmx-*` | attributi e code-list statistici standard (`obsStatus`, `unitMeasure`) |
| OWL-Time | `time:` | dimensione temporale (uso minimale; gli anni restano `xsd:gYear`) |
| DCAT-AP_IT | `dcatapit:` | metadati del dataset secondo il profilo italiano |
| Dublin Core + FOAF + vCard | `dcterms:` `foaf:` `vcard:` | titoli, licenze, autore e contatti su dataset e cubi |
| PROV-O | `prov:` | lineage delle osservazioni stimate (`prov:wasDerivedFrom`) |
| OWL sameAs | `owl:` | linking esterno: 107 verso DBpedia, più alias NUTS |

#### Tier 1 — Il cuore dell'ontologia

**RDF Data Cube** (`qb:`) — raccomandazione W3C ispirata a SDMX (lo standard ONU/Eurostat/FMI per i dati statistici), è l'ontologia canonica per pubblicare in RDF dati multidimensionali: `qb:DataSet` è il cubo, `qb:DataStructureDefinition` (DSD) il suo schema di dimensioni, misure e attributi, `qb:Observation` la singola cella. Nel progetto regge 9 DSD, 9 `qb:DataSet` e 13.312 `qb:Observation`, ancorate ai concetti `sdmx-concept:` via `qb:concept` per l'interoperabilità con i cubi Eurostat.

**SKOS** (Simple Knowledge Organization System, `skos:`) — raccomandazione W3C per modellare tassonomie e vocabolari controllati; fornisce `skos:Concept`, `skos:ConceptScheme`, le label e le `notation`. Lo usiamo per le sei code-list proprie (vedi 4.3) — tipi di gestione INPS, regimi di liquidazione, voci di reddito MEF, indicatori demografici ISTAT, componenti IDPT, aree geografiche — in coerenza stilistica con l'ancora AGID, anch'essa modellata in SKOS.

**OntoPiA CLV + Vocabolari Controllati AGID** (`clv:`) — OntoPiA è la rete di ontologie ufficiale della PA italiana (AgID, dal 2018, allineata ai Core Vocabulary europei ISA²); il suo Core Location Vocabulary descrive le entità territoriali con classi come `clv:Province` e property come `clv:acronym` o `clv:situatedWithin`, e i Vocabolari Controllati istanziano già tutte le 107 province e le 20 regioni con URI canoniche, codice ISTAT, sigla, NUTS e label IT/EN. È l'**ancora primaria** del grafo: riusiamo integralmente le 107 URI AGID senza emetterne di nostre, e grazie al multi-typing OntoPiA ogni provincia eredita quattro tipi (`clv:Province`, `clv:AdminUnitComponent`, `skos:Concept`, `clv:Feature`) al prezzo di una sola URI.

#### Tier 2 — Accessori per i cubi statistici

**SDMX content vocabulary** (`sdmx-attribute:`, `sdmx-code:`, `sdmx-concept:`) — pubblicato dal W3C insieme a `qb`, è la traduzione RDF dello standard SDMX e fornisce attributi e code-list statistici riusabili. La code-list che ci serve di più è `obsStatus` (`A` Normal, `E` Estimated, `P` Provisional, `F` Forecast, `M` Missing, `B` Break): 4.399 osservazioni del grafo portano `obsStatus=E` (Plan B del cubo 9, importo annuo stimato dei cubi 2 e 3, aggregazione retroattiva Sardegna del cubo 3, IDPT computed del cubo 8). I concetti `sdmx-concept:` sono inoltre ancorati alle nostre DimensionProperty e MeasureProperty via `qb:concept`.

**OWL-Time** (`time:`) — raccomandazione W3C per i concetti temporali strutturati (istanti, intervalli, durate). Nel progetto l'uso è **minimale**: la dimensione temporale puntuale (anno di snapshot, anno di decorrenza) è modellata con il più leggero `xsd:gYear`, senza perdita di semantica. È dichiarata nell'inventario per completezza, ma il suo peso nel grafo finale è marginale.

#### Tier 3 — Packaging del dataset

**DCAT-AP_IT** (`dcatapit:`) — profilo italiano AGID di DCAT-AP, a sua volta profilo europeo del Data Catalog Vocabulary del W3C. È la lingua franca per descrivere un dataset pubblico (chi lo pubblica, quando, con quale licenza e formato) ed è il vocabolario obbligatorio per i cataloghi della PA italiana. Il deliverable finale `idpt:atlante-idpt` è un `dcatapit:Dataset` (con triple-typing `dcat:Dataset` + `void:Dataset`, vedi 4.8) con metadati conformi al profilo.

**Dublin Core + FOAF + vCard** (`dcterms:`, `foaf:`, `vcard:`) — il corredo che DCAT-AP_IT porta con sé: `dcterms:` per i metadati documentali (titolo, descrizione, licenza, fonte, autore, publisher), `foaf:` per gli agenti, `vcard:` per i contact point. Sono applicati sia al `dcatapit:Dataset` finale sia ai 9 `qb:DataSet` interni, così che ogni cubo sia autoesplicativo e citabile anche fuori dal deliverable; l'autore è dichiarato come `foaf:Agent + dcatapit:Agent` con vCard.

#### Tier 4 — Tattico minimale

**PROV-O** (`prov:`) — raccomandazione W3C per provenance e lineage in RDF. L'uso è **minimale e tattico**: solo `prov:wasDerivedFrom` sulle 4.399 osservazioni stimate. Costa una sola property ma permette, con una query e l'operatore transitivo `prov:wasDerivedFrom+`, di risalire l'intera catena di derivazione fino alle osservazioni primarie (vedi 4.5); la provenance completa (`prov:Activity`, `prov:Agent` strutturati) resta un upgrade post-progetto, con i metadati di pipeline già tracciati a livello tabellare (sez. 3.6).

**`owl:sameAs`** — la property OWL che afferma l'identità fra entità di dataset diversi, standard di fatto del linking esterno nel LOD Cloud. Nel grafo conta 107 link AGID → DBpedia come contributo originale (sidecar `agid_to_dbpedia.ttl`, vedi 4.6) e 2 alias per riconciliare le PA del Trentino-Alto Adige (`ITD1`↔`ITD10`, `ITD2`↔`ITD20`, sidecar `nuts_aliases.ttl`); gli `owl:sameAs` NUTS verso `nuts.geovocab.org` arrivano invece pre-cotti dal TTL AGID nativo (116 link totali, incluse 9 revisioni NUTS storiche).

#### Vocabolari valutati e scartati

Per completezza, abbiamo consapevolmente lasciato fuori: **Schema.org Dataset** (SEO-only, non LOD-grade per PA italiana); **OWL "vero" con assiomi/restriction** (over-engineering per code-list a 4-8 valori); **GeoSPARQL** (non modelliamo geometrie nel grafo, il rendering passa per GeoJSON Openpolis); **Eurostat dimension namespace** (ridondante con `sdmx-attribute:`); **XKOS** (sovradimensionato per il nostro caso); **VoID completo** (incluso solo in forma minimale sul `dcatapit:Dataset`); **SDMX-RDF puro** (più pesante di qb, orientato a istituti nazionali); **modellazione "wide"** dove ogni record porta tutti i campi come property (anti-pattern, vedi caso MEF in 4.9); **DCAT puro** o DCAT-AP europeo senza profilo IT (perderebbero l'allineamento al contesto italiano); **GeoNames** e **Wikidata** come ancore territoriali primarie (sono target di linking esterno, non ancore native).

### 4.2 Una sola classe propria: `idpt:SedeINPS`

Su un grafo di ~120.000 triple, abbiamo definito *una sola* classe propria — `idpt:SedeINPS` — più due ObjectProperty associate. Tutto il resto è istanza di classi standard (`clv:Province`, `clv:Region`, `skos:Concept`, `qb:Observation`, `qb:DataSet`, `qb:DataStructureDefinition`, `dcatapit:Dataset`, ecc.). Questa parsimonia non è uno stilismo: è la metrica diretta su cui si misura "LOD ben fatto vs LOD inventato".

La motivazione della classe propria è semantica, non comoda. Come dichiarato nella sez. 2.1, l'asimmetria fra "provincia di residenza" (asse del cubo 1, 107 entità) e "provincia della sede INPS" (asse dei cubi 2 e 3, 106 sedi) è una realtà del dominio INPS che il grafo deve rappresentare onestamente. Le due opzioni alternative sarebbero state semanticamente disoneste: (a) "appiattire" le sedi sulla residenza richiederebbe duplicare alcune osservazioni e introdurrebbe doppi conteggi nelle query di aggregazione; (b) modellare le sedi come `clv:Province` confonderebbe due assi che il dato sorgente tiene distinti. Una classe propria preserva la distinzione senza intaccare la centralità dell'ancora AGID.

```turtle
@prefix idpt: <https://robertobrunocl.github.io/idpt-italia/> .
@prefix clv:  <https://w3id.org/italia/onto/CLV/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

idpt:SedeINPS a owl:Class ;
    rdfs:label "Sede territoriale INPS"@it ;
    rdfs:subClassOf clv:Feature ;
    rdfs:comment "Unità territoriale di gestione INPS, distinta dalla provincia amministrativa AGID."@it .

idpt:correspondsToProvinceAGID a owl:ObjectProperty ;
    rdfs:domain idpt:SedeINPS ; rdfs:range clv:Province ;
    rdfs:comment "Relazione 1-a-1: la sede corrisponde a una sola provincia AGID."@it .

idpt:aggregatesProvince a owl:ObjectProperty ;
    rdfs:domain idpt:SedeINPS ; rdfs:range clv:Province ;
    rdfs:comment "Relazione 1-a-N: la sede aggrega più province AGID (usato solo per Cagliari + Sud Sardegna)."@it .

# Esempio: la sede aggregata sarda
idpt:sede-inps-cagliari-e-sud-sardegna a idpt:SedeINPS ;
    skos:prefLabel "Cagliari e Sud Sardegna"@it ;
    skos:notation "INPS-CA-SU" ;
    idpt:aggregatesProvince
        <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/092> ,
        <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/111> .
```

Delle 106 sedi INPS del grafo, 105 sono in relazione `idpt:correspondsToProvinceAGID` (1-a-1) con una `clv:Province` AGID; solo 1 (la sede aggregata `idpt:sede-inps-cagliari-e-sud-sardegna`) è in relazione `idpt:aggregatesProvince` (1-a-N) con 2 province AGID. La distinzione delle due property — invece di unificarle in una sola con cardinalità variabile — rende le query SPARQL più pulite: chi cerca le sedi "normali" 1-a-1 le interroga via `correspondsToProvinceAGID`, chi vuole il caso aggregato lo riconosce immediatamente via `aggregatesProvince`. Le 106 sedi sono istanziate nel sidecar `inps_to_agid.ttl` (sez. 4.6) come parte dello stesso lavoro di linking che vi salva le label INPS originali come `skos:altLabel`.

### 4.3 Le sei code-list SKOS proprie

Il grafo ha bisogno di code-list controllate per le dimensioni qualitative dei cubi: tipi di gestione INPS, regimi di liquidazione, voci di reddito MEF, indicatori demografici ISTAT, componenti dell'IDPT, aree geografiche. Sono tutte modellate come `skos:ConceptScheme` (lo schema) con `skos:Concept` (i singoli termini) per coerenza col TTL AGID delle province e per parsimonia ontologica. Riusiamo come `skos:notation` le **sigle native** dei dataset sorgenti dove esistono, per coerenza forte con i CSV originari.

| Code-list | # concetti | `skos:notation` |
|---|---:|---|
| `idpt:tipi-gestione-inps` | 5 | `PRIV`, `PUB`, `AUTO`, `ASS`, `TOT` |
| `idpt:regimi-liquidazione` | 4 | `RETR`, `MIX-DINI`, `MIX-FORNERO`, `CONTR` |
| `idpt:indicatori-demografici` | 8 | sigle native ISTAT: `POP014`, `POP1564`, `POP65OVER`, `OLDAGEDEPR`, `AGEINDEX`, `MEANAGEP`, `BIRTHRATE`, `LIFEEXP65T` |
| `idpt:voci-reddito-mef` | 5 | sigle native MEF: `v2`, `v4`, `v5`, `v6`, `v7` |
| `idpt:componenti-idpt` | 4 | `PRESS-DEM`, `PESO-ECO`, `ERED-ST`, `IDPT-AGG` |
| `idpt:aree-geografiche` (ausiliaria) | 1 | `IT-TOT` (per il cubo 4 nazionale) |

Esempio della code-list `idpt:regimi-liquidazione`:

```turtle
idpt:regimi-liquidazione a skos:ConceptScheme ;
    skos:prefLabel "Regimi di liquidazione delle pensioni"@it ;
    dcterms:description "Sistema di calcolo della pensione, derivante dalla stratificazione storica delle riforme previdenziali italiane (Dini 1995, Fornero 2011)."@it ;
    skos:hasTopConcept idpt:regime-retributivo, idpt:regime-misto-dini,
                       idpt:regime-misto-fornero, idpt:regime-contributivo-puro .

idpt:regime-retributivo a skos:Concept ;
    skos:inScheme idpt:regimi-liquidazione ;
    skos:prefLabel "Retributivo"@it ;
    skos:notation "RETR" ;
    skos:scopeNote "Pensione calcolata sulle retribuzioni di fine carriera. Sistema pre-Riforma Dini 1995, per chi aveva ≥18 anni di contribuzione al 31/12/1995."@it .
```

Il riuso delle sigle ISTAT (cubo 6) e MEF (cubo 7) come `skos:notation` è il piccolo dettaglio LOD-aware che fa la differenza: chi legge il grafo riconosce immediatamente che `POP65OVER` o `v2` sono gli identificatori nativi delle fonti sorgenti — il legame fra CSV e RDF è esplicito a livello di vocabolario, non solo a livello di documentazione. La code-list `idpt:tipi-gestione-inps` include un quinto concetto `idpt:gestione-totale` (notation `TOT`) necessario al cubo 3 della serie storica, dove i dati INPS arrivano già aggregati sulle 4 gestioni e quindi modellati come "gestione totale". Le 6 code-list materializzate vivono in `output/vocabularies/code_lists.ttl` insieme alle classi e property proprie (`classes_and_properties.ttl`), e sono caricate nel `graph:vocabularies` di Fuseki.

**Packaging unificato per esplorazione visuale.** I due file ontologici sopra elencati (classi/property e code-list) sono affiancati da un terzo file `output/vocabularies/ontology.ttl`, generato come *bundle aggregato* dei due. Il bundle aggiunge in testa una dichiarazione `<idpt:> a owl:Ontology` con metadati ricchi (titolo bilingue, descrizione, creator, publisher, licenza CC-BY 4.0, versione, prefisso preferito via VANN) e include sotto il contenuto sostantivo di entrambi i file sorgente, per un totale di 551 triple. Lo scopo del bundle non è la pubblicazione in Fuseki — per quella vengono caricati i due file singoli nei rispettivi grafi nominati — ma il **caricamento in editor ontologici come Protégé**, che si aspettano una singola dichiarazione `owl:Ontology` come radice del file aperto. Aprendo `ontology.ttl` in Protégé via *File → Open File*, si naviga ad albero la classe propria `idpt:SedeINPS` con la sua subClassOf `clv:Feature`, le 2 ObjectProperty associate, le 10 `qb:DimensionProperty` e le 9 `qb:MeasureProperty`, le 9 `qb:DataStructureDefinition` e i 6 `skos:ConceptScheme` con i 27 `skos:Concept` totali.

Lo stesso file è visualizzabile come **grafo interattivo navigabile** caricandolo nel visualizzatore standard W3C/OWL **WebVOWL** ([service.tib.eu/webvowl](https://service.tib.eu/webvowl/)), che mostra classi come cerchi, property come archi, code-list SKOS come gruppi separati. Visto che il file è esposto pubblicamente via GitHub Pages, è sufficiente aprire l'URL diretto <https://service.tib.eu/webvowl/#iri=https://robertobrunocl.github.io/idpt-italia/output/vocabularies/ontology.ttl> per vederlo renderizzato. Il bottone "Visualizza l'ontologia su WebVOWL" è disponibile anche dalla landing page del sito.

### 4.4 Le nove DSD dei cubi qb

Ogni `qb:DataSet` del progetto ha una sua DSD (Data Structure Definition) esplicita, che dichiara dimensioni, misure e attributi. Tutte le `qb:DimensionProperty` con range `skos:Concept` sono linkate alla rispettiva code-list via `qb:codeList`; tutte le `qb:DimensionProperty` e `qb:MeasureProperty` sono ancorate al concetto SDMX appropriato via `qb:concept`. La tabella seguente sintetizza i 9 cubi.

| # | `qb:DataSet` | Dimensioni | Misure | Stile qb | # Obs |
|---|---|---|---|---|---:|
| 1 | `cubo-pensioni-vigenti-residenza` | provincia AGID × anno × tipoGestione | numeroPensioni, importoMedioMensile, importoAnnuoComplessivo | A | 535 |
| 2 | `cubo-pensioni-regime-sede` | sedeINPS × anno × regimeLiquidazione × measureType | (3 misure via measureType) | B | 1.272 |
| 3 | `cubo-pensioni-serie-storica-sede` | sedeINPS × anno × tipoGestione × measureType | (3 misure via measureType) | B | 9.105 |
| 4 | `cubo-pensioni-decorrenza-gdp` | areaGeografica × annoDecorrenza | numeroPensioni, importoMedioMensile, etàMediaDecorrenza | A | 46 |
| 5 | `cubo-occupati-istat` | provincia AGID × anno | numeroOccupati | A | 107 |
| 6 | `cubo-indicatori-demografici-istat` | provincia AGID × anno × indicatoreDemografico | valoreIndicatore | A | 856 |
| 7 | `cubo-redditi-mef` | provincia AGID × anno × voceReddito | frequenzaDichiaranti, ammontareTotale | A | 535 |
| 8 | `cubo-idpt-computed` *(graph nominato separato)* | provincia AGID × anno × componenteIDPT | valoreIDPT | A | 428 |
| 9 | `cubo-plan-b-gdp-projected` | provincia AGID × anno × regimeLiquidazione | numeroPensioni | A | 428 |

Il **mix di stili A + B** è una decisione metodologica esplicita. Lo stile A (multi-measure cubes: più misure per `qb:Observation`) è usato per 7 cubi dove tutte le misure hanno pari status semantico (cubi 1, 4, 5, 6, 7, 8, 9). Lo stile B (`qb:measureType` come dimensione: una osservazione per misura) è usato per i 2 cubi dove convivono misure primarie e misure stimate (cubi 2 e 3, dove l'`importoAnnuoComplessivo` è ricostruito come `n × media × 13` con `obsStatus=E` mentre le altre due misure sono primarie con `obsStatus=A`). Lo stile B permette di marcare diversamente lo status delle singole misure all'interno della stessa "cella" del cubo concettuale. Adottare lo stile A ovunque avrebbe perso questa distinzione; adottare lo stile B ovunque avrebbe triplicato il numero di osservazioni nei cubi che non ne hanno bisogno (es. il cubo 6 passerebbe da 856 a 856 × 1 = 856 — perché ha già una misura unica — ma il cubo 5 che ha una sola misura sarebbe inutilmente complicato).

Le URI delle osservazioni seguono un **pattern leggibile** `idpt:obs-{cubo-short}-{provincia-istat o sede-short}-{anno}-{dimensioni-residue}`. Esempi: `idpt:obs-vigenti-001-2026-privati` (Torino, gestione privati nel cubo 1), `idpt:obs-regime-sas-2026-priv-retr-num` (sede Sassari, privati, retributivo, misura `numeroPensioni` nel cubo 2), `idpt:obs-idpt-001-2026-press-dem` (Torino, pressione demografica nel cubo 8). Il pattern dà URI leggibili nelle query SPARQL e nei debug — anti-pattern hash UUID che sarebbero cortissimi ma illeggibili per chi scrive SPARQL a mano.

Frammento Turtle dello schema del cubo 1 — l'esempio più leggibile, da cui derivano tutti gli altri con piccole variazioni:

```turtle
@prefix idpt: <https://robertobrunocl.github.io/idpt-italia/> .
@prefix qb:   <http://purl.org/linked-data/cube#> .
@prefix sdmx-concept:   <http://purl.org/linked-data/sdmx/2009/concept#> .
@prefix sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#> .
@prefix clv:  <https://w3id.org/italia/onto/CLV/> .

idpt:provincia a qb:DimensionProperty ;
    rdfs:range clv:Province ;
    qb:concept sdmx-concept:refArea .

idpt:annoRiferimento a qb:DimensionProperty ;
    rdfs:range xsd:gYear ;
    qb:concept sdmx-concept:refPeriod .

idpt:tipoGestione a qb:DimensionProperty ;
    rdfs:range skos:Concept ;
    qb:codeList idpt:tipi-gestione-inps .

idpt:numeroPensioni a qb:MeasureProperty ;
    rdfs:range xsd:nonNegativeInteger ;
    qb:concept sdmx-concept:obsValue .

idpt:dsd-pensioni-vigenti-residenza a qb:DataStructureDefinition ;
    qb:component [ qb:dimension idpt:provincia       ; qb:order 1 ] ;
    qb:component [ qb:dimension idpt:annoRiferimento ; qb:order 2 ] ;
    qb:component [ qb:dimension idpt:tipoGestione    ; qb:order 3 ] ;
    qb:component [ qb:measure   idpt:numeroPensioni ] ;
    qb:component [ qb:measure   idpt:importoMedioMensile ] ;
    qb:component [ qb:measure   idpt:importoAnnuoComplessivo ] ;
    qb:component [ qb:attribute sdmx-attribute:obsStatus ;
                   qb:componentRequired "true"^^xsd:boolean ;
                   qb:componentAttachment qb:Observation ] .
```

L'emissione di tutte e 13.312 le `qb:Observation` è realizzata dal quattordicesimo step custom di macrorefine — `EmitQbObservations` in `macrorefine/src/macrorefine/steps/lod/emit.py`, brevemente già citato nella sez. 3.2 — che è lo step "ponte" fra elaborazione tabellare e trasformazione RDF. Lo step prende in input il `Dataset` finale di una Recipe (con colonne `provincia_uri`, `tipo_gestione_uri`, `anno`, eventuali misure, eventuale `_status`, eventuale `_derived_from`) e genera un file Turtle conforme alla DSD del cubo, completo di tutte le `qb:Observation` con URI a pattern, valori tipati, `obsStatus`, `prov:wasDerivedFrom` dove pertinenti. Lo step è parametrizzato e ha attraversato cinque revisioni durante le Fasi 4–6 (`obs_status_column` e `prov_derived_from_column` aggiunti per il pattern obs derivata, `measure_type_column` e `value_column` aggiunti per lo stile B, supporto a dimensioni con literal tipato `(uri, xsd_datatype)` aggiunto per `xsd:gYear`).

### 4.5 Il pattern "osservazione derivata" uniforme

Ogni misura del grafo che *non* è un dato primario letto dal CSV sorgente, ma una stima o un'aggregazione del progetto, è etichettata **in modo uniforme** con una coppia di asserzioni:

- `sdmx-attribute:obsStatus sdmx-code:obsStatus-E` (Estimated)
- `prov:wasDerivedFrom <obs-origine-1> , <obs-origine-2> , ...` (una o più sorgenti)

Il pattern è applicato in **4 punti del grafo**:

| # | Caso | Cubo | # obs marcate |
|---|---|---|---:|
| 1 | Aggregazione retroattiva Sardegna 2005–2011 | 3 | 84 |
| 2 | Importo annuo ricostruito (`n × media × 13`) | 2, 3 | 3.459 |
| 3 | Plan B GDP proiettato sulle 107 province | 9 | 428 |
| 4 | IDPT computed | 8 | 428 |
| | | **Totale** | **4.399** |

Esempio dell'osservazione Plan B GDP per Torino, regime retributivo:

```turtle
idpt:obs-plan-b-001-2026-retributivo a qb:Observation ;
    qb:dataSet idpt:cubo-plan-b-gdp-projected ;
    idpt:provincia <.../provinces/001> ;
    idpt:annoRiferimento "2026"^^xsd:gYear ;
    idpt:regimeLiquidazione idpt:regime-retributivo ;
    idpt:numeroPensioni "4900"^^xsd:nonNegativeInteger ;
    sdmx-attribute:obsStatus sdmx-code:obsStatus-E ;
    prov:wasDerivedFrom
        idpt:obs-vigenti-001-2026-pubblici ,   # 35.000 GDP Torino totali (cubo 1)
        idpt:cubo-pensioni-decorrenza-gdp ;    # 14% retributivo nazionale (cubo 4)
    rdfs:comment "Stima: 35.000 × 14% = 4.900 pensioni."@it .
```

Il vantaggio del pattern è doppio. Una **singola query SPARQL** recupera tutte le 4.399 osservazioni stimate del grafo, qualunque sia il loro tipo:

```sparql
SELECT ?obs ?cubo WHERE {
  ?obs a qb:Observation ; qb:dataSet ?cubo ;
       sdmx-attribute:obsStatus sdmx-code:obsStatus-E .
}
```

Una query parallela mostra la **catena transitiva** di derivazione, fino alle origini primarie, grazie all'operatore SPARQL `+` (uno o più passi sulla stessa property):

```sparql
SELECT ?origine WHERE {
  idpt:obs-plan-b-001-2026-retributivo prov:wasDerivedFrom+ ?origine .
}
```

Per le osservazioni dell'IDPT computed (cubo 8), che derivano dal Plan B che a sua volta deriva dal cubo 1, la stessa query mostra la quadrupla origine. È il pattern di **lineage auditabile** che giustifica l'uso minimale di PROV-O senza dover ricostruire una macchina della provenance da zero. La materia prima delle catene di derivazione esisteva già a livello tabellare nell'audit trail `History` di macrorefine (sez. 3.6): la transizione tabellare → RDF è stata progettata perché ogni catena tracciata negli `StepRecord` venisse materializzata come `prov:wasDerivedFrom` nel grafo.

### 4.6 Interlinking — i tre sidecar TTL

Oltre ai cubi statistici, il grafo contiene un secondo tipo di affermazioni: i collegamenti. Da una parte ci sono i collegamenti interni, che legano i dati alle ancore territoriali del progetto; dall'altra i collegamenti esterni, che agganciano le province italiane al resto del LOD Cloud. Non sono osservazioni statistiche ma asserzioni di equivalenza e di identità, e per questo vivono in tre file TTL separati — i *sidecar* — caricati nel grafo `graph:linking` di Fuseki. Vediamoli uno alla volta.

**`output/mappings/nuts_aliases.ttl`** raccoglie sei affermazioni che riconciliano le diverse codifiche territoriali incontrate nella sez. 2.2. Due riguardano le Province Autonome di Trento e Bolzano: il cubo ISTAT degli occupati le identifica con un codice NUTS di livello regionale, mentre il cubo degli indicatori demografici usa il codice provinciale, coerente con AGID. Per dichiarare che si tratta dello stesso territorio le colleghiamo con `owl:sameAs`, accompagnato da un commento che ne precisa la portata: l'equivalenza vale solo per queste due aree, dove la regione e la provincia coincidono. Le altre quattro affermazioni riguardano Monza-Brianza, Fermo, Barletta-Andria-Trani e Sud Sardegna, le province nate troppo tardi per avere un codice NUTS europeo ufficiale; ISTAT le identifica con codici propri, da `IT108` a `IT111`, che colleghiamo ai rispettivi territori con `skos:exactMatch`. La scelta di `skos:exactMatch` anziché `owl:sameAs` è deliberata e prudente: `IT108` non è letteralmente lo stesso oggetto di Monza-Brianza, ma un identificatore equivalente prodotto da un altro ente, e affermare un'equivalenza concettuale è più onesto che affermare un'identità piena.

**`output/mappings/inps_to_agid.ttl`** contiene circa 440 triple di due tipi. Il primo conserva i nomi originali con cui l'INPS scrive le province — spesso in maiuscolo o con grafie particolari — senza per questo creare nuove entità: ogni variante viene agganciata alla provincia AGID corrispondente come etichetta alternativa, marcata con un tag di lingua privato `it-x-inps` che ne segnala l'origine. Così la dicitura `MASSA CARRARA` resta registrata e interrogabile, ma appesa alla provincia ufficiale. Il secondo tipo descrive le 106 sedi territoriali INPS come istanze della classe `idpt:SedeINPS` e le collega alle province: nella quasi totalità dei casi una sede corrisponde a una sola provincia, con l'unica eccezione della sede "Cagliari e Sud Sardegna", che ne aggrega due. Il file è prodotto automaticamente durante la Recipe del cubo 2 (sez. 3.5).

**`output/mappings/agid_to_dbpedia.ttl`** è il contributo originale del progetto al linking esterno: 107 affermazioni `owl:sameAs` che collegano ogni provincia AGID alla corrispondente risorsa su DBpedia. Le abbiamo generate con uno script dedicato, descritto nella sez. 3.2: una query recupera da DBpedia tutte le province italiane, il confronto avviene sui nomi normalizzati, e i casi che non combaciano automaticamente — le quattordici città metropolitane e undici varianti di nome — sono risolti a mano con una lista di corrispondenze. Il file porta in testa la data della query verso DBpedia, perché quei dati cambiano nel tempo e il collegamento va datato.

Messi insieme, i tre sidecar danno a ogni provincia italiana una **identità a cinque punti** dentro il LOD Cloud. Per Torino, ad esempio:

```turtle
agidp:001  # = <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/001>
    a clv:Province, clv:AdminUnitComponent, skos:Concept, clv:Feature ;
    skos:prefLabel "Torino"@it , "Turin"@en ;
    skos:notation "001" ;
    clv:acronym "TO" ;
    clv:hasRankOrder 4 ;                                # città metropolitana
    clv:situatedWithin <.../regions/01> ;               # Piemonte
    owl:sameAs <http://nuts.geovocab.org/id/ITC11> ;    # AGID nativo
    owl:sameAs <http://dbpedia.org/resource/Metropolitan_City_of_Turin> ;  # nostro sidecar
    skos:altLabel "TORINO"@it-x-inps .                  # nostro sidecar

idpt:sede-inps-torino a idpt:SedeINPS ;
    skos:prefLabel "Torino"@it ;
    skos:notation "INPS-TO" ;
    idpt:correspondsToProvinceAGID agidp:001 .          # nostro sidecar
```

Cinque ancoraggi convergono sulla stessa entità: la URI ufficiale AGID, che resta il riferimento principale; il codice NUTS europeo, che apre verso i dati Eurostat; la risorsa DBpedia, da cui si raggiunge il resto del LOD Cloud fino a Wikidata; il nome originale usato dall'INPS, conservato per non perdere traccia della fonte; e la sede INPS che gestisce amministrativamente quel territorio. È il significato concreto della quinta stella nella scala di Berners-Lee: i dati non sono soltanto aperti e strutturati, ma davvero collegati ad altri.

### 4.7 Il cubo 8 IDPT computed — il cuore narrativo

Il cubo 8 è ciò che il progetto produce di originale: l'**Indice di Dipendenza Previdenziale Territoriale** materializzato come `qb:DataSet` in un grafo nominato separato `graph:idpt-computed`. La scelta di *materializzare* l'indice invece di lasciarlo a una vista SPARQL on-the-fly è la scelta giusta per la pratica LOD: il deliverable RDF deve contenere il risultato della ricerca, non rieseguirlo a ogni interrogazione.

**Formule delle tre componenti**, calcolate per ogni provincia:

- **D1 — Pressione demografica** = numero di pensioni vigenti (cubo 1, gestione totale) / numero di occupati (cubo 5). Range grezzo: 0,59 (Bolzano) – 1,48 (Reggio di Calabria). *Nota*: il dato INPS conta pensioni, non persone — una persona può ricevere più pensioni (vecchiaia + reversibilità).
- **D2 — Peso economico** = monte pensioni € (cubo 1) / monte redditi da lavoro € (cubo 7, somma di v2+v4+v5+v6+v7). Range: 0,33 – 0,77.
- **D3 — Eredità storica** = pensioni in regime retributivo (cubo 2 + Plan B GDP del cubo 9 per i Pubblici stimati) / pensioni totali con regime. Range: 0,42 – 1,37.

Le tre componenti grezze sono poi **normalizzate min-max** sui 107 valori della stessa componente — `(x − min) / (max − min)` produce un valore in [0,1] — e **aggregate via media aritmetica**:

`IDPT(provincia) = (D1_normalizzato + D2_normalizzato + D3_normalizzato) / 3`

Le 428 osservazioni del cubo 8 (107 province × 3 componenti + 1 aggregato) portano tutte `obsStatus=E` e `prov:wasDerivedFrom` esplicito verso le osservazioni primarie. Sul caso Sardegna: D3 è calcolata sulla sede INPS aggregata "Cagliari e Sud Sardegna" e attribuita per **replica integrale** alle due province AGID `092` Cagliari e `111` Sud Sardegna — scelta preferita alla divisione 50/50 arbitraria, in assenza di dati sulla composizione regime per ognuna delle due. La replica resta documentata nei `prov:wasDerivedFrom`, quindi auditabile.

**Doppia misura per riproducibilità** (scelta LOD-grade). Ogni obs componente porta sia `idpt:valoreIDPT` (normalizzato min-max) sia `idpt:valoreGrezzoIDPT` (valore pre-normalizzazione), permettendo a un consumer SPARQL di rifare aggregazioni con pesi alternativi senza dover ricalcolare D1/D2/D3 dai cubi primari. L'obs aggregato porta solo `idpt:valoreIDPT` (l'aggregato è media di valori già normalizzati, il "grezzo" non ha significato). Il DSD dichiara `qb:componentRequired "false"` per `valoreGrezzoIDPT`, in coerenza con la sua presenza solo sulle 321 obs componenti. Sul `qb:DataSet` cubo-idpt-computed è inoltre asserito l'attributo `idpt:metodoNormalizzazione "min-max"@it` (livello DataSet), che documenta nel grafo stesso il metodo applicato.

**Risultato sostantivo**: divario Nord/Sud nettissimo, rapporto di circa 20× fra estremi.

| | Top 5 (più dipendenti) | Bottom 5 (meno dipendenti) |
|---|---|---|
| 1 | Reggio di Calabria 0,675 | Bolzano/Bozen 0,034 |
| 2 | Taranto 0,651 | Milano 0,100 |
| 3 | Catanzaro 0,627 | Trento 0,104 |
| 4 | Oristano 0,580 | Prato 0,121 |
| 5 | Nuoro 0,552 | Padova 0,141 |

La narrativa è leggibile a colpo d'occhio: due PA alpine con economia dinamica e demografia giovane (Bolzano, Trento), due metropoli del triangolo industriale (Milano, Padova) e un distretto tessile (Prato) all'estremo basso; cinque province meridionali — quattro calabro-pugliesi e una sarda — dove bassa occupazione, demografia anziana ed eredità retributiva pre-Dini si sommano in cima alla classifica. La lettura cartografica completa è nella sez. 5.

### 4.8 DCAT-AP_IT del deliverable finale

Il deliverable finale è confezionato come un unico dataset descritto secondo lo standard di catalogazione della pubblica amministrazione italiana, e si trova in `output/dataset/atlante_idpt_dataset.ttl`. Lo stesso dataset è dichiarato sotto tre tipi insieme: `dcatapit:Dataset` per la conformità al profilo italiano DCAT-AP_IT, `dcat:Dataset` per la compatibilità con lo standard europeo generico, e `void:Dataset` per descrivere le caratteristiche tecniche del grafo. I nove cubi statistici non sono nascosti dentro al pacchetto: sono collegati a esso con `dcterms:hasPart`, così chi consulta il catalogo può arrivare direttamente al singolo cubo che gli interessa senza smontare il bundle.

I metadati accompagnano il dataset con tutto ciò che serve a citarlo e riusarlo. Ci sono il titolo e la descrizione in italiano e in inglese, tre temi del vocabolario europeo EuroVoc — affari sociali, economia e regioni — e undici parole chiave bilingui. La licenza è CC-BY 4.0, accompagnata da una nota che spiega come questa scelta ricomponga le cinque diverse licenze dei dati di partenza, tutte compatibili con il riuso e l'attribuzione; il dettaglio è nella sez. 2.5. Sono dichiarati anche gli standard a cui il grafo aderisce, ovvero SKOS, Data Cube e DCAT-AP_IT, l'autore come responsabile della pubblicazione e un recapito di contatto con email.

Il dataset è offerto in tre formati scaricabili, le *distribuzioni*: il bundle completo in Turtle, la stessa cosa in JSON-LD per chi lavora in ambienti web, e un archivio ZIP con i cubi tenuti separati, per chi vuole solo alcuni pezzi.

Infine, una piccola parte VoID descrive il grafo dall'interno: dichiara quante triple contiene il bundle pubblicato — 116.633 al momento dell'emissione finale, ovvero le sole triple prodotte dal progetto, senza il vocabolario AGID riusato che Fuseki carica a parte in sola lettura — indica con `dcat:accessURL` l'indirizzo da cui raggiungerlo, e segnala tre risorse di esempio da cui iniziare a esplorarlo — la provincia di Torino in AGID, una singola osservazione di pensioni e l'IDPT calcolato di Torino.

Tutto questo è verificato da quattordici controlli SPARQL automatici (`scripts/validate_dataset.py`): confermano la conformità al profilo DCAT-AP_IT, la presenza di tutti i metadati obbligatori, l'integrità dei collegamenti verso i nove cubi, la validità degli indirizzi delle distribuzioni e la presenza dell'autore e del contatto.

### 4.9 Il caso di studio negativo: "RDF di facciata" del MEF

Il file `data/mef_redditi_irpef_comune_2024_v1.rdf`, distribuito dal MEF a fianco del CSV (sez. 2.3), è la cartina al tornasole di cosa *non* è il Linked Open Data. Lo conserviamo come **caso di studio negativo** che fa risaltare per contrasto il lavoro di modellazione fatto altrove nel progetto. L'anatomia del file mostra cinque problemi cumulativi:

- **Namespace placeholder mai sostituito**: la dichiarazione XML è `xmlns:s="http://www1.finanze.gov.it/fakeurl#"`. Sì, "fakeurl" è letteralmente scritto nel namespace — segno di un export automatico da template mai personalizzato.
- **Variabili anonime senza URI semantiche**: i predicati sono `s:v1`, `s:v2`, …, `s:v22` — numeri ordinali invece di concetti. Chi legge l'RDF deve aprire una documentazione esterna per sapere che `v2` significa "Reddito da lavoro dipendente". Nel nostro grafo la stessa informazione vive come `idpt:voce-redd-lavoro-dipendente` con `skos:notation "v2"` per preservare la sigla nativa.
- **Modellazione "wide" senza Data Cube**: ogni record è una `<s:riga>` con tutti gli attributi compressi come property dirette. Zero `qb:Observation`, zero DSD, zero pattern di cubo. Anti-pattern conclamato — il singolo nodo "tutto-contenente" è opaco a query strutturate. Nel nostro grafo la stessa informazione è modellata come 535 `qb:Observation` interrogabili separatamente via SPARQL.
- **Zero linking, zero ancore semantiche**: zero occorrenze di SKOS, qb, DCAT, `owl:sameAs`, vocabolari AGID, classificazioni ISTAT. Le sigle delle province sono stringhe libere, non collegate al vocabolario controllato pubblicato dalla stessa PA italiana.
- **Data malformata**: `<s:aggiornato>2026-23-04</s:aggiornato>` — mese 23, formato non ISO 8601. Per un file che il MEF dichiara esplicitamente come "5-star RDF format" è il sigillo della distanza fra dichiarato e implementato.

Il caso MEF è in netto contrasto con il TTL AGID delle province (`data/provinces.ttl`, sez. 2.4), pubblicato dalla stessa Pubblica Amministrazione italiana ma con cura LOD-grade: vocabolario SKOS canonico, ontologia CLV ufficiale italiana, `owl:sameAs` nativi verso NUTS Eurostat (116 link), URI canoniche risolvibili via `w3id.org`, licenza esplicita CC-BY 4.0 dichiarata come `dct:license` nel file stesso. Stessa fonte di rilascio (la PA italiana), due esempi opposti di pratica LOD. L'insegnamento che il contrasto consegna è che il giudizio sostantivo sul LOD non si fa sulla compliance formale (il file ha estensione `.rdf`, valida sintatticamente, viene servito con MIME type corretto, è conforme alla grammatica RDF/XML), ma sulla **onestà semantica** (riusa vocabolari standard? espone URI significative? è interrogabile come parte del Web di dati? è connesso al LOD Cloud globale?). Per usare la scala di Berners-Lee, il file MEF è ★★★ vestite da ★★★★★: ha la forma esteriore del LOD 5★ ma il contenuto di un dump XML di una tabella.

---

## 5. Visualizzazione e interrogazione

Le sezioni 2, 3 e 4 hanno raccontato la costruzione del grafo IDPT. Questa sezione racconta i tre canali attraverso cui il grafo diventa **fruibile**: la **visualizzazione cartografica** che traduce le 428 osservazioni dell'IDPT computed in due mappe coropletiche interattive; l'**interrogazione SPARQL** con 12 query di demo che coprono la domanda di ricerca del progetto ed estraggono dal grafo letture aggregate, traiettorie storiche, validazioni cross-fonte; la **pubblicazione** in stack DCAT-AP_IT + GitHub Pages, con la demo dal vivo ancorata a una istanza Fuseki locale per evitare dipendenze di rete in fase di presentazione. Un grafo che non si interroga è solo un file Turtle; un grafo che non si visualizza è opaco al lettore non tecnico; un grafo che non si pubblica non è LOD. I tre canali sono complementari e ognuno indirizza un'audience diversa — il decisore politico vuole la mappa, il ricercatore vuole l'endpoint SPARQL, il portale di catalogazione vuole il `dcatapit:Dataset`.

### 5.1 Mappe coropletiche IDPT

Le due mappe coropletiche del progetto vivono in `output/visualizations/idpt_map.html` e `output/visualizations/idpt_components.html` come **pagine HTML standalone** generate da `scripts/build_maps.py`. La scelta di **Folium** (binding Python di Leaflet) è motivata da tre vincoli: (a) la mappa deve essere integrabile nella landing page GitHub Pages del progetto senza richiedere un backend GIS, (b) deve essere interattiva (tooltip al passaggio mouse, zoom, pan) per permettere la lettura provincia per provincia, (c) deve funzionare offline. Folium soddisfa tutti e tre i requisiti emettendo un singolo file HTML autocontenuto con tutta la libreria JavaScript inlinizzata. Le **geometrie provinciali** arrivano dal GeoJSON di Openpolis introdotto in sez. 2.4 (eredità ISTAT CC-BY), in proiezione WGS84; il match poligoni ↔ osservazioni IDPT avviene sul campo `codice_istat` come intero a 3 cifre.

La mappa principale `idpt_map.html` visualizza l'**IDPT aggregato** per le 107 province con scala a 5 quintili dal giallo (basso) al rosso (alto). L'uso dei quintili invece di una scala lineare è una scelta cartografica metodologica: distribuisce equamente le province nelle 5 classi di colore evitando che i picchi estremi (Reggio di Calabria 0.675) schiaccino visivamente la maggioranza delle province in un'unica fascia. Al passaggio del mouse su una provincia, un tooltip espone quattro valori: l'IDPT aggregato e le tre componenti normalizzate D1, D2, D3 — il lettore vede non solo "quanto" ma anche "perché" una provincia ha quel punteggio (es. per Reggio di Calabria D1 = 1.000 e D2 = 1.000 ma D3 = 0.026, contro Catanzaro con D1 = 0.638, D2 = 0.835, D3 = 0.409, che mostra una storia diversa fra pressione demografica e eredità retributiva).

La mappa componenti `idpt_components.html` espone **quattro mappe affiancate in CSS grid 2×2** — le 3 componenti separate più l'aggregato finale — per permettere il confronto visuale diretto. Una lettura interessante che emerge dal confronto: D1 (pressione demografica) e D2 (peso economico) hanno gradienti Nord/Sud molto simili (Sud più alto), mentre D3 (eredità storica del retributivo) mostra un gradiente diverso, più legato alla composizione storica del lavoro pubblico nelle singole province che non al gradiente economico complessivo — Sondrio e Belluno, per esempio, mostrano valori D3 alti pur essendo nel Nord, perché hanno alta concentrazione di pensioni di magistrati e impiegati pubblici di carriera lunga. Il limite di questa visualizzazione è che è **uno snapshot 2026**, senza animazione storica — un'animazione che mostrasse la traiettoria IDPT 1998–2026 (sulle dimensioni effettivamente disponibili nei cubi 3 e 5) sarebbe un upgrade post-progetto naturale, citato in 5.4.

### 5.2 Interrogazione via SPARQL — 12 query di demo

Il grafo IDPT è caricato in Apache Jena **Fuseki 5.2.0** locale via lo script `scripts/load_fuseki.sh` (HTTP PUT/POST idempotente sui 6 grafi nominati documentati in sez. 4 — `graph:agid`, `graph:vocabularies`, `graph:linking`, `graph:observations`, `graph:idpt-computed`, `graph:metadata`). L'avvio di Fuseki con il flag `--set tdb:unionDefaultGraph=true` è una **necessità configurativa scoperta empiricamente**: per default in Fuseki TDB2 le query SPARQL `SELECT ?s ?p ?o WHERE { ?s ?p ?o }` interrogano *solo* il default graph; visto che noi carichiamo tutto in grafi nominati, il default graph resta vuoto e le query restituirebbero zero risultati. La flag fa sì che il default graph sia l'unione dei 6 nominati, rendendo le query trasparenti senza dover modificare ogni query con `FROM <graph:...>` espliciti. La trappola è raccontabile nel report come "tipica della pratica LOD": caricare i dati in grafi nominati è semanticamente la cosa giusta da fare, ma richiede una configurazione lato server per essere immediatamente fruibile da SPARQL standard.

Lo script `scripts/run_sparql_demo.sh` esegue in batch le 12 query e ne stampa i risultati in formato CSV — il pattern di consumo previsto per la demo dal vivo. Le 12 query sono organizzate intorno alla domanda di ricerca del progetto (chi sono le province più dipendenti, perché lo sono, come si distribuisce l'eredità retributiva) e ne estendono il raggio a interrogazioni accessorie permesse dalla ricchezza del grafo (traiettoria storica del numero di pensioni, evoluzione dell'età alla decorrenza GDP nei decenni, durata attesa di una pensione provincia per provincia, validazioni cross-fonte INPS × MEF). La tabella riassuntiva:

| # | Query | Cubo / vocabolario | Domanda |
|---|---|---|---|
| q01 | Top 10 IDPT | cubo 8 + AGID | Province più dipendenti dal sistema |
| q02 | Bottom 10 IDPT | cubo 8 + AGID | Province meno dipendenti |
| q03 | Drill-down Torino | cubo 8 + AGID | Composizione IDPT di una specifica provincia |
| q04 | Distribuzione gestioni Calabria | cubo 1 + AGID regione | Composizione previdenziale al Sud |
| q05 | Serie storica top 5 sedi | cubo 3 | Crescita pensioni in 28 anni |
| q06 | Catena PROV | cubi 1, 4, 9 | Audit completo di una stima Plan B |
| q07 | Aggregato obs stimate | tutti | Dove vivono le stime nel grafo |
| q08 | Cross-fonte INPS×MEF | cubi 1 + 7 + AGID | Validazione cross-source su città metropolitane |
| q09 | Quintupla Torino | tutti (sidecar inclusi) | Cosa significa "5★" nel grafo concretamente |
| q10 | % retributivo per regione | cubi 1 + 2 + AGID | Eredità retributiva pre-1995 per regione |
| q11 | Età decorrenza per decennio | cubo 4 | Effetto cumulato delle riforme previdenziali |
| q12 | Durata attesa pensione | cubi 6 + 4 + AGID | Quanto durano in media le pensioni provincia per provincia |

Otto query sono commentate in dettaglio nei paragrafi che seguono, con snippet completo e lettura del risultato atteso.

#### q01 — Top 10 IDPT: la classifica delle province più dipendenti

La query interroga il cubo 8 (IDPT computed) per restituire le 10 province con valore di IDPT aggregato più alto, ordinate dal massimo. Il join con il vocabolario AGID estrae per ciascuna provincia il codice ISTAT a 3 cifre, la sigla a 2 lettere e l'etichetta italiana — filtrata con `FILTER(LANG(?provincia) = "it")` per scartare l'etichetta inglese che AGID porta accanto a quella italiana.

```sparql
PREFIX qb:   <http://purl.org/linked-data/cube#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX clv:  <https://w3id.org/italia/onto/CLV/>
PREFIX idpt: <https://robertobrunocl.github.io/idpt-italia/>

SELECT ?codice_istat ?sigla ?provincia ?idpt
WHERE {
  ?obs qb:dataSet idpt:cubo-idpt-computed ;
       idpt:componenteIDPT idpt:idpt-aggregato ;
       idpt:provincia ?p ;
       idpt:valoreIDPT ?idpt .
  ?p skos:notation ?codice_istat ;
     clv:acronym   ?sigla ;
     skos:prefLabel ?provincia .
  FILTER(LANG(?provincia) = "it")
}
ORDER BY DESC(?idpt)
LIMIT 10
```

Risultato (campione delle prime righe): Reggio di Calabria (RC) 0.675, Taranto (TA) 0.651, Catanzaro (CZ) 0.627, Oristano (OR) 0.580, Nuoro (NU) 0.552. Sotto: Cosenza, Brindisi, Vibo Valentia, Foggia, Crotone. **Nove province su dieci sono al Sud**, con la sola eccezione di una. È la risposta diretta alla domanda di ricerca del progetto.

#### q05 — Serie storica del numero di pensioni nelle 5 sedi INPS più popolose

La query interroga il cubo 3 (serie storica per sede INPS) per restituire l'andamento del numero di pensioni dal 1998 al 2026 sulle 5 sedi INPS più grandi (Milano, Roma, Torino, Napoli, Brescia), dichiarate inline tramite `VALUES`. Il cubo 3 è modellato in stile B qb con `qb:measureType` come dimensione, quindi il filtro `qb:measureType idpt:numeroPensioni ; idpt:numeroPensioni ?n_pensioni` seleziona le sole osservazioni della misura numerica.

```sparql
PREFIX qb:   <http://purl.org/linked-data/cube#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX idpt: <https://robertobrunocl.github.io/idpt-italia/>

SELECT ?sede ?anno ?n_pensioni
WHERE {
  VALUES ?sede_uri {
    idpt:sede-inps-torino idpt:sede-inps-milano idpt:sede-inps-roma
    idpt:sede-inps-napoli idpt:sede-inps-brescia
  }
  ?obs qb:dataSet idpt:cubo-pensioni-serie-storica-sede ;
       idpt:sedeINPS ?sede_uri ;
       idpt:annoRiferimento ?anno ;
       qb:measureType idpt:numeroPensioni ;
       idpt:numeroPensioni ?n_pensioni .
  ?sede_uri skos:prefLabel ?sede .
  FILTER(LANG(?sede) = "it")
}
ORDER BY ?sede ?anno
```

La query restituisce 145 righe (5 sedi × 29 anni); plottata come trend, mostra tutte e 5 le sedi in **crescita +30/+40% in 28 anni** — il "boom" pensionistico italiano in un grafico solo.

#### q07 — Distribuzione delle osservazioni stimate fra i cubi

La query conta per ciascun `qb:DataSet` del grafo quante delle sue `qb:Observation` portano `obsStatus=E` (Estimated). Il pattern uniforme di sez. 4.5 si traduce così in una singola query aggregata che mostra dove vivono tutte le 4.399 stime del grafo, distribuite fra i cubi.

```sparql
PREFIX qb:             <http://purl.org/linked-data/cube#>
PREFIX sdmx-attribute: <http://purl.org/linked-data/sdmx/2009/attribute#>
PREFIX sdmx-code:      <http://purl.org/linked-data/sdmx/2009/code#>

SELECT ?cubo (COUNT(?obs) AS ?obs_estimate)
WHERE {
  ?obs a qb:Observation ;
       qb:dataSet ?cubo ;
       sdmx-attribute:obsStatus sdmx-code:obsStatus-E .
}
GROUP BY ?cubo
ORDER BY DESC(?obs_estimate)
```

Risultato atteso: cubo 3 (3.119 obs — importo annuo stimato + Sardegna retroattiva), cubo 8 (428 — IDPT computed), cubo 9 (428 — Plan B GDP), cubo 2 (424 — importo annuo stimato), cubo 4 (1 — aggregato "anteriore 1980"). Totale **4.399 osservazioni stimate** materializzate col pattern uniforme — verificabili in una sola query, base del lineage di tutto il grafo.

#### q10 — Percentuale di pensioni in regime retributivo per regione

La query calcola per ogni regione italiana la quota di pensioni in regime retributivo. Numeratore: pensioni del cubo 2 con `regimeLiquidazione = retributivo` sommate per sede INPS e raggruppate per regione (traversando la gerarchia `sede → provincia AGID → regione AGID` via `idpt:correspondsToProvinceAGID` e `clv:situatedWithin`). Denominatore: totale delle pensioni del cubo 1 sulle stesse province aggregato per regione. Il cast `xsd:decimal(SUM(?n_retr)) / SUM(?n_tot)` previene la divisione intera che restituirebbe altrimenti zero.

```sparql
SELECT ?regione
       (SUM(?n_retr) AS ?totale_retr)
       (SUM(?n_tot)  AS ?totale_pensioni)
       (xsd:decimal(SUM(?n_retr)) / SUM(?n_tot) AS ?quota_retr)
WHERE {
  ?obs_r qb:dataSet idpt:cubo-pensioni-regime-sede ;
         idpt:sedeINPS ?sede ;
         idpt:regimeLiquidazione idpt:regime-retributivo ;
         qb:measureType idpt:numeroPensioni ;
         idpt:numeroPensioni ?n_retr .
  ?sede idpt:correspondsToProvinceAGID ?prov .
  ?prov clv:situatedWithin ?reg .
  ?reg skos:prefLabel ?regione .
  FILTER(LANG(?regione) = "it")

  ?obs_t qb:dataSet idpt:cubo-pensioni-vigenti-residenza ;
         idpt:provincia ?prov ;
         idpt:tipoGestione idpt:gestione-totale ;
         idpt:numeroPensioni ?n_tot .
}
GROUP BY ?regione
ORDER BY DESC(?quota_retr)
```

Risultato narrativo: le regioni del Centro-Sud (Calabria, Sicilia, Basilicata) mostrano quote di pensioni in regime retributivo più alte del Nord (Lombardia, Piemonte), riflesso della maggiore stabilità occupazionale pre-1995 nelle PA e nei settori protetti del Mezzogiorno e — al contrario — dell'alto turn-over post-Dini nel triangolo industriale.

#### q06 — Catena completa di derivazione PROV di una stima Plan B

La query usa l'operatore SPARQL `prov:wasDerivedFrom+` (property path con quantificatore "uno o più passi") per ricostruire, a partire da una singola osservazione del cubo 9 (Torino, regime retributivo, Plan B GDP 2026), tutte le entità del grafo da cui è stata derivata, navigando ricorsivamente la catena di provenance senza saperne in anticipo la profondità.

```sparql
PREFIX qb:   <http://purl.org/linked-data/cube#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX idpt: <https://robertobrunocl.github.io/idpt-italia/>

SELECT DISTINCT ?origine
WHERE {
  idpt:obs-plan-b-001-retr-2026 prov:wasDerivedFrom+ ?origine .
}
```

Per l'osservazione "Torino, regime retributivo Plan B GDP 2026", il `+` segue la catena attraverso due livelli: prima al cubo 1 con `gestione=Pubblici` (35.000 pensioni GDP totali Torino) e al `qb:DataSet` cubo 4 nazionale, poi — se anche quelle osservazioni hanno a loro volta una `prov:wasDerivedFrom` — risale ancora. È l'audit a profondità arbitraria che giustifica l'uso minimale di PROV-O senza dover ricostruire una macchina della provenance da zero. Lo stesso pattern applicato all'IDPT computed di una provincia (cubo 8) restituisce tutte le osservazioni primarie dei cubi 1, 2, 5, 7, 9 usate nel calcolo dell'indice.

#### q09 — Quintupla identità semantica di Torino

La query è la dimostrazione operativa del LOD 5★ raggiunto dal grafo. Per la provincia di Torino, restituisce in una singola interrogazione tutti i punti di identità semantica disponibili: URI canonica AGID, `skos:prefLabel` italiana, sigla `clv:acronym`, codice NUTS via `owl:sameAs` nativo AGID, URI DBpedia via `owl:sameAs` del sidecar del progetto, label INPS originale preservata come `skos:altLabel @it-x-inps`, URI della sede INPS via `idpt:correspondsToProvinceAGID`. Visto che ognuno di questi è un pattern diverso, sono dichiarati come branch alternativi `UNION`, ognuno con un `BIND` etichetta leggibile.

```sparql
SELECT ?relation ?value
WHERE {
  {
    BIND("AGID URI canonica" AS ?relation)
    BIND(STR(agidp:001) AS ?value)
  } UNION {
    BIND("NUTS via owl:sameAs" AS ?relation)
    agidp:001 owl:sameAs ?nuts .
    FILTER(STRSTARTS(STR(?nuts), "http://nuts.geovocab.org/"))
    BIND(STR(?nuts) AS ?value)
  } UNION {
    BIND("DBpedia via owl:sameAs" AS ?relation)
    agidp:001 owl:sameAs ?dbp .
    FILTER(STRSTARTS(STR(?dbp), "http://dbpedia.org/"))
    BIND(STR(?dbp) AS ?value)
  } UNION {
    BIND("skos:altLabel @it-x-inps (forma INPS originale)" AS ?relation)
    agidp:001 skos:altLabel ?al . FILTER(LANG(?al) = "it-x-inps")
    BIND(STR(?al) AS ?value)
  } UNION {
    BIND("Sede INPS (idpt:SedeINPS)" AS ?relation)
    ?sede idpt:correspondsToProvinceAGID agidp:001 .
    BIND(STR(?sede) AS ?value)
  }
}
```

(La query completa nel file `q09_quintupla_torino.rq` include altre due branch per la sigla e per la `skos:prefLabel`.) Il risultato è una tabella di 7 righe con tutte le identità di Torino. Il `FILTER(STRSTARTS(STR(?nuts), "http://nuts.geovocab.org/"))` discrimina i `owl:sameAs` "NUTS" dai `owl:sameAs` "DBpedia" guardando il prefisso dell'URI — necessario perché entrambe le triple usano la stessa property `owl:sameAs` ma puntano a spazi di nomi diversi.

#### q11 — Età media alla decorrenza GDP per decennio

La query aggrega le 46 osservazioni del cubo 4 (decorrenza GDP nazionale) per decennio di decorrenza, restituendo per ogni decennio dal 1980 in avanti l'**età media pesata** alla decorrenza pensionistica della Gestione Dipendenti Pubblici. La media pesata `SUM(?eta * ?n) / SUM(?n)` è necessaria perché i numeri annui di pensioni nuove variano da poche migliaia a centinaia di migliaia: una media aritmetica semplice (`AVG(?eta)`) darebbe lo stesso peso a un 1980 con poche pensioni e a un 2020 con tantissime, distorcendo il risultato verso i valori meno rappresentativi. Le fasce decennali sono costruite con `BIND(FLOOR(?anno_int / 10) * 10 AS ?decennio)` dopo aver convertito `xsd:gYear` a integer via `BIND(xsd:integer(STR(?anno)) AS ?anno_int)`.

```sparql
SELECT ?decennio
       (xsd:decimal(SUM(?eta * ?n)) / SUM(?n) AS ?eta_media_pesata)
       (SUM(?n) AS ?n_pensioni_decennio)
WHERE {
  ?obs qb:dataSet idpt:cubo-pensioni-decorrenza-gdp ;
       idpt:annoDecorrenza ?anno ;
       idpt:etaMediaDecorrenza ?eta ;
       idpt:numeroPensioni ?n .
  BIND(xsd:integer(STR(?anno)) AS ?anno_int)
  BIND((FLOOR(?anno_int / 10) * 10) AS ?decennio)
  FILTER(?anno_int >= 1980)
}
GROUP BY ?decennio
ORDER BY ?decennio
```

Risultato narrativo: l'età alla decorrenza GDP è cresciuta significativamente nei 5 decenni 1980–2020+, per effetto cumulato delle quattro grandi riforme previdenziali italiane (Amato 1992, Dini 1995, Maroni 2004, Fornero 2011). Il dato emerge dal grafo *senza intermediari interpretativi*: chiunque scarichi il cubo 4 e lanci la query lo vede.

#### q12 — Durata attesa di una pensione di vecchiaia per provincia

La query combina il cubo 6 (indicatori demografici ISTAT) e il cubo 4 (decorrenza GDP nazionale) per stimare la durata media attesa di una pensione di vecchiaia per ognuna delle 107 province. Il calcolo è `LIFEEXP65T_provincia + (65 − eta_decorrenza_nazionale)`: la `LIFEEXP65T` è la speranza di vita restante a 65 anni; se la decorrenza media nazionale 2020–2025 è (poniamo) a 64 anni, una persona che va in pensione a 64 ha vissuto 1 anno in meno rispetto al riferimento dei 65, quindi la durata attesa è `LIFEEXP65T + 1` anno. La query interna è una **subquery aggregata scalare** che restituisce un singolo valore (l'età media pesata nazionale alla decorrenza nel decennio 2020–2025) riusato in tutte le 107 righe della query esterna.

```sparql
SELECT ?sigla ?provincia ?lifeexp65 ?eta_decorrenza_2020s ?durata_attesa_pensione
WHERE {
  ?obs_l qb:dataSet idpt:cubo-indicatori-demografici-istat ;
         idpt:provincia ?p ;
         idpt:indicatoreDemografico idpt:ind-lifeexp65t ;
         idpt:valoreIndicatore ?lifeexp65 .
  ?p clv:acronym ?sigla ; skos:prefLabel ?provincia .
  FILTER(LANG(?provincia) = "it")

  {
    SELECT (xsd:decimal(SUM(?eta * ?n)) / SUM(?n) AS ?eta_decorrenza_2020s)
    WHERE {
      ?obs_d qb:dataSet idpt:cubo-pensioni-decorrenza-gdp ;
             idpt:annoDecorrenza ?anno ;
             idpt:etaMediaDecorrenza ?eta ;
             idpt:numeroPensioni ?n .
      FILTER(xsd:integer(STR(?anno)) >= 2020)
    }
  }

  BIND(?lifeexp65 + 65 - ?eta_decorrenza_2020s AS ?durata_attesa_pensione)
}
ORDER BY DESC(?durata_attesa_pensione)
```

La narrativa sul gradiente Nord/Sud che emerge dalla query è significativa: il noto divario sulla speranza di vita a 65 anni (Bolzano 21,6 anni contro province meridionali sotto i 19 anni) si traduce in una **differenza concreta di durata media della pensione**, dato che la letteratura statistica italiana espone raramente in questa forma diretta. Il grafo IDPT lo restituisce come lettura derivata gratuita del cubo 6 in combinazione col cubo 4.

Le query q02 (bottom 10), q03 (drill-down Torino), q04 (gestioni Calabria) e q08 (cross-fonte INPS×MEF) sono incluse nel set di demo e disponibili nei file `.rq` di `scripts/sparql/` — non sono qui commentate per parsimonia, ma seguono pattern già visti (filtri su URI vocabolario per q03 e q04, multi-cubo + cast per q08, `ORDER BY ASC` per q02).

### 5.3 Stack di pubblicazione

Il deliverable finale è accessibile attraverso tre livelli complementari. Il primo livello è il **`dcatapit:Dataset`** del progetto, presentato in dettaglio in sez. 4.8 e materializzato in `output/dataset/atlante_idpt_dataset.ttl`. Le tre distribuzioni dichiarate nel DCAT — `atlante-idpt.ttl` (bundle RDF/Turtle aggregato dei 9 cubi + sidecar + vocabolari), `atlante-idpt.jsonld` (versione JSON-LD per consumer Web), `atlante-idpt-bundle.zip` (archivio con i file separati per chi vuole granularità di cubo) — sono i tre formati pubblicati per coprire tre casi d'uso diversi: il triplestore (Turtle), l'applicazione Web/SPA (JSON-LD), e l'archivio per analisi offline (ZIP). Il VoID minimale (`void:triples`, `void:exampleResource`), insieme all'indirizzo di accesso `dcat:accessURL`, chiude il package con la dichiarazione delle caratteristiche tecniche del grafo.

Il secondo livello è la **landing page GitHub Pages** in `docs/index.html`, generata come pagina HTML statica con: descrizione del dataset auto-estratta da `dcterms:description`, statistiche aggregate (~120k triple, 13.312 obs, 107 sameAs DBpedia), la mappa principale `idpt_map.html` embedded come iframe interattivo, top/bottom 10 IDPT come tabelle HTML, link alle tre distribuzioni downloadable, 4-5 query SPARQL di esempio come blocchi pre-formattati copiabili, link al `REPORT.md` e al repository GitHub del progetto. Il branch `main` con path `/docs/` è esposto come sito statico all'URL `https://robertobrunocl.github.io/idpt-italia/` (l'username GitHub viene concretizzato in fase di deploy finale via lo script `scripts/finalize_namespace.py` che esegue il find-and-replace globale del namespace `https://example.org/idpt/` → `https://robertobrunocl.github.io/idpt-italia/` su tutti i 13 file TTL del progetto).

Il terzo livello è la **demo dal vivo**, in cui il grafo viene caricato in Fuseki locale e interrogato live con le 12 query commentate in 5.2. La scelta di non esporre un endpoint SPARQL pubblico permanente (es. via ngrok o cloud free-tier) è una decisione metodologica: in fase di presentazione conta avere zero dipendenze di rete, e Fuseki locale + `scripts/run_sparql_demo.sh` garantisce zero superficie di rischio. Un endpoint pubblico stabile (Trifid, Linked Data Frontend, oppure deploy di Fuseki su un VPS) è uno degli **upgrade post-progetto** naturali, citato in 5.4 insieme alla pubblicazione su `dati.gov.it` (registrazione standard per la PA italiana) e all'upgrade del namespace da GitHub Pages a `w3id.org/idpt-italia` via richiesta di Pull Request al maintainer di `perma-id/w3id.org`.

### 5.4 Limiti e prospettive

Il progetto raggiunge l'obiettivo della pratica LOD 5★ e produce una risposta sostantiva alla sua domanda di ricerca, ma è uno snapshot di un sistema. Cinque limiti vanno dichiarati esplicitamente come parte dell'onestà del lavoro.

**Granularità temporale dell'IDPT**. L'indice è calcolato solo per l'anno 2026. La serie storica del cubo 3 (1998–2026) fornisce la traiettoria del numero di pensioni nel tempo, ma non i denominatori storici (occupati per provincia × anno, monte redditi da lavoro per provincia × anno) che servirebbero per calcolare l'IDPT per ogni anno. Estendere il calcolo dell'IDPT alla serie storica richiederebbe l'integrazione di ulteriori cubi ISTAT-RFL (occupati storici, parzialmente disponibili) e MEF (redditi storici, anche pubblicati con disallineamento temporale crescente all'indietro).

**Plan B GDP — euristica decorrenza→regime**. La stima della composizione regime delle pensioni della Gestione Dipendenti Pubblici è derivata via un'euristica calibrata sulla normativa (Riforma Dini 1995, Riforma Fornero 2011) ma mai validata su microdati amministrativi INPS (che non sono pubblici). Un'eventuale collaborazione con INPS-DC Statistica permetterebbe di verificare l'accuratezza dell'euristica e di sostituirla con dati primari.

**Sardegna 1:N nella D3**. La decisione di replicare l'intero valore della sede aggregata Cagliari-e-Sud-Sardegna sulle due province AGID Cagliari (092) e Sud Sardegna (111) è un'approssimazione esplicita (sez. 4.7). Una stima migliore richiederebbe disaggregare la sede aggregata sulle due province con qualche criterio proxy (es. popolazione 65+ residente in ciascuna). La decisione attuale è quella più trasparente in attesa di un dato di disaggregazione disponibile.

**Disallineamento temporale MEF 2024 vs INPS 2026**. I redditi MEF si riferiscono al 2024 (dichiarati nel 2024 per l'anno di imposta 2023), gli snapshot INPS al 1.1.2026, gli occupati ISTAT al 2025. Il disallineamento di 1–3 anni introduce un rumore secondario nel calcolo di D2 ma non altera il segnale Nord/Sud principale.

**PROV-O minimale**. La provenance del grafo usa solo `prov:wasDerivedFrom`. Una valorizzazione completa del lineage richiederebbe di serializzare l'audit trail `History` di macrorefine come `prov:Activity` + `prov:Agent` + `prov:wasGeneratedBy` + `prov:wasAssociatedWith` strutturati — upgrade contenuto (i metadati di pipeline sono già tracciati negli `StepRecord`) ma non realizzato per parsimonia di scope.

Le **prospettive di sviluppo** che il lavoro apre sono varie. Una **animazione storica dell'IDPT** (su anni e indice ricalcolato) sarebbe il completamento naturale della visualizzazione. Un **confronto cross-paese via Eurostat NUTS-3** è praticabile poiché tutti i nostri 107 codici NUTS sono già linkati nel grafo via `owl:sameAs`: rifacendo lo stesso lavoro su Spagna, Francia, Germania (paesi con strutture pensionistiche comparabili) si potrebbero costruire IDPT comparabili a livello europeo. Una **registrazione del dataset su `dati.gov.it`** chiuderebbe il cerchio della pubblicazione conforme alla PA italiana. L'**upgrade del namespace a `w3id.org`** darebbe stabilità a 10+ anni alle URI canoniche del progetto. Un **endpoint SPARQL pubblico stabile** trasformerebbe il deliverable da repo statico a servizio interrogabile in modo persistente. Nessuno di questi è un blocco al risultato attuale, ma ognuno alza il valore del lavoro come infrastruttura riusabile da altri ricercatori.

---

## 6. Licenza del deliverable e compatibilità con le sorgenti

Il **deliverable finale del progetto** — il grafo RDF dell'Atlante IDPT pubblicato come `dcatapit:Dataset` — adotta come licenza **Creative Commons Attribuzione 4.0 Internazionale** (CC-BY 4.0). La scelta è compatibile con tutte e cinque le licenze sorgente dichiarate in sez. 2.5: IODL 2.0 (INPS), CC-BY 3.0 IT (ISTAT), CC-BY 3.0 generica (MEF), CC-BY 4.0 (AGID) e CC-BY (Openpolis) ammettono opere derivate con attribuzione, condizione che CC-BY 4.0 richiede esplicitamente. CC-BY 4.0 è inoltre la stessa licenza scelta da AGID per i propri vocabolari controllati, garantendo coerenza stilistica con il contesto normativo nazionale.

La dichiarazione di provenienza composita — "Dataset aggregato da fonti pubbliche con licenze CC-BY 3.0 IT (ISTAT), CC-BY 3.0 (MEF), CC-BY 4.0 (AGID), IODL 2.0 (INPS); riconfezionato come opera derivata con licenza CC-BY 4.0" — è materializzata nel campo `dcterms:rights` del `dcatapit:Dataset` finale e accompagna ogni distribuzione pubblicata (TTL, JSON-LD, ZIP).

Una sesta licenza, **CC-BY-SA 3.0**, vincola DBpedia, che è il target del linking esterno `owl:sameAs` del progetto (107 triple nel sidecar `agid_to_dbpedia.ttl`). Poiché un'asserzione `owl:sameAs` referenzia un'entità esterna senza duplicarne i contenuti, la clausola share-alike di DBpedia non si propaga al nostro deliverable, che resta licenziabile come CC-BY 4.0. L'attribuzione DBpedia è comunque mantenuta nel sidecar via `dcterms:source` verso `https://dbpedia.org/sparql` con timestamp della query, perché DBpedia evolve nel tempo e il mapping va datato.
