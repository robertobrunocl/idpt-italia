# macrorefine

Libreria Python di data cleaning a pipeline, sviluppata come parte del
progetto **Atlante della dipendenza previdenziale italiana — IDPT** (vedi
`../README.md` per il contesto). Il nome richiama l'idea di "fare refining
in modo macroscopico", cioè per blocchi componibili e ripetibili invece
che con script monolitici per ogni dataset.

## Contesto e scopo

La libreria è stata scritta per supportare la pipeline di elaborazione del
progetto IDPT, dove nove dataset CSV eterogenei (INPS, ISTAT, MEF) andavano
puliti, normalizzati, aggregati e arricchiti con riferimenti a vocabolari
controllati AGID prima di essere materializzati come grafo RDF. Il dominio
di applicazione naturale è quindi quello del **data cleaning verso Linked
Open Data**, con un'estensione (`macrorefine.steps.lod`) che contiene
13 step custom specifici per il progetto IDPT (parsing numeri italiani,
linking province → URI AGID via SPARQL, aggregazioni territoriali, ecc.).

La libreria *non* è un prodotto a sé stante: è uno strumento di lavoro che
risolve i pattern di pulizia ricorrenti incontrati nel progetto, con
particolare attenzione a tre requisiti che il dominio LOD richiede:

- **Immutabilità del `Dataset`** e audit trail strutturato (`StepRecord`
  con parametri e metriche), perché ogni trasformazione deve essere
  ricostruibile a partire dal CSV grezzo.
- **History serializzabile** in sidecar JSON, perché il lineage tabellare
  diventa poi `prov:wasDerivedFrom` nel grafo RDF emesso.
- **Recipe** come fabbriche di pipeline parametrizzate per un singolo CSV
  sorgente, perché ogni cubo del grafo IDPT ha la sua Recipe dedicata.

---

## 📦 Installazione

```bash
# Clona il repository
git clone <your-repo-url>
cd macrorefine

# Crea e attiva un virtualenv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installa in modalità editable con le dipendenze di sviluppo
pip install -e ".[dev]"
```

**Requisiti**: Python ≥ 3.10, pandas ≥ 2.0

---

## 🚀 Quickstart

```python
import pandas as pd
from macrorefine import Dataset, Pipeline
from macrorefine.steps import (
    NormalizeColumnNames,
    DropEmptyColumns,
    DropDuplicateRows,
    FillMissing,
)

# 1. Carica un dataset (anche sporco)
df = pd.DataFrame({
    "ID": [1, 2, 3, 3],
    "Full Name": ["Alice", "Bob", "Charlie", "Charlie"],
    "Age": [30, None, 25, 25],
    "EmptyCol": [None, None, None, None],
})
ds = Dataset(df)

# 2. Diagnostica
print(ds.profile())

# 3. Costruisci una pipeline
clean = (
    Pipeline()
    .add(NormalizeColumnNames())
    .add(DropEmptyColumns())
    .add(DropDuplicateRows())
    .add(FillMissing(columns=["age"], strategy="median"))
    .run(ds)
)

# 4. Risultato + audit trail
print(clean.to_pandas())
print(clean.history)
```

---

## 📚 Concetti chiave

### `Dataset`

Wrapper immutabile attorno a un `pandas.DataFrame`. Ogni trasformazione ritorna **un nuovo** `Dataset`, lasciando invariato l'originale.

```python
ds = Dataset.from_csv("data.csv")
ds = Dataset.from_parquet("data.parquet")

ds.columns          # ['col_a', 'col_b']
ds.shape            # (1000, 2)
ds.head(5)          # primi 5 record (DataFrame)
ds.to_pandas()      # copia del DataFrame interno
ds.history          # lista degli step applicati
ds.profile()        # diagnostica
```

### `Pipeline`

Catena ordinata di step, con API fluente.

```python
pipeline = (
    Pipeline(on_error="interactive")  # "interactive" | "skip" | "raise"
    .add(NormalizeColumnNames())
    .add(DropEmptyColumns())
)
clean = pipeline.run(ds)
```

**Strategie di gestione errori (`on_error`):**

| Valore | Comportamento |
|---|---|
| `"interactive"` *(default)* | Chiede all'utente: `[continue/skip/abort]` |
| `"skip"` | Logga l'errore e continua con lo step successivo |
| `"raise"` | Solleva l'eccezione (fail-fast) |

### `PipelineStep`

Classe base per ogni operazione. Per creare uno step custom basta sottoclassarla e implementare `apply()`:

```python
from macrorefine import PipelineStep

class UppercaseCity(PipelineStep):
    def apply(self, dataset):
        df = dataset.to_pandas()
        df["city"] = df["city"].str.upper()
        return dataset.with_data(df, step_name="UppercaseCity")

# Uso
pipeline.add(UppercaseCity())
```

### `ColumnStep`

Per step che operano su **colonne specifiche**, `ColumnStep` riduce il boilerplate: implementi solo `transform_column`, il resto è automatico.

```python
from macrorefine import ColumnStep

class Uppercase(ColumnStep):
    def transform_column(self, series, column_name):
        return series.str.upper()

# Uso
pipeline.add(Uppercase(columns=["name", "city"]))
```

Vantaggi rispetto a un `PipelineStep` puro:

- Validazione automatica dell'esistenza delle colonne
- Gestione automatica della history
- Supporta sia stringa singola (`columns="x"`) sia lista (`columns=["x", "y"]`)
- Il parametro `column_name` permette logica condizionale per colonna

### `Recipe`

Per **pipeline ricorrenti** su dataset specifici, incapsulale in una `Recipe`:

```python
from macrorefine import Recipe, Pipeline
from macrorefine.steps import NormalizeColumnNames, DropEmptyColumns

class CRMDatasetRecipe(Recipe):
    """Pipeline standard per i dataset CRM aziendali."""

    def build(self) -> Pipeline:
        return (
            Pipeline()
            .add(NormalizeColumnNames())
            .add(DropEmptyColumns())
            .add(MyCustomStep())
        )

clean = CRMDatasetRecipe().apply(ds)
```

---

## 🔧 Step built-in

| Step | Descrizione |
|---|---|
| `NormalizeColumnNames` | Converte i nomi delle colonne in `snake_case` |
| `RenameColumns(mapping=...)` | Rinomina colonne secondo un mapping  |
| `DropEmptyColumns` | Rimuove le colonne completamente vuote |
| `DropColumns(columns=...)` |  Rimuove le colonne specificate |
| `DropDuplicateRows` | Rimuove le righe duplicate |
| `DropColumns(columns=...)` | Rimuove le colonne specificate |
| `FillMissing(columns=..., strategy=...)` | Riempie i NaN con `mean`, `median` o `constant` |
| `CastTypes(mapping=..., errors=...)` | Cambia il tipo delle colonne (`raise`/`coerce`) |
| `ParseDates(columns=..., format=..., errors=...)` |  Parsing datetime con formato opzionale |

---

## 💾 Salvataggio dei Dataset

Per scritture semplici, `Dataset` ha già:

```python
ds.to_csv("out.csv")
ds.to_parquet("out.parquet")
```

Per uso avanzato, il modulo `io` offre più funzionalità:

```python
from macrorefine import save_dataset

save_dataset(
    dataset,
    "output/rifiuti_arricchito.csv",
    save_history=True,    # crea anche rifiuti_arricchito.history.json
    sep=";",              # kwargs passati al writer pandas
)
```

Caratteristiche:
- **Auto-detect del formato** dall'estensione (`.csv`, `.parquet`, `.json`)
- **Creazione automatica** delle cartelle mancanti
- **History sidecar** opzionale: file JSON con il log delle trasformazioni applicate
- **Format esplicito**: `format="csv"` per file senza estensione

## 🔍 Profiling

```python
report = ds.profile()
print(report)
```

Output:
```
ProfileReport
========================================
Rows: 100   Cols: 5

⚠ Non-snake_case columns (3):
    - 'ID'
    - 'Full Name'
    - 'EmptyCol'
⚠ Empty columns: ['EmptyCol']
⚠ Duplicate rows: 2

Dtypes:
    ID: int64
    Full Name: object
    ...
```

Attributi accessibili programmaticamente:

```python
report.n_rows
report.n_cols
report.non_snake_case_columns
report.duplicated_column_names
report.empty_columns
report.high_null_columns       # dict: col -> ratio
report.duplicate_rows
report.dtypes                  # dict: col -> dtype
```

---

## 🧪 Testing

```bash
pytest -v
pytest --cov=macrorefine --cov-report=term-missing
```

---

## 📁 Struttura del progetto

```
macrorefine/
├── src/macrorefine/
│   ├── dataset.py        # Dataset (wrapper immutabile)
│   ├── pipeline.py       # Pipeline + gestione errori
│   ├── step.py           # PipelineStep (ABC)
│   ├── recipe.py         # Recipe (ABC)
│   ├── history.py        # History + StepRecord
│   ├── profiling.py      # Diagnostica
│   └── steps/            # Step built-in
├── tests/                # Test suite (pytest)
└── examples/             # Esempi d'uso
```

---

## Stato e limiti

La libreria copre i pattern di pulizia incontrati nel progetto IDPT ma non
è un toolkit di data cleaning completo. In particolare:

- Backend basato solo su `pandas`. Non c'è astrazione di backend né
  supporto a DuckDB / Polars / Spark.
- Il profiling è euristico (rileva i pattern più comuni) ma non sostituisce
  strumenti dedicati come `ydata-profiling` o `pandera`.
- L'estensione LOD-aware (`macrorefine.steps.lod`) è tagliata su misura per
  i vocabolari controllati AGID e per i CSV INPS/ISTAT/MEF, e non è pensata
  per essere generica.
- La gestione errori interattiva ha senso in fase di sviluppo della Recipe;
  per esecuzioni batch in produzione si usa `on_error="raise"`.

## License

MIT