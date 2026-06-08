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

Il progetto risponde a una domanda di **data journalism a base semantica**: quali territori italiani sono più dipendenti dal sistema pensionistico, e quanto è sostenibile questa dipendenza in termini di rapporto pensionati/occupati, peso economico delle pensioni sul reddito locale ed eredità storica delle riforme previdenziali. La domanda è il *vettore* del lavoro, non il suo fine: il fine è la **pratica del Linked Open Data** — portare nove dataset pubblici italiani di basso livello (CSV statistici INPS, ISTAT, MEF, oltre ai vocabolari controllati territoriali AGID OntoPiA) a un grafo RDF **5★** sulla scala di Berners-Lee, con riuso massimo di vocabolari standard, ancoraggio semantico al contesto della PA italiana e linking esterno verso il LOD Cloud globale. Il vettore — l'analisi previdenziale — è ciò che dà senso narrativo al lavoro semantico.

Per rispondere alla domanda di ricerca ho costruito un **Indice di Dipendenza Previdenziale Territoriale (IDPT)** calcolato a livello provinciale come **media aritmetica di tre componenti normalizzate** in [0,1]. La prima componente, **D1 — pressione demografica previdenziale**, è il rapporto fra numero di pensioni vigenti e numero di occupati della provincia (`pensionati / occupati`): misura quanto la base produttiva di un territorio "sostiene" la sua base assistita. La seconda, **D2 — peso economico delle pensioni**, è il rapporto fra monte annuo delle pensioni erogate e monte annuo dei redditi da lavoro dichiarati (`monte_pensioni € / monte_redditi €`): misura quanto pesa la spesa pensionistica sul reddito complessivo del territorio. La terza, **D3 — eredità storica delle riforme**, è la quota di pensioni vigenti ancora liquidate in regime retributivo pre-Riforma Dini 1995 sul totale (`pensioni_retributivo / pensioni_totali`): misura il "peso del passato" delle stratificazioni normative. Le tre componenti grezze sono **normalizzate min-max** sulle 107 province e poi **aggregate via media aritmetica**, ottenendo un valore IDPT in [0,1] dove 0 è la provincia meno dipendente e 1 quella più dipendente. La scelta della media aritmetica (anziché pesata) è metodologica e non arbitraria: dichiara esplicitamente "le tre dimensioni contano uguale" senza introdurre pesi soggettivi da giustificare, e poiché i tre componenti normalizzati sono materializzati separatamente nel grafo qualunque consumer SPARQL può ricalcolare l'aggregato con pesi diversi se li ritiene più appropriati. La normalizzazione min-max è la trasformazione più trasparente; la sua sensibilità agli outlier (Reggio Calabria in alto, Bolzano in basso) è dichiarata fra i limiti dell'analisi.

Per costruire il grafo ho acquisito **9 dataset di partenza** + 2 vocabolari controllati AGID, li ho elaborati a livello tabellare con **macrorefine** — una libreria Python di data cleaning a pipeline sviluppata appositamente per il progetto, estesa con **13 step custom LOD-aware** organizzati in 9 Recipe — e trasformati semanticamente in un grafo RDF di **circa 117.000 triple** distribuite su **6 grafi nominati** Apache Jena Fuseki. Il grafo finale contiene **13.312 `qb:Observation`** strutturate in **9 `qb:DataSet`** modellati con RDF Data Cube, ancorate alle URI canoniche AGID delle 107 province e linkate esternamente a DBpedia tramite **107 asserzioni `owl:sameAs`**. Una sola classe propria (`idpt:SedeINPS`) è introdotta per onestà semantica, a fronte di 9 vocabolari standard riusati (qb, SKOS, OntoPiA CLV, SDMX content, OWL-Time minimale, DCAT-AP_IT, dcterms+foaf+vcard, PROV-O minimale, owl:sameAs). Un pattern uniforme di "osservazione derivata" — `sdmx-attribute:obsStatus sdmx-code:obsStatus-E` + `prov:wasDerivedFrom` — è applicato a quattro punti del grafo per **4.399 osservazioni stimate** totali (aggregazione retroattiva ex-province sarde 2005–2011, importo annuo ricostruito come `n × media × 13` sui cubi 2 e 3, proiezione Plan B GDP sulla composizione regime provinciale, materializzazione dell'IDPT computed), tutte navigabili con una singola query SPARQL via property path transitivo. Il deliverable è impacchettato come `dcatapit:Dataset` conforme al profilo italiano AGID di DCAT, pubblicato come bundle TTL/JSON-LD/ZIP, e interrogato in demo con 12 query SPARQL che coprono dalla classifica IDPT al drill-down per provincia, dall'evoluzione storica del numero di pensioni in 28 anni alla durata attesa di una pensione provincia per provincia.

Il risultato sostantivo è un **divario Nord/Sud netto, di circa 20× fra estremi**: in cima alla classifica IDPT 2026 si collocano Reggio di Calabria (0.675), Taranto, Catanzaro, Oristano e Nuoro — nove province su dieci al Sud — dove la combinazione di occupazione contenuta, demografia anziana ed eredità retributiva di alta funzione pubblica produce un livello di dipendenza dal sistema pensionistico nettamente più alto. In fondo si collocano Bolzano (0.034), Milano, Trento, Prato e Padova — economie dinamiche, demografia ancora giovane, eredità retributiva contenuta. Sul piano della pratica LOD, il lavoro fa emergere dieci scoperte tecniche raccontabili — dai NUTS storici multipli preservati come `owl:sameAs` nel TTL AGID, ai "fake-NUTS" proprietari ISTAT `IT108`–`IT111` modellati come `skos:exactMatch`, dalla discrepanza esatta di 11.991 pensioni Pubblici residenti all'estero fra cubo 4 nazionale e cubo 9 provinciale e culmina in un **case study negativo**: il file RDF/XML pubblicato dal MEF accanto al CSV delle dichiarazioni IRPEF comunali è un "RDF di facciata" (namespace `fakeurl`, variabili `v1..v22` anonime, modellazione wide senza `qb:Observation`, data malformata) che, nonostante l'autoetichetta "5-star RDF format", il progetto smonta riga per riga come esempio di compliance formale senza onestà semantica — in netto contrasto col TTL AGID delle province, pubblicato dalla stessa Pubblica Amministrazione italiana con cura LOD-grade.

Sul piano metodologico, il progetto adotta una sequenza esplicita "**ontologia prima del codice**": tutte le decisioni di modellazione (vocabolari, classi, code-list, DSD, pattern di derivazione, layout file e grafi nominati Fuseki) sono state congelate **prima** della scrittura di una singola riga di pipeline di trasformazione, evitando l'errore tipico delle pipeline open data di adattare a posteriori il modello al codice già scritto. La validazione è strutturata su due livelli ortogonali: **172 unit test pytest** sugli step LOD-aware di macrorefine validano la pipeline tabellare; **33 check SPARQL post-emissione** (10 sui vocabolari + 9 sui cubi + 14 sul DCAT-AP_IT del deliverable) validano la conformità del grafo RDF al modello ontologico atteso. Il deliverable finale — repository GitHub con codice + grafo + landing page GitHub Pages con mappa coropletica embedded + query SPARQL di demo — è riproducibile end-to-end, ed è rilasciato sotto licenza CC-BY 4.0 (vedi sez. 6 per il dettaglio sulla compatibilità con le licenze sorgente).

---

## 2. Dataset di partenza

Lo studio dell'Indice di Dipendenza Previdenziale Territoriale ha richiesto di attraversare tre ecosistemi open data italiani — **INPS** per la spesa pensionistica, **ISTAT** per l'occupazione e la demografia, **MEF** per i redditi da lavoro — ancorati al vocabolario controllato territoriale di **AGID OntoPiA**. Sono stati acquisiti in totale **9 dataset di partenza** (4 cubi OLAP INPS, 3 estrazioni dal databrowser ISTAT, 1 archivio CSV MEF a granularità comunale, 1 file GeoJSON ausiliario di geometrie provinciali) e **2 vocabolari controllati AGID** in formato Turtle (province e regioni). Per ciascuna fonte questa sezione dichiara l'URL canonico, i parametri di estrazione necessari alla riproducibilità, la licenza ufficiale verificata sul portale di pubblicazione, la composizione e il ruolo nel calcolo dell'IDPT.

Tre osservazioni di contesto utili a inquadrare il lavoro di acquisizione. **Primo**, i cubi OLAP dell'Osservatorio statistico INPS sono applicazioni JavaScript client-side: non esiste un URL diretto al CSV finale, ma solo l'URL del cubo, su cui l'utente imposta manualmente filtri, dimensioni di riga, dimensioni di colonna e statistiche prima dell'export. Per garantire riproducibilità del dataset di input — un requisito metodologico forte nella pratica LOD — questi parametri vanno annotati esplicitamente come parte della provenance del dato; nel report sono pertanto dichiarati alla stregua di un URL canonico. **Secondo**, ISTAT ha deprecato il vecchio data warehouse `dati.istat.it`, ora redirige al nuovo databrowser `esploradati.istat.it` che esporta in formato SDMX-like (header con codici standard, decimali col punto, separatore virgola, codifica UTF-8 con BOM) ma adotta un **quoting CSV non standard** — apice singolo come `quotechar` per gestire gli apostrofi nei nomi propri — che rompe il default di `pandas.read_csv` e richiede una lettura via `csv.reader` stdlib esplicitamente configurato. **Terzo**, il MEF affianca al CSV affidabile delle dichiarazioni IRPEF comunali un file RDF/XML formalmente compliant ma sostanzialmente vuoto di modellazione semantica (variabili `v1..v22` senza URI significative, namespace placeholder `fakeurl`, modellazione wide senza `qb:Observation`) — il *case study negativo* discusso in dettaglio nella sez. 4 con il framing "RDF di facciata".

### 2.1 INPS

Le quattro estrazioni INPS derivano tutte dall'**Osservatorio statistico** dell'Istituto, area pensioni vigenti e pensioni per anno di decorrenza. Sono pubblicate sotto la stessa licenza **IODL 2.0** ([Italian Open Data Licence v2.0](https://www.dati.gov.it/iodl/2.0/)), come dichiarato dal portale [INPS Open Data](https://www.inps.it/it/it/dati-e-bilanci/open-data.html). 

**[1] Pensioni vigenti per provincia di residenza, 2026** — file `inps_pensioni_vigenti_provincia_2026_v1.csv`. Cubo OLAP all'indirizzo <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/377>. È il dataset principale dell'intero progetto. **Filtri impostati**: anno 2026; tipo gestione = `Pensioni ai lavoratori dipendenti privati` + `Pensioni ai lavoratori dipendenti pubblici` + `Pensioni ai lavoratori autonomi e parasubordinati` + `Prestazioni assistenziali`. **Layout**: righe = provincia di residenza, colonne = tipo di gestione, statistiche = `Numero pensioni (SUM)`, `Importo medio mensile`, `Importo complessivo annuo (in milioni di euro) (SUM)`. La voce `Cumulo`, le `Assicurazioni facoltative` e le `Convenzioni internazionali` sono escluse per coerenza con il perimetro IDPT (voci marginali o doppi conteggi). L'export contiene 110 entità territoriali — le 107 province attuali più 2 Province Autonome del Trentino-Alto Adige più 3 ex-province sarde da aggregare a posteriori sulle 5 province AGID attuali — 4 tipologie di gestione, 3 misure, più 7 aggregati continentali per le pensioni erogate all'estero e una riga "Totale". Il totale verificato è di **20.925.413 pensioni** per circa **344 mld € di importo annuo**. Anomalie tecniche principali: numeri in formato italiano (`9.999,9`), celle `-` per valori soppressi per privacy o non applicabili, nomi province in MAIUSCOLO con varianti tipografiche (`MASSA CARRARA` senza trattino, `PESARO -URBINO` con spazio prima del trattino, `FORLI'-CESENA` con apostrofo dattilografico). Risoluzione delle anomalie nella sez. 3. **Ruolo nell'IDPT**: numeratore della dimensione D1 (pensionati per provincia) e numeratore della dimensione D2 (monte pensioni per provincia); alimenta il cubo 1 del grafo RDF e fornisce la quota provinciale GDP che il Plan B (sez. 3) proietta sulla composizione regime nazionale per generare il cubo 9.

**[2] Pensioni vigenti per regime di liquidazione e provincia della sede INPS, 2026** — file `inps_pensioni_vigenti_regime_liquidazione_provincia_2026_v1.csv`. Cubo OLAP all'indirizzo <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/389>. **Filtri impostati**: anno 2026 (nessun filtro su gestione: il cubo per regime non include i Pubblici per costruzione del cubo OLAP). **Layout**: righe = provincia sede INPS, colonne = regime di liquidazione, statistiche = `Numero pensioni (SUM)`, `Importo medio mensile`. La statistica `Importo complessivo annuo (in milioni di euro)` è **soppressa dal cubo OLAP alla cross-tab provincia × regime per motivi di privacy** — un esempio rappresentativo del compromesso fra granularità statistica e tutela dei microdati che attraversa la pubblicazione open data di fonte amministrativa. La ricostruzione di questa misura come stima `n × importo_medio_mensile × 13` (12 mensilità più tredicesima) è documentata nella sez. 3 e materializzata nel grafo come osservazione derivata con `obsStatus=E` e `prov:wasDerivedFrom` esplicito. L'export contiene 106 sedi territoriali — un asse diverso da quello della "provincia di residenza" del dataset [1] (`CAGLIARI E SUD SARDEGNA` aggregata, `FORLI` senza Cesena, `VERBANIA` come label di Verbano-Cusio-Ossola) — 4 regimi (`Retributivo`, `Misto riforma Dini`, `Misto riforma Fornero`, `Contributivo puro`), 2 misure. La copertura è di **12.873.198 pensioni**, il 96% del comparto Privati + Autonomi/Parasub del dataset [1], il 61,5% del totale generale. Restano fuori i Dipendenti Pubblici (circa 3,17 mln, oggetto del Plan B) e le pensioni Assistenziali (4,42 mln, per natura non disaggregabili per regime). Anomalie tecniche: stesse anomalie nominali del dataset [1] ma in maiuscolo, più etichette regime senza spazi (`MistoriformaDini`, `MistoriformaFornero`, `Contributivopuro`). **Ruolo nell'IDPT**: dimensione D3 (eredità storica delle riforme) per il segmento Privati + Autonomi/Parasub; alimenta il cubo 2 del grafo.

**[3] Pensioni vigenti per sede INPS, serie storica 1998–2026** — file `inps_pensioni_vigenti_serie_storica_provincia_1998_2026_v1.csv`. Cubo OLAP all'indirizzo <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/390>. **Filtri impostati**: tipo gestione = stesse 4 gestioni del dataset [1], per garantire confrontabilità diacronica. **Layout**: righe = provincia della sede INPS, colonne = anno (29 valori, 1998–2026), statistiche = `Numero pensioni (SUM)`, `Importo medio mensile`. Anche qui l'importo complessivo annuo non è disponibile in alcuna configurazione del cubo per la serie storica: viene ricostruito come stima `n × importo_medio × 13` per ognuna delle 6.150 osservazioni reali. Asse territoriale: 106 sedi INPS, identico al dataset [2] (non al dataset [1]). Anomalie temporali da gestire nella sez. 3: celle `-` per BAT, Fermo e Monza-Brianza negli anni 1998–2008 perché istituite nel 2009; salto numerico per le sedi sarde dopo il 2011 a seguito dell'aggregazione retroattiva di Olbia-Tempio, Ogliastra, Carbonia-Iglesias e Medio Campidano sulle sedi attuali. Verifica numerica di coerenza: la somma 2026 della serie storica restituisce 20.925.421 pensioni, coincidente al 99,99996% col dataset [1] (differenza di 8 unità per arrotondamenti). **Ruolo nell'IDPT**: alimenta il cubo 3 del grafo, che non entra nel calcolo dell'IDPT snapshot 2026 ma fornisce la prospettiva diacronica della spesa pensionistica italiana (la crescita di 15,2 → 20,9 mln pensioni in 28 anni, +37%, è uno dei riferimenti narrativi del lavoro).

**[4] Pensioni della Gestione Dipendenti Pubblici per anno di decorrenza, 2026 — totale categorie** — file `inps_pensioni_decorrenza_pubblici_tutte_categorie_2026_v1.csv`. Cubo OLAP all'indirizzo <https://servizi2.inps.it/servizi/osservatoristatistici/6/37/o/388>. **Filtri impostati**: anno 2026; tipo gestione = `Pensioni ai lavoratori dipendenti pubblici`. **Layout**: righe = anno di decorrenza, colonne (nessuna), statistiche = `Numero pensioni (SUM)`, `Età media alla decorrenza`, `Importo medio mensile`, `Importo medio mensile alla decorrenza`. **Limite strutturale del cubo OLAP**: la dimensione "Provincia" non è disponibile per costruzione su questo cubo. Non esiste alcuna pubblicazione INPS — né cubo OLAP, né dataset su `dati.gov.it`, né portale Open Data INPS — che esponga la composizione GDP × regime di liquidazione × provincia. Si tratta di un buco strutturale del rilascio open data INPS sul segmento pubblico, che il progetto risolve con il **Plan B**: stimare la composizione regime GDP a livello nazionale tramite un'euristica anno-di-decorrenza → regime calibrata sulle riforme Dini 1995 e Fornero 2011, e proiettare la composizione stimata sulle 107 quote provinciali GDP del dataset [1]. Il dataset [4] è l'input nazionale di questa proiezione. Dimensioni: dataset nazionale, 46 righe (decorrenze da "anteriore al 31/12/1980" al 2025), 4 misure; totale verificato **3.171.265 pensioni GDP** (coincidente col totale Pubblici aggregato del dataset [1] al netto delle pensioni Pubblici residenti all'estero). **Ruolo nell'IDPT**: alimenta il cubo 4 del grafo (decorrenza GDP nazionale) e, tramite l'euristica decorrenza→regime, il cubo 9 (Plan B GDP proiettato per provincia × regime).

#### Asimmetria territoriale fra i quattro cubi INPS — limite accettato

Una caratteristica delicata del rilascio open data INPS che attraversa i quattro dataset e va dichiarata esplicitamente è la **disomogeneità dell'asse territoriale**. Il dataset [1] (pensioni vigenti) adotta come dimensione la **provincia di residenza del titolare** della pensione: l'unità territoriale è dunque definita dal luogo in cui il pensionato vive, e l'export contiene 110 entità (107 province attuali + 2 PA + 3 ex-province sarde da aggregare). I dataset [2] (regime di liquidazione) e [3] (serie storica) adottano invece la **provincia della sede INPS** che gestisce amministrativamente la posizione previdenziale: l'unità territoriale è in questo caso definita dal centro di erogazione, e l'export contiene 106 entità con aggregazioni diverse — `CAGLIARI E SUD SARDEGNA` accorpa due province AGID in una sola sede, la sede di `FORLI` copre il territorio di Forlì + Cesena ma è etichettata solo come "Forlì", `VERBANIA` è la label INPS della sede di Verbano-Cusio-Ossola. Il dataset [4] è nazionale e non ha dimensione territoriale, quindi non pone il problema.

Concettualmente, **provincia di residenza** e **provincia della sede INPS** misurano fenomeni diversi: la prima dice "dove vive chi riceve la pensione", la seconda dice "quale ufficio INPS la eroga". Non sono ricavabili l'una dall'altra: l'INPS non pubblica la tabella di transito dei singoli titolari, né un dataset open che permetta di mappare 1-a-1 i due assi. **Per il progetto IDPT accettiamo questa asimmetria come limite metodologico dichiarato**: non avendo la composizione regime × residenza, usiamo la composizione regime × sede del cubo 2 e la attribuiamo (al netto degli aggregati di sede sopra elencati) alle province AGID corrispondenti. È un'approssimazione ragionevole perché la maggioranza dei pensionati riceve la pensione tramite la sede INPS della propria provincia di residenza, ma l'imperfezione esiste e va segnalata al lettore del grafo. Conseguenza operativa per la modellazione semantica: nella sez. 4 introdurremo una classe propria `idpt:SedeINPS` distinta dalle 107 `clv:Province` AGID, con due property di relazione (`idpt:correspondsToProvinceAGID` per il caso 1-a-1 e `idpt:aggregatesProvince` per il caso 1-a-N di Cagliari + Sud Sardegna). Questo modo di modellare, invece di "appiattire" la sede sulla residenza e nascondere la disomogeneità, preserva i due assi come entità semantiche distinte e rende l'asimmetria interrogabile via SPARQL — pattern coerente con l'obiettivo di onestà rappresentazionale che attraversa il progetto.

### 2.2 ISTAT

Le tre estrazioni ISTAT provengono dal nuovo databrowser `esploradati.istat.it`, e sono pubblicate sotto la stessa licenza **Creative Commons Attribuzione 3.0 Italia** ([CC-BY 3.0 IT](https://creativecommons.org/licenses/by/3.0/it/)), come dichiarato dalle [note legali ISTAT](https://www.istat.it/note-legali/). L'attribuzione richiesta è "Fonte: ISTAT". Tutti gli export adottano il formato SDMX-like descritto nel cappello di sezione, con il quoting CSV non standard `quotechar="'"` che richiederà gestione esplicita nella pipeline.

Una curiosità di rilievo per il framing LOD del progetto: **lo stesso ente, in due cubi diversi, adotta due codifiche territoriali differenti per le Province Autonome di Trento e Bolzano**. Il cubo "Rilevazione Forze di Lavoro" (occupati, dataset [5]) usa la codifica NUTS-2 `ITD1`/`ITD2`, mentre il cubo "Indicatori demografici provinciali" (dataset [6] e [7]) usa la codifica NUTS-3 corretta `ITD10`/`ITD20`, coerente con il vocabolario AGID. La disomogeneità interna ai rilasci ISTAT è un esempio concreto di perché la pratica LOD ha bisogno di un'ancora semantica esterna (AGID OntoPiA, in questo caso) che riconcilii a posteriori identificatori istituzionali concorrenti — pattern documentato nella sez. 4 con il sidecar `nuts_aliases.ttl`. Una seconda asimmetria, sempre lato ISTAT, riguarda le 4 province moderne senza NUTS-3 Eurostat ufficiale (Monza-Brianza, Fermo, BAT, Sud Sardegna): per esse i CSV ISTAT usano codici proprietari `IT108`, `IT109`, `IT110`, `IT111` — fake-NUTS non riconosciuti da AGID, che modelleremo con `skos:exactMatch` (sez. 4) per onestà semantica.

**[5] Occupati per provincia, media annua 2025** — file `istat_occupati_provincia_2025_v1.csv`. Databrowser: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0500LAB,1.0/LAB_OFFER/LAB_OFF_EMPLOY/DCCV_OCCUPATIT1/DCCV_OCCUPATIT1_PROVDATA/IT1,150_938_DF_DCCV_OCCUPATIT1_21,1.0>. **Filtri impostati**: ultimo anno disponibile (2025, media annua) — i dati ISTAT delle Forze di Lavoro a livello provinciale sono pubblicati solo come media annua, non trimestralmente; solo province (escluse aree geografiche aggregate); aggregato per sesso (valore "totale"). **Composizione**: 107 entità (105 province standard in NUTS-3 + 2 PA in NUTS-2); 1 misura, "occupati totali 15–89 anni in migliaia". Il disallineamento temporale rispetto allo snapshot INPS 1.1.2026 è di pochi mesi: il fatto che la media annua 2025 sia disponibile a maggio 2026 è una "buona sorpresa" del rilascio ISTAT, e rende l'IDPT 2026 calcolabile con denominatori sufficientemente recenti. **Ruolo nell'IDPT**: denominatore della dimensione D1 (occupati per provincia); alimenta il cubo 5 del grafo.

**[6] Indicatori demografici provinciali, 1.1.2026** — file `istat_indicatori_demografici_provincia_2026_v1.csv`. Databrowser: <https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,POP,1.0/POP_POPULATION/DCIS_INDDEMOG1/IT1,22_293_DF_DCIS_INDDEMOG1_1,1.0>. **Filtri impostati**: anno di riferimento 1.1.2026 (dato stimato preliminare; il definitivo esce mesi dopo). L'allineamento temporale con lo snapshot INPS è perfetto. **Composizione**: 107 entità complete, con PA Trento e Bolzano in NUTS-3 corretto come segnalato sopra; 6 indicatori derivati per i quali la stessa code-list SKOS del progetto riusa le sigle ISTAT native come `skos:notation`: `POP014` (popolazione 0–14 anni, %), `POP1564` (15–64, %), `POP65OVER` (65+, %), `OLDAGEDEPR` (indice di dipendenza degli anziani), `AGEINDEX` (indice di vecchiaia), `MEANAGEP` (età media). **Ruolo nell'IDPT**: nessuna componente del numero IDPT, ma variabili di contesto per la narrativa territoriale del grafo. Alimenta il cubo 6 insieme al dataset [7].

**[7] Tasso di natalità e speranza di vita a 65 anni, 2025** — file `istat_natalita_speranza_di_vita_2025_v1.csv`. Stesso databrowser del dataset [6]. **Filtri impostati**: 2 indicatori del cubo "Indicatori demografici" non disponibili al 1.1.2026 perché misurati su base annua chiusa, quindi rilasciati con riferimento 2025. **Composizione**: 107 entità, 2 indicatori — `BIRTHRATE` (tasso di natalità per mille abitanti, dato provvisorio) e `LIFEEXP65T` (speranza di vita a 65 anni, dato stimato). Il disallineamento temporale è ininfluente perché si tratta di variabili di contesto. **Ruolo narrativo**: `LIFEEXP65T` è particolarmente utile come variabile di "durata della pensione" provincia per provincia, con un noto gradiente Nord/Sud (Bolzano sopra 22 anni, province meridionali sotto 20). Confluisce nel cubo 6 con il dataset [6] — i due dataset ISTAT demografici sono unificati in un unico cubo per coerenza di fonte, granularità e natura degli indicatori.

### 2.3 MEF

**[8] Redditi e principali variabili IRPEF su base comunale, anno di imposta 2024** — file `mef_redditi_irpef_comune_2024_v1.csv`. Dipartimento delle Finanze del Ministero dell'Economia e delle Finanze. **URL diretto del CSV (ZIP)**: <https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_2024.zip?d=1615465800>. **Pagina indice degli open data fiscali comunali**: <https://www1.finanze.gov.it/finanze/analisi_stat/public/index.php?search_class%5b0%5d=cCOMUNE&opendata=yes>. **Pagina descrittiva ufficiale "Open data comunale IRPEF"**: <https://www.finanze.gov.it/it/statistiche-fiscali/open-data-comunale-principali-variabili-irpef/>. **Licenza**: **Creative Commons Attribuzione 3.0** ([CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/)) — la versione *generica* (Unported), non la versione "Italia"; la pagina ufficiale del MEF dichiara letteralmente *"I dati sono rilasciati con licenza Creative Commons 3.0 e distribuiti utilizzando le tecnologie digitali correnti e gli standard Web più diffusi"*.

**Composizione**: 7.897 comuni italiani × 53 colonne — per ogni voce di reddito una doppia colonna "Frequenza" (numero dichiaranti) e "Ammontare in euro" (totale). **Granularità**: comunale, riaggregabile a livello provinciale tramite il campo nativo `Sigla Provincia` con un semplice group-by. **Granularità temporale**: anno di imposta 2024 (redditi prodotti nel 2023, dichiarati nel 2024), disallineato di circa tre anni dallo snapshot INPS 1.1.2026 — limite metodologico minore, dichiarato come tale nel report. **Variabili effettivamente utilizzate** (5 su 53): `v2` Reddito da lavoro dipendente e assimilati, `v4` Reddito da lavoro autonomo, `v5` Reddito imprenditore in contabilità ordinaria, `v6` Reddito imprenditore in contabilità semplificata, `v7` Reddito da partecipazione — componenti del **monte redditi da lavoro** che costituisce il denominatore della dimensione D2 dell'IDPT. Una sesta variabile, `v3` Reddito da pensione, è impiegata come **validazione cross-fonte** per triangolare il monte pensioni del dataset INPS [1]. Anomalie tecniche da risolvere nella sez. 3: il "NA-bug" di `pandas` sui 92 comuni della provincia di Napoli con `Sigla="NA"` interpretata come `NaN`; una riga sentinella con `Codice Istat=0`, `Sigla=0`, `Regione=Mancante/errata` (placeholder MEF per dichiarazioni con territorio non assegnato) da filtrare prima dell'aggregazione. **Ruolo nell'IDPT**: denominatore di D2 dopo aggregazione `Sigla Provincia` → 107 province; alimenta il cubo 7.

Va menzionato che lo stesso URL della pagina indice MEF distribuisce, accanto al CSV, un file RDF/XML con lo stesso contenuto formale. **Quel file non è stato usato come fonte di dati**, ma è conservato nella cartella `data/` del repository (`mef_redditi_irpef_comune_2024_v1.rdf`) come **caso di studio negativo** della pratica LOD nelle PA italiane: il namespace dichiarato è `http://www1.finanze.gov.it/fakeurl#` (letteralmente "fakeurl"), le variabili sono nominate `v1..v22` senza URI semantiche, il modello è "wide" senza alcuna `qb:Observation`, la data di aggiornamento è malformata (`2026-23-04`, mese 23). La discussione completa è nella sez. 4, in chiusura, come contrappunto al lavoro di modellazione ben fatto realizzato altrove nel progetto.

### 2.4 Ancore semantiche AGID + geometrie ausiliarie (licenze CC-BY 4.0 e CC-BY)

Il progetto si appoggia a due artefatti AGID per l'ancoraggio semantico territoriale e a un terzo artefatto open per il rendering cartografico. Le tre risorse non sono "dataset statistici" nel senso degli otto precedenti — non veicolano misure — ma sono comunque fonti pubbliche da dichiarare con licenza e URL canonico.

**[9] Vocabolario Controllato Province d'Italia — AGID OntoPiA** — file `data/provinces.ttl`. URL canonico del vocabolario: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces>. URL del file Turtle raw: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/provinces/provinces.ttl>. **Licenza**: **Creative Commons Attribuzione 4.0 Internazionale** ([CC-BY 4.0](https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40), codice AGID `A21_CCBY40`) — licenza verificata leggendo direttamente le triple `dct:license <https://w3id.org/italia/controlled-vocabulary/licences/A21_CCBY40>` presenti nel file TTL stesso. **Contenuto per provincia**: URI canonica, `skos:prefLabel` IT/EN, `skos:notation` (codice ISTAT a 3 cifre), `clv:acronym` (sigla auto a 2 lettere), `owl:sameAs` verso codice NUTS Eurostat (eventualmente multipli per province con NUTS storici), `clv:situatedWithin` verso la regione di appartenenza, `clv:hasRankOrder` (3 per provincia ordinaria, 4 per città metropolitana). Dimensioni: 107 province istanziate, 116 link `owl:sameAs` verso NUTS (9 codici NUTS storici extra preservati come `owl:sameAs` multipli per le 6 province polinominate: Bergamo, Udine, Sassari, Nuoro, Rimini, Sud Sardegna), circa 2.712 triple totali. **Ruolo nel grafo IDPT**: ancora semantica primaria. Tutte le 107 province del progetto sono identificate con le URI canoniche AGID; il pattern OntoPiA garantisce multi-typing gratuito (`clv:Province` + `clv:AdminUnitComponent` + `skos:Concept` + `clv:Feature`), eliminando la necessità di modellare classi territoriali proprie. Il vocabolario è inoltre il pivot del linking esterno: dai suoi `owl:sameAs` nativi verso NUTS si arriva transitivamente al LOD Cloud europeo, e i 107 `owl:sameAs` aggiuntivi materializzati dal progetto verso DBpedia (sez. 4) completano la quintupla identità di ogni provincia.

**[10] Vocabolario Controllato Regioni d'Italia — AGID OntoPiA** — file `data/regions.ttl`. URL canonico: <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/regions>. URL del file Turtle raw: <https://raw.githubusercontent.com/italia/dati-semantic-assets/master/VocabolariControllati/territorial-classifications/regions/regions.ttl>. Licenza identica al vocabolario delle province: **CC-BY 4.0** (verificata leggendo le triple `dct:license` del file). Struttura analoga, 20 regioni, circa 477 triple. **Ruolo nel grafo IDPT**: ancora di livello superiore per le query SPARQL di aggregazione regionale (es. la query di demo `q10_regime_retributivo_geo.rq` che calcola la percentuale di regime retributivo per regione).

**[11] Geometrie provinciali ISTAT, ridistribuite da Openpolis in GeoJSON** — file `data/limits_IT_provinces.geojson`. **URL download diretto**: <https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_provinces.geojson>. **Repository**: <https://github.com/openpolis/geojson-italy>. **Licenza**: **CC-BY** ereditata dalla licenza dei confini amministrativi ISTAT originali, mantenuta esplicitamente da Openpolis sui file ridistribuiti. L'attribuzione richiesta è doppia (ISTAT + Openpolis). **Origine**: i confini amministrativi ufficiali ISTAT sono ridistribuiti dal team Openpolis in formato GeoJSON nella proiezione geografica WGS84, con tre versioni a diversa granularità (province, regioni, comuni). Il match province IDPT ↔ poligoni avviene sul campo `codice_istat` integer. **Ruolo nel progetto**: layer cartografico per le mappe coropletiche Folium discusse nella sez. 5 (`output/visualizations/idpt_map.html`, `output/visualizations/idpt_components.html`). **Ruolo nel grafo RDF**: nessuno — il file di geometrie non entra fra le triple del grafo, è puro materiale di rendering. È documentato qui per completezza di provenance e licenza del deliverable visualizzativo.

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

L'elaborazione è stata realizzata interamente con **macrorefine**, libreria Python di data cleaning a pipeline sviluppata appositamente per il progetto. macrorefine ha un'architettura concettualmente semplice ma rigorosa: un `Dataset` *immutabile* che incapsula un DataFrame `pandas`, una `Pipeline` *fluente* che concatena `Step` componibili, una `Recipe` riusabile che è una fabbrica di pipeline parametrizzate per uno specifico CSV sorgente. Ogni `Step` produce un nuovo `Dataset` (mai mutazione in-place) e registra un `StepRecord(name, params, metrics)` in una `History` che viene serializzata come sidecar `*.history.json` accanto al CSV pulito. Il sidecar contiene, per ogni esecuzione: nome dello step, parametri passati, timestamp UTC, metriche di output (es. righe lette / righe scritte / righe scartate, conteggio di match riusciti contro vocabolari esterni, totali preservati nelle aggregazioni). Questo audit trail strutturato è precisamente la "materia prima" che la sez. 4 trasformerà in lineage PROV-O minimale del grafo RDF.

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

Questa sotto-sezione racconta come ciascuna anomalia citata nella sez. 2 è stata risolta a livello di codice, in ordine di apparizione nei CSV.

**Numeri in formato italiano (4 CSV INPS).** I CSV dell'Osservatorio statistico INPS adottano la convenzione italiana — punto come separatore delle migliaia e virgola come separatore decimale (`1.234,56`), con celle vuote marcate `-`. Lo step `ParseItalianNumbers` è implementato come `ColumnStep` (applicato cella per cella su una lista di colonne specificate): regex `^[\d.,\s\-]+$` per identificare i numeri, rimozione dei punti di migliaia, sostituzione della virgola decimale con punto, conversione a `float`, mappatura della sentinella `-` a `NaN`. La scelta di non usare `pandas.to_numeric` con `decimal=","` è motivata: il default `pandas` non gestisce la sentinella `-` (che diventerebbe parsing error), e soprattutto non distingue il `-` "valore soppresso per privacy" (semanticamente diverso da `NaN` di valore mancante) da un eventuale errore di import. Con uno step custom abbiamo il pieno controllo: la sentinella `-` viene tracciata nelle metriche `StepRecord` come `count_suppressed`, riportata nel sidecar `*.history.json`, e successivamente mappata a `obsStatus=M` (Missing) o a osservazione omessa nelle Recipe finali.

**Template OLAP sporco (CSV INPS).** I CSV esportati dal cubo OLAP INPS contengono righe non tabellari nell'header e nel footer (titolo del cubo, descrizione dei filtri impostati, fonte, data di estrazione) e righe di totale alla fine. `pandas.read_csv` su questi file applica un'inferenza automatica delle colonne che fallisce — durante lo sviluppo della Recipe del cubo 1 abbiamo verificato che `pandas` perde 28 righe su un CSV INPS sporco senza apparente errore. La lettura è stata quindi affidata al modulo standard `csv.reader` con scansione esplicita: salta le righe iniziali finché non incontra l'header tabellare atteso (rilevato via match su un nome colonna noto), legge le righe successive finché non incontra la riga "Totale" (che viene scartata), filtra esplicitamente le 7 righe di aggregati continentali (`Europa`, `Asia`, `Africa`, `America Settentrionale`, `America Centrale`, `America Meridionale`, `Oceania`) che sono fuori dal perimetro IDPT (pensioni con residenza italiana).

**Quoting CSV non standard (CSV ISTAT).** I CSV esportati dal databrowser `esploradati.istat.it` adottano un quoting non standard: l'apice singolo come `quotechar` invece del doppio apice. La motivazione tecnica è la presenza nei nomi di provincia di apostrofi (`Valle d'Aosta`, `Reggio nell'Emilia`) che con doppio quote dovrebbero essere raddoppiati ma che ISTAT preferisce gestire con un quoting alternativo. Il default di `pandas.read_csv` (`quotechar='"'`) interpreta i campi come stringhe non quotate e li spezza alla prima virgola interna; passare `quotechar="'"` a `pandas` produce un errore di parser perché alcune righe contengono apici singoli non quotati (per gli accenti tipografici). La soluzione adottata è un helper `read_istat_csv()` basato su `csv.reader` stdlib con `quotechar="'"` esplicito, riutilizzato dalle Recipe dei cubi 5 e 6.

**NA-bug pandas su CSV MEF.** Quando `pandas.read_csv` incontra un valore stringa `NA` su una colonna `Sigla Provincia`, lo converte di default a `numpy.nan` perché `NA` è uno dei valori di default `na_values`. **Conseguenza**: i 92 comuni della provincia di Napoli (sigla = `NA`) perdono il loro identificatore territoriale subito dopo la lettura del CSV, e l'aggregazione per provincia produce un cluster spurio "comuni senza provincia". Il fix è una riga di codice — `pandas.read_csv(path, keep_default_na=False)` — ma è esattamente il tipo di bug silenzioso che si annida nelle pipeline open data se la convenzione di nomenclatura territoriale non è verificata empiricamente. Il MEF distribuisce inoltre **una riga sentinella** con `Codice Istat=0`, `Sigla=0`, `Regione=Mancante/errata` come placeholder per dichiarazioni con territorio non assegnato: viene filtrata esplicitamente dalla Recipe del cubo 7 prima dell'aggregazione `Sigla Provincia` → URI AGID.

**Aggregazione retroattiva delle ex-province sarde.** Il CSV INPS della serie storica [3] mostra una discontinuità territoriale: dal 2005 al 2011 sono presenti righe per le 4 ex-province sarde (Olbia-Tempio, Carbonia-Iglesias, Medio Campidano, Ogliastra), dal 2012 al 2026 quelle righe scompaiono e i loro valori sono assorbiti dalle sedi INPS attuali (Sassari, Cagliari-e-Sud-Sardegna, Nuoro). Per evitare due policy diverse fra snapshot 2026 e serie storica, lo step `AggregateSardiniaProvinces` lavora in due modalità: in modalità **snapshot** (cubo 1) aggrega le 3 ex-province che compaiono nel CSV 2026 (Carbonia-Iglesias e Medio Campidano → Sud Sardegna 111, Olbia-Tempio → Sassari 090, Ogliastra → Nuoro 091) preservando il totale al singolo intero; in modalità **mark serie storica** (cubo 3) ricostruisce le 84 osservazioni 2005-2011 sulle 3 sedi attuali e le marca con `obsStatus=E` (Estimated) + `prov:wasDerivedFrom` esplicito nella tabella di output, per il successivo passaggio RDF. Le somme su conteggi sono dirette, le medie sugli importi sono pesate sul numero di pensioni (`weight_pairs`) per non distorcere gli aggregati.

**Aggregazione 7.897 comuni MEF → 107 province.** Lo step `AggregateMEFRedditiByProvincia` esegue un `groupby('Sigla Provincia').sum()` sulle 10 colonne di interesse (5 voci × 2 misure: `Frequenza` + `Ammontare in euro`), seguito da un unpivot wide→long che ribalta le 5 voci `v2/v4/v5/v6/v7` da colonne a righe della code-list `idpt:voci-reddito-mef`. Il match Sigla → URI AGID avviene poi tramite `LinkProvinceToAGID_bySigla`, che usa `clv:acronym` come chiave esatta — zero ambiguità perché ogni sigla a 2 lettere è univoca nel vocabolario AGID. Il risultato sono 535 righe (107 province × 5 voci) pronte per l'emissione `qb:Observation` del cubo 7.

**Riconciliazione nominale INPS → AGID.** Il `LinkProvinceToAGID_byName` risolve il caso più delicato: i CSV INPS portano i nomi delle province in italiano, talora in maiuscolo, con varianti tipografiche storiche e abbreviazioni che non corrispondono allo `skos:prefLabel@it` del vocabolario AGID. La pipeline interna è a quattro stadi: (1) normalizzazione (lowercase, NFKD con drop dei combining accent, fix spazi attorno ai trattini, collasso whitespace multipli); (2) match diretto sul nome AGID normalizzato; (3) dizionario manuale `SETTLED_ALIASES` per le anomalie strutturali documentate. 
Le 13 anomalie nominali strutturali del confronto INPS vs AGID, materializzate come entry del dizionario, sono:

| Nome INPS originale (CSV)             | Nome AGID (`skos:prefLabel@it`) | Codice ISTAT | Origine                                                          |
| ------------------------------------- | ------------------------------- | ------------ | ---------------------------------------------------------------- |
| `Aosta`                               | Valle d'Aosta/Vallée d'Aoste    | 007          | residenza                                                        |
| `Barletta -Andria-Trani`              | Barletta-Andria-Trani           | 110          | residenza (fix spazio)                                           |
| `Forli' -Cesena`                      | Forlì-Cesena                    | 040          | residenza (fix accento + spazio)                                 |
| `Massa -Carrara`                      | Massa-Carrara                   | 045          | residenza (fix spazio)                                           |
| `Provincia Autonoma di Bolzano/Bozen` | Bolzano/Bozen                   | 021          | residenza                                                        |
| `Provincia Autonoma di Trento`        | Trento                          | 022          | residenza                                                        |
| `Reggio Calabria`                     | Reggio di Calabria              | 080          | residenza                                                        |
| `Reggio Emilia`                       | Reggio nell'Emilia              | 035          | residenza                                                        |
| `Verbano -Cusio-Ossola`               | Verbano-Cusio-Ossola            | 103          | residenza (fix spazio)                                           |
| `VERBANIA`                            | Verbano-Cusio-Ossola            | 103          | regime sede / serie storica (maiuscolo)                          |
| `FORLI`                               | Forlì-Cesena                    | 040          | regime sede / serie storica (maiuscolo, senza accento)           |
| `BOLZANO`                             | Bolzano/Bozen                   | 021          | regime sede / serie storica (maiuscolo)                          |
| `TRENTO`                              | Trento                          | 022          | regime sede / serie storica (maiuscolo)                          |
| `PESARO -URBINO`                      | Pesaro e Urbino                 | 041          | regime sede (variante `-` vs ` e `, scoperta in Fase 1 blocco 3) |

L'ultima riga della tabella è una scoperta sopravvenuta durante lo sviluppo che vale la pena raccontare: il vocabolario AGID modella "Pesaro e Urbino" con il connettore congiuntivo (" e "), mentre il cubo INPS regime di liquidazione usa l'abbreviazione con trattino. La pipeline di normalizzazione li rende rispettivamente `pesaro e urbino` e `pesaro-urbino`, mismatch a livello di stringa risolto solo aggiungendo l'entry esplicita al dizionario. Le metriche `StepRecord` distinguono `matched_via_direct`, `matched_via_alias`, `matched_via_fuzzy` per l'audit a posteriori.

**Stima dell'importo annuo soppresso (cubi 2 e 3).** Il cubo OLAP INPS sopprime la statistica `Importo complessivo annuo` per privacy quando si scende a granularità provincia × regime (cubo 2) o sede × anno (cubo 3); abbiamo già menzionato il problema nella sez. 2. Lo step `EstimateAnnualAmount` ricostruisce l'importo come `numero_pensioni × importo_medio_mensile × 13` (12 mensilità più tredicesima), aggiunge una colonna `_status="estimated"`, e popola una colonna `_derived_from` con la coppia delle due osservazioni primarie da cui la stima è derivata (necessaria per emettere `prov:wasDerivedFrom` nella sez. 4). Il moltiplicatore 13 è una convenzione INPS pubblica per le pensioni annue; il pattern di derivazione esplicita preserva la separazione semantica fra dato primario e stima.

**Plan B GDP — la trasformazione più articolata.** Lo step `ProjectGDPRegimeComposition` realizza in due fasi quanto descritto nella sez. 2.1 sul dataset [4]. Fase 1: legge il CSV decorrenza GDP nazionale (46 righe da "anteriore al 31/12/1980" al 2025), applica l'euristica anno-di-decorrenza → regime di liquidazione e produce 4 percentuali nazionali di composizione regime GDP. Le soglie dell'euristica sono calibrate sulle due grandi riforme previdenziali italiane: chi è andato in pensione prima del 1996 è interamente in regime retributivo puro (sistema pre-Riforma Dini 1995); chi è andato in pensione fra il 1996 e il 2011 è in regime misto-Dini (retributivo per l'anzianità maturata fino al 1995, contributivo per il resto); chi è andato in pensione dal 2012 in poi è in regime misto-Fornero (retributivo fino al 2011, contributivo per il resto) o, raramente, contributivo puro (per chi ha iniziato a contribuire dopo il 1996, caso ancora rarissimo nel 2026 perché l'età pensionabile non è stata ancora raggiunta). Sul CSV reale, queste percentuali si attestano a 13,85% Retributivo + 34,23% Misto-Dini + 51,92% Misto-Fornero + 0% Contributivo-puro (la quota Contributivo-puro è praticamente assente perché chi è entrato nel mondo del lavoro dopo l'1/1/1996 non è ancora arrivato all'età pensionabile nel 2026). Fase 2: legge via SPARQL il cubo 1 già emesso, estrae per ogni provincia il numero di pensioni `gestione-pubblici`, moltiplica per le 4 percentuali nazionali, produce 428 osservazioni stimate (107 province × 4 regimi). Il totale per provincia è preservato al singolo intero; il totale nazionale sommato sulle 107 province (3.159.266) differisce di esattamente **11.991 pensioni** dal totale GDP del cubo 4 (3.171.257) — differenza interamente giustificata dalle pensioni Pubblici residenti all'estero (Europa 7.833 + Asia 381 + Africa 1.941 + America Settentrionale 745 + America Centrale 300 + America Meridionale 607 + Oceania 184 = 11.991), che il cubo 1 esclude per coerenza con la decisione "pensioni estere fuori dall'IDPT". Validazione esatta al singolo intero, ricostruzione riproducibile, e onestà metodologica: la differenza è dichiarata, non nascosta.

### 3.4 Le quattro Recipe a pipeline lineare — cubi 1, 5, 6, 7

Una `Recipe` macrorefine è la fabbrica che orchestra gli step custom per produrre una specifica tabella pulita pronta per l'emissione `qb:Observation`. Le quattro Recipe descritte in questa sottosezione hanno pipeline lineari: stile A qb multi-measure, nessuna proiezione, nessuna aggregazione retroattiva, nessuna stima di misura.

**Cubo 5 (occupati ISTAT)** — `scripts/recipes/cubo5_occupati_istat.py`. Pipeline minimale: `RenameColumns({"REF_AREA": "ref_area", "Osservazione": "n_occupati"})` → `CastTypes({"n_occupati": "float"})` → `LinkProvinceToAGID_byNUTS(nuts_column="ref_area", provinces_ttl="data/provinces.ttl", nuts_aliases_ttl="output/mappings/nuts_aliases.ttl")`. Output: 107/107 province matchate, 107 osservazioni di output, una misura primaria (`numeroOccupati`). Recipe "Hello World" che è servita a validare il pattern `EmitQbObservations` per i tre cubi successivi.

**Cubo 7 (redditi MEF)** — `scripts/recipes/cubo7_redditi_mef.py`. Pipeline: `read_csv(keep_default_na=False)` → `DropRows` della sentinella `Codice Istat=0` → `AggregateMEFRedditiByProvincia` (group-by sigla + unpivot 5 voci) → `LinkProvinceToAGID_bySigla`. Output: 535 osservazioni (107 province × 5 voci di reddito), 107/107 sigle matchate.

**Cubo 6 (indicatori demografici ISTAT)** — `scripts/recipes/cubo6_indicatori_demografici_istat.py`. Pipeline: `read_istat_csv` con `quotechar="'"` → unione dei due CSV (indicatori 2026 + natalità/speranza vita 2025, gestiti come due input separati con `annoRiferimento` distinto) → `LinkProvinceToAGID_byNUTS` (gestisce le PA in NUTS-3 corretto dal cubo demografico) → `EnrichWithStaticMapping` per arricchire ogni riga con URI dell'indicatore SKOS (`POP014` → `idpt:ind-pop014`, ecc.) e unità di misura SDMX (`%`, `anni`, `per mille`). Output: 856 osservazioni (642 per il 2026 + 214 per il 2025), validation 7/7 verde.

**Cubo 1 (vigenti residenza INPS)** — `scripts/recipes/cubo1_vigenti_residenza.py`. La più complessa delle "facili" per via dei due step custom INPS-specifici e dell'aggregazione Sardegna. Pipeline: `csv.reader` stdlib per lettura template OLAP sporco → `ParseItalianNumbers` su tutte le colonne numeriche INPS → `AggregateSardiniaProvinces` (modalità snapshot, 8 → 5 nomi sardi) → `UnpivotINPSPensioniVigenti` (5 gestioni × 3 misure wide→long) → `LinkProvinceToAGID_byName`. Output: 535 osservazioni (107 province × 5 gestioni — incluso `gestione-totale` aggregato), 505 direct + 30 alias matched dalla pipeline a 4 stadi.

### 3.5 Le quattro Recipe con stile B qb e pattern di derivazione — cubi 2, 3, 4, 9

Le quattro Recipe rimanenti hanno pipeline più articolate: adottano lo stile B qb (`qb:measureType` come dimensione, una osservazione per misura), oppure includono la stima dell'importo annuo soppresso, l'aggregazione retroattiva sarda, la proiezione Plan B sulla composizione regime GDP.

**Cubo 4 (decorrenza GDP nazionale)** — `scripts/recipes/cubo4_decorrenza_gdp.py`. Pipeline lineare ma con una decisione metodologica esplicita: la riga "Decorrenza anteriore al 31/12/1980" viene aggregata sull'anno 1980 con marcatura `obsStatus=E` (Estimated) — invece di scartarla o di trattarla come "anno 0", il pattern uniforme del progetto è preservato. Output: 46 osservazioni (45 status=A primarie + 1 status=E aggregata).

**Cubo 9 (Plan B GDP projected)** — `scripts/recipes/cubo9_plan_b_gdp_projected.py`. La prima materializzazione su scala del pattern "osservazione derivata": 428 osservazioni (107 province × 4 regimi) tutte con `obsStatus=E` e **doppia** `prov:wasDerivedFrom` — una verso l'osservazione del cubo 1 con `gestione=Pubblici` per quella provincia, l'altra verso il `qb:DataSet` del cubo 4 da cui si ricava la composizione regime nazionale. Helper SPARQL `_load_pubblici_per_provincia(cubo1_ttl)` per leggere le 107 quote provinciali GDP dal cubo 1 appena emesso. Output: 428 osservazioni, 856 link `prov:wasDerivedFrom` totali (2 per ogni obs). Validazione esatta della discrepanza 11.991 con il cubo 4 nazionale.

**Cubo 2 (regime sede INPS)** — `scripts/recipes/cubo2_regime_sede.py`. Prima implementazione dello **stile B qb**: la dimensione `qb:measureType` distingue per ogni osservazione quale misura sta esprimendo (`numeroPensioni`, `importoMedioMensile`, `importoAnnuoComplessivo`); una stessa coppia (sede, regime) genera 3 osservazioni distinte. Lo step `UnpivotINPSRegimeSede` ribalta wide→long le 106 sedi × 4 regimi × 2 misure primarie esplicite del CSV (`numeroPensioni`, `importoMedioMensile`) verso 106 × 4 × 2 = 848 osservazioni primarie con `obsStatus=A`. Quindi `EstimateAnnualAmount` ricostruisce per ogni coppia (sede, regime) l'`importoAnnuoComplessivo` come `n × media × 13`, emettendo 106 × 4 = 424 osservazioni con `obsStatus=E` e `prov:wasDerivedFrom` verso le due osservazioni primarie da cui la stima è derivata. La gestione "Pubblici" è esclusa per costruzione dal cubo OLAP INPS, quindi rimossa anche dal DSD del cubo 2 (decisione coerente con la realtà del dato). Linking sede INPS via `LinkSedeINPS`, che emette contestualmente il sidecar `output/mappings/inps_to_agid.ttl` con le 106 istanze `idpt:SedeINPS`. Output: 1.272 osservazioni totali (848 primarie + 424 stimate), 848 link `prov:wasDerivedFrom`.

**Cubo 3 (serie storica sedi INPS)** — `scripts/recipes/cubo3_serie_storica_sede.py`. Stile B qb anch'esso, ma su 29 anni invece che 4 regimi. Pipeline: csv.reader stdlib per template OLAP sporco → `ParseItalianNumbers` → `UnpivotINPSSerieStorica` (29 anni × 3 measureType, scarto delle righe `-` per BAT, Fermo, Monza pre-2009 — `obsStatus=M` Missing implicito tramite omissione di osservazione) → `AggregateSardiniaProvinces` in modalità `mark_serie_storica` (84 osservazioni 2005-2011 sulle 3 sedi sarde compositive marcate `obsStatus=E`) → `EstimateAnnualAmount` per l'importo annuo ricostruito → `LinkSedeINPS`. Output: 9.105 osservazioni totali — 5.986 status=A primarie + 3.035 status=E importo annuo stimato + 84 status=E aggregazione Sardegna retroattiva — coperte da una sola DSD coerente.

### 3.6 Audit trail e validazione tabellare

L'intera elaborazione è coperta da **172 unit test pytest** (`macrorefine/tests/`) che esercitano gli step custom su micro-fixture rappresentative e da test di integrazione end-to-end sui CSV reali del progetto. Le verifiche di integrazione sono particolarmente rilevanti per la riproducibilità: per il cubo 1 viene controllato che la pipeline porti 110 → 107 entità territoriali dopo l'aggregazione sarda e che 107/107 vengano risolte da `LinkProvinceToAGID_byName`; per il cubo 7 che 7.897 comuni MEF vengano aggregati su 107 province con preservazione esatta delle 5 voci di reddito; per il cubo 9 che la conservazione dei totali GDP per provincia mostri `max diff = 0` rispetto al cubo 1 in input.

I sidecar `*.history.json` prodotti accanto a ogni CSV pulito registrano, oltre al tracciamento step-per-step già descritto, l'identità del CSV di input (path + hash SHA256), il commit hash di macrorefine al momento dell'esecuzione, l'identità dell'agente (`Roberto Bruno` come `prov:Agent` configurato nelle Recipe) e i timestamp UTC di inizio e fine pipeline. Sono questi metadati, esistenti già a livello tabellare grazie alla scelta architetturale di macrorefine, che la sez. 4 monterà come triple PROV-O minimali nel grafo RDF (`prov:wasDerivedFrom` su ogni osservazione stimata + `dcterms:source` sui `qb:DataSet`). La distinzione "audit trail tabellare" (qui) vs "lineage semantico" (sez. 4) è meno una distinzione di sostanza che di livello di astrazione: gli stessi metadati di provenance esistono a entrambi i livelli, con il livello RDF che li espone come triple interrogabili via SPARQL.

Le 172 verifiche tabellari sono solo il primo livello di validazione del progetto. Sopra di loro, nella sez. 4, troveranno posto i 33 check SPARQL post-emissione (10 sui vocabolari + 9 sui cubi + 14 sul DCAT-AP_IT del deliverable), che validano la conformità del grafo RDF rispetto al modello ontologico atteso. Le due famiglie di test sono complementari e ortogonali: i test tabellari verificano che la pipeline produca le tabelle corrette; i test SPARQL verificano che il grafo emesso dalle tabelle sia conforme allo schema ontologico atteso.

---

## 4. Trasformazione dei dataset — modellazione ontologica e RDF

Con la sezione 4 entriamo nel cuore del progetto: la **pratica del Linked Open Data**. Le tabelle pulite prodotte dalla sezione 3 vengono qui modellate ontologicamente e materializzate come grafo RDF — passaggio in cui ogni decisione tecnica si traduce in una decisione semantica e quindi pesa sul giudizio "LOD ben fatto vs LOD di facciata". Tre principi guidano l'intera modellazione: **massimo riuso di vocabolari standard** (9 vocabolari riusati a fronte di una sola classe propria su tutto il grafo); **un cubo per fenomeno omogeneo** (9 `qb:DataSet` separati invece di un cubo unico "tuttologo" che sarebbe stato un anti-pattern conclamato); **pattern uniforme per le osservazioni derivate** (`sdmx-attribute:obsStatus sdmx-code:obsStatus-E` + `prov:wasDerivedFrom` applicato in 4 punti del grafo, su un totale di 4.399 osservazioni stimate).

Il risultato di questa fase è un grafo RDF di circa **117.000 triple** distribuite su **6 grafi nominati** in Apache Jena Fuseki: `graph:agid` (vocabolari controllati territoriali, read-only), `graph:vocabularies` (classi, property, code-list proprie), `graph:linking` (i tre sidecar di interlinking), `graph:observations` (le osservazioni primarie degli 8 cubi statistici), `graph:idpt-computed` (il cubo 8 con le 428 osservazioni dell'IDPT calcolato), `graph:metadata` (il `dcatapit:Dataset` del deliverable). Le **13.312 `qb:Observation`** totali del grafo coprono 107 province × 29 anni × 9 cubi × 5 gestioni / 4 regimi / 8 indicatori demografici / 5 voci di reddito a seconda della DSD applicabile. Su tutto questo sono materializzati **107 `owl:sameAs` verso DBpedia** che chiudono la quintupla identità di ogni provincia italiana nel LOD Cloud. La sezione che segue racconta le decisioni che hanno prodotto questo risultato.

### 4.1 I nove vocabolari riusati — perché ognuno è lì

Il primo lavoro della modellazione è stato selezionare i vocabolari da riusare. Il riuso massiccio di standard esterni è la metrica sostantiva del lavoro LOD: si misura sulla *parsimonia delle classi proprie* e sulla *densità di linking semantico* verso vocabolari riconosciuti. I 9 vocabolari selezionati sono organizzati in quattro tier in base al ruolo che svolgono nel grafo.

#### Tier 1 — Il cuore dell'ontologia

**RDF Data Cube (`qb:` = `http://purl.org/linked-data/cube#`)** — Raccomandazione W3C del 16 gennaio 2014. È l'ontologia "canonica" per pubblicare in RDF dati statistici multidimensionali — cubi del tipo "occupati per provincia × anno × sesso × settore". Risponde alla domanda *"come modello in modo interoperabile uno schema statistico generale, indipendentemente dal dominio?"*. Ispirata a SDMX (Statistical Data and Metadata eXchange, ISO/IEC 17369), lo standard di scambio sviluppato congiuntamente da BIS, BCE, Eurostat, FMI, OECD, ONU, Banca Mondiale. Concetti chiave: `qb:DataSet` (il cubo nel suo insieme), `qb:DataStructureDefinition` o DSD (lo schema del cubo: dimensioni / misure / attributi), `qb:Observation` (una singola cella del cubo, identificata univocamente dalla combinazione dei valori delle dimensioni). Nel nostro progetto: 9 DSD, 9 `qb:DataSet`, 13.312 `qb:Observation`. Interoperabile con altri cubi qb dell'ecosistema europeo — Eurostat pubblica i propri dataset come qb e le nostre DSD ancorano dimensioni e misure ai loro `sdmx-concept:` standard via `qb:concept` per riusabilità diretta. Alternative scartate: SDMX-RDF puro (più pesante, orientato a istituti nazionali), modellazione "wide" ad hoc dove ogni record porta tutti i campi come property (anti-pattern documentato dal caso MEF discusso in 4.9).

**SKOS** (Simple Knowledge Organization System, `skos:` = `http://www.w3.org/2004/02/skos/core#`) — Raccomandazione W3C del 18 agosto 2009. Ontologia per modellare in RDF tassonomie, thesauri, classificazioni gerarchiche, vocabolari controllati — pensata per cose come ATECO, ISCO, le classificazioni merceologiche Eurostat, i vocabolari bibliotecari. Risponde a *"come modello in modo interoperabile una lista di termini ufficiali con etichette, sigle, definizioni e relazioni gerarchiche?"*. Concetti chiave: `skos:Concept` (un singolo termine), `skos:ConceptScheme` (la tassonomia nel suo insieme), `skos:prefLabel`/`skos:altLabel` per le etichette con tag di lingua, `skos:notation` per le sigle/codici, `skos:broader`/`skos:narrower` per le gerarchie, `skos:exactMatch`/`skos:closeMatch` per le equivalenze fra schemi diversi. Nel nostro progetto: 6 code-list SKOS proprie (vedi 4.3) per modellare i tipi di gestione INPS, i regimi di liquidazione, le voci di reddito MEF, gli indicatori demografici ISTAT, le componenti IDPT, le aree geografiche. Coerenza stilistica con l'ancora AGID: il TTL dei vocabolari controllati territoriali è già modellato in SKOS, quindi la nostra scelta non introduce un dialetto estraneo nel grafo. Alternative scartate: OWL "vero" con assiomi e restriction (over-engineering per code-list a 4-8 valori), reinvenzione tramite `rdfs:label` (reinventerebbe metà di SKOS).

**OntoPiA CLV + Vocabolari Controllati Territoriali AGID** (`clv:` = `https://w3id.org/italia/onto/CLV/`, URI canoniche `https://w3id.org/italia/controlled-vocabulary/territorial-classifications/...`) — OntoPiA è la rete di ontologie ufficiale della Pubblica Amministrazione italiana, sviluppata da AgID a partire dal 2018 nel quadro del Piano Triennale per l'Informatica nella PA. Contiene una decina di ontologie connesse fra loro (Persona, Organizzazione, Indirizzo, Documento, Luogo, ecc.) allineate al Core Vocabulary del programma europeo ISA². CLV (Core Location Vocabulary) è la sua ontologia per le entità territoriali italiane: definisce classi come `clv:Province`, `clv:Region`, `clv:City`, e property come `clv:acronym` (sigla auto a 2 lettere), `clv:situatedWithin` (regione di appartenenza), `clv:hasRankOrder` (ordinaria vs città metropolitana). I "Vocabolari Controllati territoriali" (province, regioni, comuni) istanziano già tutte le 107 province e le 20 regioni con URI canoniche, codice ISTAT, sigla, NUTS, label IT/EN. Nel nostro progetto: **ancora primaria** del grafo. Riusiamo integralmente le 107 URI canoniche AGID per identificare le province — non ne emettiamo una sola di nostra. Il pattern multi-typing OntoPiA fa sì che ogni provincia AGID sia automaticamente `clv:Province` + `clv:AdminUnitComponent` + `skos:Concept` + `clv:Feature`, ereditando quattro punti di vista semantici al prezzo di una sola URI. Alternative scartate: GeoNames (non ufficiale italiano, gerarchia amministrativa povera), DBpedia o Wikidata come ancora primaria (anti-pattern: sono target di linking esterno, non ancore native), URI proprie del progetto (anti-pattern, perderemmo l'allineamento al contesto della PA italiana).

#### Tier 2 — Accessori per i cubi statistici

**SDMX content vocabulary** (`sdmx-attribute:` = `http://purl.org/linked-data/sdmx/2009/attribute#`, `sdmx-code:`, `sdmx-concept:`) — Pubblicato dal W3C insieme a `qb` nel 2014, è la traduzione RDF dello standard internazionale SDMX. Fornisce **attributi standard** (`sdmx-attribute:obsStatus`, `sdmx-attribute:unitMeasure`, `sdmx-attribute:obsConf`, ecc.) e **code-list standard** riusabili in qualunque cubo qb. Il caso d'uso nostro più rilevante è la code-list di `obsStatus` con i valori `sdmx-code:obsStatus-A` (Normal, valore primario), `-E` (Estimated, valore stimato/derivato), `-P` (Provisional, dato provvisorio), `-F` (Forecast), `-M` (Missing), `-B` (Time series break). Inoltre fornisce **concetti standard** (`sdmx-concept:refArea` per la dimensione territoriale, `sdmx-concept:refPeriod` per la temporale, `sdmx-concept:obsValue` per le misure) a cui le nostre `qb:DimensionProperty` e `qb:MeasureProperty` si ancorano via `qb:concept` per dichiarare esplicitamente la loro semantica SDMX. Nel nostro progetto: 4.399 osservazioni del grafo portano `obsStatus=E` (Plan B GDP cubo 9, importo annuo stimato cubi 2 e 3, aggregazione retroattiva Sardegna cubo 3, IDPT computed cubo 8); l'osservazione del cubo 4 aggregata sull'anno 1980 porta `obsStatus=E` per coerenza pattern. Alternative scartate: booleani propri tipo `:isProjected true` (zero interoperabilità), stringhe libere per lo stato (anti-pattern).

**OWL-Time** (`time:` = `http://www.w3.org/2006/time#`) — Raccomandazione W3C del 19 ottobre 2017. Ontologia generale per concetti temporali in RDF: istanti, intervalli, durate, calendari, relazioni di ordine (Allen's interval algebra), validità storica delle entità. Risponde a *"come modello in modo formale fatti che hanno una dimensione temporale strutturata?"*. Nel nostro progetto: uso **minimale**. La dimensione temporale puntuale (anno snapshot, anno decorrenza) è modellata con `xsd:gYear` (literal XSD standard), che è significativamente più leggero senza perdita di semantica. OWL-Time sarebbe stato opzionalmente impiegato per intervalli di validità di entità territoriali estinte/nate (Olbia-Tempio 2005–2016, BAT dal 2009) via `dcterms:valid`, ma le 4 ex-province sarde sono state aggregate retroattivamente (vedi sez. 2.1) e quindi non compaiono come entità del grafo. La presenza di OWL-Time nel grafo finale è minima — è dichiarato fra i vocabolari riusati per onestà di inventario, non per peso semantico.

#### Tier 3 — Packaging del dataset

**DCAT-AP_IT** (`dcatapit:` = `http://dati.gov.it/onto/dcatapit#`) — Profilo italiano AGID di DCAT-AP (profilo applicativo europeo), che a sua volta è il profilo europeo di DCAT (Data Catalog Vocabulary, Raccomandazione W3C). DCAT è la *lingua franca* per descrivere dataset pubblici: chi li ha pubblicati, quando, sotto quale licenza, in quale formato, dove scaricarli, a quale tema appartengono, di cosa parlano. DCAT-AP_IT è quello che usa il portale italiano `dati.gov.it` ed è obbligatorio per la pubblicazione nei cataloghi PA italiana. Estende DCAT con vincoli aggiuntivi (es. licenze obbligatorie via code-list AGID, conformsTo verso standard nazionali) e con classi specifiche (`dcatapit:Dataset`, `dcatapit:Distribution`, `dcatapit:Agent`, `dcatapit:Organization`). Nel nostro progetto: il deliverable finale `idpt:atlante-idpt` è un `dcatapit:Dataset` (oltre che `dcat:Dataset` + `void:Dataset` per triple-typing — vedi 4.8) con metadati conformi al profilo italiano. Alternative scartate: DCAT puro o DCAT-AP europeo (perdono il contesto italiano), Schema.org `Dataset` (orientato SEO, non LOD-grade per PA).

**dcterms + foaf + vcard** — il trio "infrastruttura Dublin Core" che DCAT-AP_IT trascina con sé. **`dcterms:`** (Dublin Core Terms, `http://purl.org/dc/terms/`) è lo standard storico (1995, refresh 2008) per metadati documentali: `dcterms:title`, `dcterms:description`, `dcterms:license`, `dcterms:issued`, `dcterms:modified`, `dcterms:source`, `dcterms:conformsTo`, `dcterms:creator`, `dcterms:publisher`, `dcterms:hasPart`, `dcterms:language`, `dcterms:valid`. **`foaf:`** (Friend Of A Friend, `http://xmlns.com/foaf/0.1/`, attivo dal 2000) è l'ontologia minimale per descrivere persone e organizzazioni come agenti — `foaf:Agent`, `foaf:Organization`, `foaf:name`, `foaf:homepage`. **`vcard:`** (`http://www.w3.org/2006/vcard/ns#`) è la traduzione RDF del formato vCard usato per i contact point: `vcard:fn` (full name), `vcard:hasEmail`. Nel nostro progetto: tutti e tre i vocabolari sul `dcatapit:Dataset` finale e sui 9 `qb:DataSet` interni — ogni cubo è autoesplicativo con il suo titolo, descrizione, fonte, licenza, in modo da poter essere citato e usato anche al di fuori del deliverable. L'autore del progetto è dichiarato come `foaf:Agent + dcatapit:Agent` con vCard contact point email.

#### Tier 4 — Tattico minimale

**PROV-O** (`prov:` = `http://www.w3.org/ns/prov#`) — Raccomandazione W3C del 30 aprile 2013 per *provenance* e *lineage* in RDF. Permette di esprimere il "come, quando, da chi" un'entità è stata derivata da altre. Concetti chiave: `prov:Entity` (un dato o un documento), `prov:Activity` (un processo), `prov:Agent` (chi ha eseguito l'attività), `prov:wasDerivedFrom` (relazione fondamentale fra entità derivate, supporta navigazione transitiva via SPARQL property path), `prov:wasGeneratedBy` (entità → attività), `prov:wasAssociatedWith` (attività → agente). Nel nostro progetto: uso **minimale e tattico** — solo `prov:wasDerivedFrom` sulle 4.399 osservazioni stimate. La provenance completa (Activity, Agent strutturato) sta già nei sidecar `*.history.json` di macrorefine (sez. 3.6), convertibili in PROV-O completo come upgrade post-progetto. Costo della scelta: una sola property. Beneficio: ogni osservazione stimata è esplicitamente etichettata come derivata da altre, e una singola query SPARQL con `prov:wasDerivedFrom+` (operatore transitivo +) recupera la catena di derivazione completa fino alle osservazioni primarie — pattern di audit applicabile a tutte le 4 famiglie di derivazione del grafo (4.5).

**`owl:sameAs`** — una *singola property* dell'ontologia OWL (Web Ontology Language, Raccomandazione W3C 2004, refresh OWL 2 del 2009). Sintatticamente afferma che "questa entità è identica a quest'altra entità", anche se vivono in dataset diversi. È **lo standard di fatto per il linking esterno nel LOD Cloud** — la "colla" che rende il web di dati un unico grafo globale. Nel nostro progetto: 107 `owl:sameAs` AGID → DBpedia materializzati come nostro contributo originale (sidecar `agid_to_dbpedia.ttl`, vedi 4.6), più 2 `owl:sameAs` aggiuntivi nel sidecar `nuts_aliases.ttl` per riconciliare le PA del Trentino-Alto Adige (NUTS-2 `ITD1`↔NUTS-3 `ITD10`, idem `ITD2`↔`ITD20`). Il resto degli `owl:sameAs` NUTS — verso `nuts.geovocab.org` — arriva già pre-cotto dal TTL AGID nativo (116 link totali, incluse 9 revisioni NUTS storiche multiple). Alternative scartate per il linking esterno: linking diretto verso Wikidata (raggiunto comunque transitivamente via DBpedia), GeoNames (escluso per parsimonia ragionata — un'unica fonte esterna ben curata vale più di tre fonti parziali da mantenere).

#### Vocabolari valutati e scartati

Per completezza di rendicontazione metodologica, vale la pena dichiarare anche cosa abbiamo *consapevolmente lasciato fuori*: **Schema.org Dataset** (SEO-only, non LOD-grade per PA italiana), **OWL "vero" con assiomi e restriction** (over-engineering — usiamo solo `owl:sameAs`), **GeoSPARQL** (non modelliamo geometrie nel grafo RDF; il rendering avviene via GeoJSON Openpolis dichiarato in sez. 2.4 e discusso in sez. 5), **Eurostat dimension namespace** (ridondante con `sdmx-attribute:` per i nostri attributi), **XKOS** (estensione SKOS per classificazioni statistiche multilivello con storicizzazione formale — sovradimensionato per code-list a 4-8 valori, citato nel report come alternativa valutata e scartata per parsimonia), **VoID completo** (incluso solo in forma minimale, 3 property `void:triples` + `void:sparqlEndpoint` + `void:exampleResource` sul `dcatapit:Dataset`).

### 4.2 Una sola classe propria: `idpt:SedeINPS`

Su un grafo di ~117.000 triple, abbiamo definito *una sola* classe propria — `idpt:SedeINPS` — più due ObjectProperty associate. Tutto il resto è istanza di classi standard (`clv:Province`, `clv:Region`, `skos:Concept`, `qb:Observation`, `qb:DataSet`, `qb:DataStructureDefinition`, `dcatapit:Dataset`, ecc.). Questa parsimonia non è uno stilismo: è la metrica diretta su cui si misura "LOD ben fatto vs LOD inventato".

La motivazione della classe propria è semantica, non comoda. Come dichiarato nella sez. 2.1, l'asimmetria fra "provincia di residenza" (asse del cubo 1, 107 entità) e "provincia della sede INPS" (asse dei cubi 2 e 3, 106 sedi) è una realtà del dominio INPS che il grafo deve rappresentare onestamente. Le due opzioni alternative sarebbero state semanticamente disoneste: (a) "appiattire" le sedi sulla residenza richiederebbe duplicare alcune osservazioni e introdurrebbe doppi conteggi nelle query di aggregazione; (b) modellare le sedi come `clv:Province` confonderebbe due assi che il dato sorgente tiene distinti. Una classe propria preserva la distinzione senza intaccare la centralità dell'ancora AGID.

```turtle
@prefix idpt: <https://example.org/idpt/> .
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

**Packaging unificato per esplorazione visuale.** I due file ontologici sopra elencati (classi/property e code-list) sono affiancati da un terzo file `output/vocabularies/ontology.ttl`, generato come *bundle aggregato* dei due. Il bundle aggiunge in testa una dichiarazione `<idpt:> a owl:Ontology` con metadati ricchi (titolo bilingue, descrizione, creator, publisher, licenza CC-BY 4.0, versione, prefisso preferito via VANN) e include sotto il contenuto sostantivo di entrambi i file sorgente, per un totale di 551 triple. Lo scopo del bundle non è la pubblicazione in Fuseki — per quella vengono caricati i due file singoli nei rispettivi grafi nominati — ma il **caricamento in editor ontologici come Protégé**, che si aspettano una singola dichiarazione `owl:Ontology` come radice del file aperto. Aprendo `ontology.ttl` in Protégé via *File → Open File*, si naviga ad albero la classe propria `idpt:SedeINPS` con la sua subClassOf `clv:Feature`, le 2 ObjectProperty associate, le 10 `qb:DimensionProperty` e le 9 `qb:MeasureProperty`, le 9 `qb:DataStructureDefinition` e i 6 `skos:ConceptScheme` con i 27 `skos:Concept` totali. La generazione del bundle è una semplice concatenazione dei due file più il preambolo: i file sorgente restano la fonte di verità.

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
@prefix idpt: <https://example.org/idpt/> .
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

Il principio adottato dalla modellazione è che ogni misura del grafo che *non* è un dato primario letto dal CSV sorgente, ma una stima o un'aggregazione del progetto, deve essere etichettata **in modo uniforme** come tale. Il pattern è composto da una coppia di asserzioni:

- `sdmx-attribute:obsStatus sdmx-code:obsStatus-E` (Estimated)
- `prov:wasDerivedFrom <obs-origine-1> , <obs-origine-2> , ...` (una o più sorgenti)

Il pattern uniforme è applicato in **4 punti del grafo**:

| # | Caso | Cubo | Origini | # obs marcate |
|---|---|---|---|---:|
| 1 | Aggregazione retroattiva Sardegna 2005–2011 | 3 | obs sede sarda + obs ex-provincia stessa fascia anno | 84 |
| 2 | Importo annuo ricostruito (`n × media × 13`) | 2, 3 | obs `numeroPensioni` + obs `importoMedioMensile` stessa cella | 3.459 |
| 3 | Plan B GDP proiettato | 9 | obs cubo 1 gestione=Pubblici + DataSet cubo 4 | 428 |
| 4 | IDPT computed | 8 | obs primarie usate nel calcolo della componente | 428 |
| | | | **Totale obs estimate** | **4.399** |

Esempio dell'osservazione del Plan B GDP per Torino, regime retributivo:

```turtle
idpt:obs-plan-b-001-2026-retributivo a qb:Observation ;
    qb:dataSet idpt:cubo-plan-b-gdp-projected ;
    idpt:provincia <https://w3id.org/italia/controlled-vocabulary/territorial-classifications/provinces/001> ;
    idpt:annoRiferimento "2026"^^xsd:gYear ;
    idpt:regimeLiquidazione idpt:regime-retributivo ;
    idpt:numeroPensioni "4900"^^xsd:nonNegativeInteger ;
    sdmx-attribute:obsStatus sdmx-code:obsStatus-E ;
    prov:wasDerivedFrom
        idpt:obs-vigenti-001-2026-pubblici ,         # 35.000 GDP Torino totali (cubo 1)
        idpt:cubo-pensioni-decorrenza-gdp ;          # 14% retributivo nazionale (cubo 4)
    rdfs:comment "Stima: 35.000 (GDP Torino) × 14% (retributivo nazionale) = 4.900 pensioni."@it .
```

Il vantaggio della scelta è duplice. Innanzitutto, una **singola query SPARQL** recupera tutte le 4.399 osservazioni stimate del grafo, ovunque si trovino, qualunque sia il loro tipo:

```sparql
SELECT ?obs ?cubo WHERE {
  ?obs a qb:Observation ; qb:dataSet ?cubo ;
       sdmx-attribute:obsStatus sdmx-code:obsStatus-E .
}
```

E secondo, una query parallela mostra la **catena transitiva** di derivazione di qualsiasi osservazione stimata, fino alle sue origini primarie:

```sparql
SELECT ?origine WHERE {
  idpt:obs-plan-b-001-2026-retributivo prov:wasDerivedFrom+ ?origine .
}
```

L'operatore SPARQL `+` (uno o più passi) segue la catena transitivamente; per le osservazioni dell'IDPT computed che derivano dal Plan B che a sua volta deriva dal cubo 1, una sola query mostra la quadrupla origine. È il pattern di **lineage auditabile** che giustifica l'uso minimale di PROV-O senza dover ricostruire una macchina della provenance da zero. Vale la pena ricordare che la materia prima di tutto questo esisteva già a livello tabellare nei sidecar `*.history.json` di macrorefine (sez. 3.6): la transizione "tabellare → RDF" è stata progettata in modo che ogni catena di derivazione che era tracciata nelle History venisse materializzata come `prov:wasDerivedFrom` nel grafo. Le due rappresentazioni sono ortogonali ma coerenti.

### 4.6 Interlinking — i tre sidecar TTL

Il linking interno (fra dati e ancore semantiche del grafo IDPT) e il linking esterno (verso il LOD Cloud) sono materializzati in tre sidecar TTL caricati nel `graph:linking` di Fuseki. Sono distinti dai cubi statistici perché sono asserzioni di equivalenza e di identità, non osservazioni statistiche.

**`output/mappings/nuts_aliases.ttl`** — 6 asserzioni. Le 2 sono `owl:sameAs` semantici locali per le PA Trentino-Alto Adige, che riconciliano il cubo ISTAT-RFL (occupati, NUTS-2) con il cubo ISTAT-Demo (indicatori, NUTS-3) come dichiarato nella sez. 2.2: `ITD10 owl:sameAs ITD1` e `ITD20 owl:sameAs ITD2`, con `rdfs:comment` che dichiara esplicitamente la natura locale dell'equivalenza ("valida solo per le PA dove regione NUTS-2 coincide con provincia NUTS-3"). Le altre 4 sono `skos:exactMatch` per i fake-NUTS ISTAT proprietari (`IT108`/`IT109`/`IT110`/`IT111` per Monza-Brianza, Fermo, BAT, Sud Sardegna — le 4 province moderne senza NUTS-3 Eurostat ufficiale, anch'esse anticipate in sez. 2.2). La scelta di `skos:exactMatch` invece di `owl:sameAs` per i fake-NUTS è metodologicamente cauta: `IT108` non è "lo stesso oggetto" di Monza-Brianza nel senso identitario forte, è un identificatore concettualmente equivalente prodotto da un sistema diverso (ISTAT vs Eurostat).

**`output/mappings/inps_to_agid.ttl`** — circa 440 triple. Contiene due pattern. Primo: `skos:altLabel` con tag di lingua privato `it-x-inps` (estensione BCP47 `x-` per subtag privato, pattern usato in archivi e biblioteche per registrare varianti grafiche) sulle URI AGID delle province, che preserva le anomalie nominali INPS senza creare entità nuove. Esempio: `agidp:047 skos:altLabel "MASSA CARRARA"@it-x-inps`. Secondo: le 106 istanze `idpt:SedeINPS` con `idpt:correspondsToProvinceAGID` (1-a-1, 105 istanze) o `idpt:aggregatesProvince` (1-a-N, solo la sede Cagliari-e-Sud-Sardegna). Il sidecar è generato come effetto collaterale dello step `LinkSedeINPS` durante la Recipe del cubo 2 (sez. 3.5).

**`output/mappings/agid_to_dbpedia.ttl`** — 107 `owl:sameAs` AGID → DBpedia, materializzati come contributo originale del progetto via lo script standalone `scripts/generate_agid_to_dbpedia.py` (sez. 3.2). La procedura di matching è: query SPARQL su `https://dbpedia.org/sparql` per estrarre tutte le province italiane (`?p a dbo:Province ; dbo:country dbpedia:Italy`), match esatto su `prefLabel` italiana normalizzata, reconciliation manuale con 25 override hardcoded (14 città metropolitane "Metropolitan City of …" + 11 anomalie nominali). Il file contiene un header con `dcterms:source <https://dbpedia.org/sparql>` e `dcterms:created` con timestamp della query, perché DBpedia evolve nel tempo e il mapping va datato.

I tre sidecar insieme producono la **quintupla identità** di ogni provincia italiana nel LOD Cloud. Per Torino:

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

Cinque "punti di identità" sulla stessa entità: la URI canonica AGID (ancora primaria), il codice NUTS Eurostat (linking europeo), la risorsa DBpedia (linking LOD globale, transitivo verso Wikidata e oltre), la label INPS originale preservata, l'identificatore della sede INPS che la gestisce amministrativamente. Pattern **LOD 5★ pieno** sulla scala di Berners-Lee.

### 4.7 Il cubo 8 IDPT computed — il cuore narrativo

Il cubo 8 è ciò che il progetto produce di originale: l'**Indice di Dipendenza Previdenziale Territoriale** materializzato come `qb:DataSet` in un grafo nominato separato `graph:idpt-computed`. La materializzazione (preferita all'alternativa "vista on-the-fly via SPARQL puro") è la scelta giusta per la pratica LOD: il deliverable RDF deve contenere il risultato della ricerca, non lasciarlo a una query da rieseguire ogni volta.

Le tre dimensioni dell'IDPT (sez. 1 del report — Abstract) sono calcolate per ogni provincia secondo formule esplicite:

- **D1 — Pressione demografica previdenziale** = pensionati_totale (cubo 1) / (occupati_migliaia (cubo 5) × 1000). Range grezzo sulle 107 province: 0.59 (Bolzano) – 1.48 (Reggio di Calabria).
- **D2 — Peso economico delle pensioni** = monte_pensioni_€ (cubo 1, somma dei `importoAnnuoComplessivo` per provincia × 10⁶) / monte_redditi_da_lavoro_€ (cubo 7, somma di `v2 + v4 + v5 + v6 + v7` per provincia). Range grezzo: 0.33 – 0.77.
- **D3 — Eredità storica delle riforme** = pensioni_in_regime_retributivo (cubo 2 + cubo 9 per la quota Pubblici stimata via Plan B) / pensioni_totali_con_regime (cubo 2 esteso a Pubblici dal cubo 9). Range grezzo: 0.42 – 1.37 (il valore > 1 di alcune province non sarde con `agidp:092` Cagliari e `agidp:111` Sud Sardegna è effetto della decisione "Sardegna 1:N" discussa sotto).

Le tre dimensioni grezze sono poi **normalizzate min-max** sui 107 valori della stessa componente: per ognuna, `(x − min) / (max − min)` produce un valore in [0,1] dove 0 è la provincia con il valore minimo e 1 è la provincia con il valore massimo. Le tre componenti normalizzate sono poi **aggregate via media aritmetica** in un valore IDPT finale anch'esso in [0,1]:

`IDPT(provincia) = (D1_normalizzato + D2_normalizzato + D3_normalizzato) / 3`

Le 428 osservazioni del cubo 8 (107 province × 4 concetti — le 3 componenti più l'aggregato) portano tutte `obsStatus=E` (sono derivate per costruzione) e `prov:wasDerivedFrom` esplicito verso le osservazioni dei cubi primari usate nel calcolo. Decisione metodologica delicata sul caso Sardegna: D3 viene calcolata sulla sede INPS "Cagliari e Sud Sardegna" (sede aggregata) ma deve essere attribuita a *due* province AGID separate (`092` Cagliari e `111` Sud Sardegna). La decisione adottata (Opzione a del Blocco F) è di **replicare l'intero valore della sede aggregata su entrambe le province AGID** — sceltà semantica preferita rispetto a una divisione arbitraria 50/50 perché non abbiamo dati su come la composizione regime varia fra le due province; la replica è documentata nei `prov:wasDerivedFrom` delle osservazioni interessate, quindi auditabile.

Il risultato sostantivo è un **divario Nord/Sud nettissimo**, con un rapporto di circa 20× fra le province più dipendenti e quelle meno dipendenti dal sistema pensionistico:

**Top 5 IDPT** (più dipendenti): Reggio di Calabria 0.675, Taranto 0.651, Catanzaro 0.627, Oristano 0.580, Nuoro 0.552.
**Bottom 5 IDPT** (meno dipendenti): Bolzano/Bozen 0.034, Milano 0.100, Trento 0.104, Prato 0.121, Padova 0.141.

La narrativa è solida: due province alpine autonome con economia dinamica e demografia ancora giovane (Bolzano, Trento) all'estremo basso; due metropoli del triangolo industriale (Milano, Padova) e una città di distretto tessile (Prato) accanto a loro; all'estremo alto cinque province meridionali — quattro calabresi/pugliesi e una sarda — dove la combinazione di bassa occupazione, demografia anziana, ed eredità retributiva del periodo pre-Dini produce un livello di dipendenza dal sistema pensionistico nettamente più alto. La lettura cartografica viene approfondita nella sez. 5.

### 4.8 DCAT-AP_IT del deliverable finale

Il deliverable del progetto è impacchettato come `dcatapit:Dataset` in `output/dataset/atlante_idpt_dataset.ttl`, con triple-typing (`dcatapit:Dataset` + `dcat:Dataset` + `void:Dataset`) per ottenere sia la conformità al profilo italiano AGID (`dcatapit:`) sia la compatibilità con DCAT puro (`dcat:`) sia la dichiarazione minimale delle caratteristiche tecniche del grafo (`void:`). I 9 `qb:DataSet` interni sono collegati al dataset di packaging via `dcterms:hasPart`, in modo che il consumer del DCAT possa navigare al cubo specifico di interesse senza dover decostruire il bundle.

I metadati del `dcatapit:Dataset` includono: titolo bilingue IT/EN, descrizione, 3 temi EuroVoc (SOCI = Affari sociali, ECON = Economia, REGI = Regioni), 11 keyword bilingue, licenza CC-BY 4.0, `dcterms:rights` esplicativo della composizione delle 5 licenze sorgente (IODL 2.0 INPS + CC-BY 3.0 IT ISTAT + CC-BY 3.0 MEF + CC-BY 4.0 AGID, ricompilato sotto CC-BY 4.0 — vedi sez. 2.5), `dcterms:conformsTo` verso SKOS, qb e dcatapit (triplice conformità), pubblicatore Roberto Bruno come `foaf:Agent + dcatapit:Agent`, contact point vCard con email. Sono dichiarate **3 distribuzioni**: il bundle TTL aggregato (`atlante-idpt.ttl`), la versione JSON-LD (`atlante-idpt.jsonld`), e un bundle ZIP con i sorgenti separati per chi vuole i singoli cubi distinti. La componente VoID minimale espone `void:triples` (calcolato sui file emessi: 116.633 triple al momento dell'emissione finale), `void:sparqlEndpoint` (URL placeholder verso il Fuseki di pubblicazione), e tre `void:exampleResource` (la URI di Torino in AGID, una `qb:Observation` esemplare, l'IDPT computed di Torino).

Il file passa **14/14 check SPARQL** di validazione (`scripts/validate_dataset.py`): conformità DCAT-AP_IT, presenza di tutti i metadati obbligatori, integrità delle relazioni `dcterms:hasPart` verso i 9 cubi, validità delle URI delle distribuzioni, presenza dei due agenti (publisher, creator), presenza del contact point.

### 4.9 Il caso di studio negativo: "RDF di facciata" del MEF

Il file `data/mef_redditi_irpef_comune_2024_v1.rdf` distribuito dal MEF a fianco del CSV (sez. 2.3) è la cartina al tornasole di cosa *non* è il Linked Open Data. Lo conserviamo in repository non come fonte di dati — usiamo il CSV per il cubo 7 — ma come **caso di studio negativo** che fa risaltare per contrasto il lavoro di modellazione fatto altrove nel progetto. L'anatomia del file mostra cinque problemi cumulativi.

**Namespace placeholder mai sostituito**: la dichiarazione XML del file è `xmlns:s="http://www1.finanze.gov.it/fakeurl#"`. Sì, "fakeurl" è letteralmente scritto nel namespace. Vale a dire che ogni asserzione del file ha come predicato un'URI che inizia con la stringa "fakeurl" — un dettaglio inequivocabile che il file non è stato pubblicato con la cura del LOD ma è il risultato di un export automatico da un template mai personalizzato.

**Variabili anonime senza URI semantiche**: i predicati del file sono `s:v1`, `s:v2`, ..., `s:v22` — numeri ordinali invece di concetti. Chi legge l'RDF deve aprire una documentazione esterna per scoprire che `v2` significa "Reddito da lavoro dipendente". Nel nostro grafo, in netto contrasto, la stessa informazione vive come `idpt:voce-redd-lavoro-dipendente` (URI semantica) con `skos:notation "v2"` (preserviamo la sigla nativa del MEF come notazione) — `v2` è preservato come riconoscibilità, ma l'URI canonica è `voce-redd-lavoro-dipendente` per consumo machine-readable.

**Modellazione "wide" senza Data Cube**: ogni record è una `<s:riga>` con tutti gli attributi compressi come property dirette. Zero `qb:Observation`, zero `qb:DataStructureDefinition`, zero pattern di cubo. È esattamente il pattern anti-LOD documentato in W3C come anti-pattern (un singolo nodo "tutto-contenente" è opaco a query strutturate). Nel nostro grafo la stessa informazione è modellata come 535 `qb:Observation` distinte, con dimensioni interrogabili separatamente via SPARQL.

**Zero linking, zero ancore semantiche**: il file contiene zero occorrenze di SKOS, zero di qb, zero di DCAT, zero di `owl:sameAs`, zero di vocabolari AGID, zero di classificazioni ISTAT. Le sigle delle province sono stringhe libere, non collegate al vocabolario controllato che è pubblicato dalla stessa PA italiana. Non c'è un solo "ponte" semantico verso il resto del LOD Cloud.

**Data malformata**: il file dichiara `<s:aggiornato>2026-23-04</s:aggiornato>`. Mese 23. Formato non ISO 8601. Per un file che si presenta come 5★ — il MEF lo dichiara esplicitamente nella sua pagina open data ("statistiche distribuzioni esportabili in PDF, Excel, CSV e in 5-star RDF format") — la data malformata è il sigillo della distanza fra dichiarato e implementato.

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
PREFIX idpt: <https://example.org/idpt/>

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
PREFIX idpt: <https://example.org/idpt/>

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
PREFIX idpt: <https://example.org/idpt/>

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

Il deliverable finale è accessibile attraverso tre livelli complementari. Il primo livello è il **`dcatapit:Dataset`** del progetto, presentato in dettaglio in sez. 4.8 e materializzato in `output/dataset/atlante_idpt_dataset.ttl`. Le tre distribuzioni dichiarate nel DCAT — `atlante-idpt.ttl` (bundle RDF/Turtle aggregato dei 9 cubi + sidecar + vocabolari), `atlante-idpt.jsonld` (versione JSON-LD per consumer Web), `atlante-idpt-bundle.zip` (archivio con i file separati per chi vuole granularità di cubo) — sono i tre formati pubblicati per coprire tre casi d'uso diversi: il triplestore (Turtle), l'applicazione Web/SPA (JSON-LD), e l'archivio per analisi offline (ZIP). Il VoID minimale (`void:triples`, `void:sparqlEndpoint`, `void:exampleResource`) chiude il package con la dichiarazione delle caratteristiche tecniche del grafo.

Il secondo livello è la **landing page GitHub Pages** in `docs/index.html`, generata come pagina HTML statica con: descrizione del dataset auto-estratta da `dcterms:description`, statistiche aggregate (~117k triple, 13.312 obs, 107 sameAs DBpedia), la mappa principale `idpt_map.html` embedded come iframe interattivo, top/bottom 10 IDPT come tabelle HTML, link alle tre distribuzioni downloadable, 4-5 query SPARQL di esempio come blocchi pre-formattati copiabili, link al `REPORT.md` e al repository GitHub del progetto. Il branch `main` con path `/docs/` è esposto come sito statico all'URL `https://robertobrunocl.github.io/idpt-italia/` (l'username GitHub viene concretizzato in fase di deploy finale via lo script `scripts/finalize_namespace.py` che esegue il find-and-replace globale del namespace `https://example.org/idpt/` → `https://robertobrunocl.github.io/idpt-italia/` su tutti i 13 file TTL del progetto).

Il terzo livello è la **demo dal vivo**, in cui il grafo viene caricato in Fuseki locale e interrogato live con le 12 query commentate in 5.2. La scelta di non esporre un endpoint SPARQL pubblico permanente (es. via ngrok o cloud free-tier) è una decisione metodologica: in fase di presentazione conta avere zero dipendenze di rete, e Fuseki locale + `scripts/run_sparql_demo.sh` garantisce zero superficie di rischio. Un endpoint pubblico stabile (Trifid, Linked Data Frontend, oppure deploy di Fuseki su un VPS) è uno degli **upgrade post-progetto** naturali, citato in 5.4 insieme alla pubblicazione su `dati.gov.it` (registrazione standard per la PA italiana) e all'upgrade del namespace da GitHub Pages a `w3id.org/idpt-italia` via richiesta di Pull Request al maintainer di `perma-id/w3id.org`.

### 5.4 Limiti e prospettive

Il progetto raggiunge l'obiettivo della pratica LOD 5★ e produce una risposta sostantiva alla sua domanda di ricerca, ma è uno snapshot di un sistema. Cinque limiti vanno dichiarati esplicitamente come parte dell'onestà del lavoro.

**Granularità temporale dell'IDPT**. L'indice è calcolato solo per l'anno 2026. La serie storica del cubo 3 (1998–2026) fornisce la traiettoria del numero di pensioni nel tempo, ma non i denominatori storici (occupati per provincia × anno, monte redditi da lavoro per provincia × anno) che servirebbero per calcolare l'IDPT per ogni anno. Estendere il calcolo dell'IDPT alla serie storica richiederebbe l'integrazione di ulteriori cubi ISTAT-RFL (occupati storici, parzialmente disponibili) e MEF (redditi storici, anche pubblicati con disallineamento temporale crescente all'indietro).

**Plan B GDP — euristica decorrenza→regime**. La stima della composizione regime delle pensioni della Gestione Dipendenti Pubblici è derivata via un'euristica calibrata sulla normativa (Riforma Dini 1995, Riforma Fornero 2011) ma mai validata su microdati amministrativi INPS (che non sono pubblici). Un'eventuale collaborazione con INPS-DC Statistica permetterebbe di verificare l'accuratezza dell'euristica e di sostituirla con dati primari.

**Sardegna 1:N nella D3**. La decisione di replicare l'intero valore della sede aggregata Cagliari-e-Sud-Sardegna sulle due province AGID Cagliari (092) e Sud Sardegna (111) è un'approssimazione esplicita (sez. 4.7). Una stima migliore richiederebbe disaggregare la sede aggregata sulle due province con qualche criterio proxy (es. popolazione 65+ residente in ciascuna). La decisione attuale è quella più trasparente in attesa di un dato di disaggregazione disponibile.

**Disallineamento temporale MEF 2024 vs INPS 2026**. I redditi MEF si riferiscono al 2024 (dichiarati nel 2024 per l'anno di imposta 2023), gli snapshot INPS al 1.1.2026, gli occupati ISTAT al 2025. Il disallineamento di 1–3 anni introduce un rumore secondario nel calcolo di D2 ma non altera il segnale Nord/Sud principale.

**PROV-O minimale**. La provenance del grafo usa solo `prov:wasDerivedFrom`. Una valorizzazione completa del lineage richiederebbe la serializzazione dei sidecar `*.history.json` di macrorefine come `prov:Activity` + `prov:Agent` + `prov:wasGeneratedBy` + `prov:wasAssociatedWith` strutturati — upgrade tecnicamente immediato (i dati esistono già nelle history) ma non realizzato per parsimonia di scope.

Le **prospettive di sviluppo** che il lavoro apre sono varie. Una **animazione storica dell'IDPT** (su anni e indice ricalcolato) sarebbe il completamento naturale della visualizzazione. Un **confronto cross-paese via Eurostat NUTS-3** è praticabile poiché tutti i nostri 107 codici NUTS sono già linkati nel grafo via `owl:sameAs`: rifacendo lo stesso lavoro su Spagna, Francia, Germania (paesi con strutture pensionistiche comparabili) si potrebbero costruire IDPT comparabili a livello europeo. Una **registrazione del dataset su `dati.gov.it`** chiuderebbe il cerchio della pubblicazione conforme alla PA italiana. L'**upgrade del namespace a `w3id.org`** darebbe stabilità a 10+ anni alle URI canoniche del progetto. Un **endpoint SPARQL pubblico stabile** trasformerebbe il deliverable da repo statico a servizio interrogabile in modo persistente. Nessuno di questi è un blocco al risultato attuale, ma ognuno alza il valore del lavoro come infrastruttura riusabile da altri ricercatori.

---

## 6. Licenza del deliverable e compatibilità con le sorgenti

Il **deliverable finale del progetto** — il grafo RDF dell'Atlante IDPT pubblicato come `dcatapit:Dataset` — adotta come licenza **Creative Commons Attribuzione 4.0 Internazionale** (CC-BY 4.0). La scelta è compatibile con tutte e cinque le licenze sorgente dichiarate in sez. 2.5: IODL 2.0 (INPS), CC-BY 3.0 IT (ISTAT), CC-BY 3.0 generica (MEF), CC-BY 4.0 (AGID) e CC-BY (Openpolis) ammettono opere derivate con attribuzione, condizione che CC-BY 4.0 richiede esplicitamente. CC-BY 4.0 è inoltre la stessa licenza scelta da AGID per i propri vocabolari controllati, garantendo coerenza stilistica con il contesto normativo nazionale.

La dichiarazione di provenienza composita — "Dataset aggregato da fonti pubbliche con licenze CC-BY 3.0 IT (ISTAT), CC-BY 3.0 (MEF), CC-BY 4.0 (AGID), IODL 2.0 (INPS); riconfezionato come opera derivata con licenza CC-BY 4.0" — è materializzata nel campo `dcterms:rights` del `dcatapit:Dataset` finale e accompagna ogni distribuzione pubblicata (TTL, JSON-LD, ZIP).

Una sesta licenza, **CC-BY-SA 3.0**, vincola DBpedia, che è il target del linking esterno `owl:sameAs` del progetto (107 triple nel sidecar `agid_to_dbpedia.ttl`). Poiché un'asserzione `owl:sameAs` referenzia un'entità esterna senza duplicarne i contenuti, la clausola share-alike di DBpedia non si propaga al nostro deliverable, che resta licenziabile come CC-BY 4.0. L'attribuzione DBpedia è comunque mantenuta nel sidecar via `dcterms:source` verso `https://dbpedia.org/sparql` con timestamp della query, perché DBpedia evolve nel tempo e il mapping va datato.
