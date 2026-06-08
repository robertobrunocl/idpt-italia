# MacroRefine

> A simple, modular and extensible data cleaning pipeline library for Python.

MacroRefine ti aiuta a costruire **pipeline di pulizia e trasformazione dati** in modo dichiarativo, riusabile e tracciabile. Identifica automaticamente le criticità più comuni nei dataset (nomi colonne sporchi, valori mancanti, duplicati, ecc.) e ti permette di applicare step di pulizia componibili — inclusi step **custom** scritti da te per i tuoi casi specifici.

---

## ✨ Caratteristiche principali

- 🧱 **Dataset immutabile**: ogni trasformazione produce un nuovo `Dataset`, mai effetti collaterali
- 📜 **History automatica**: ogni step applicato viene registrato con parametri e metriche
- 🔍 **Profiling integrato**: rileva problemi comuni con un comando
- 🔗 **Pipeline fluente**: API chainable, leggibile e componibile
- 🛠️ **Estensibilità**: crea facilmente `PipelineStep` custom per i tuoi casi
- 📦 **Recipe**: incapsula pipeline ricorrenti in classi riusabili
- ⚠️ **Gestione errori interattiva**: in caso di errore puoi continuare, saltare o abortire

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

## 🗺️ Roadmap

- [ ] `ColumnStep` helper per step su singole colonne
- [ ] Step aggiuntivi: `CastTypes`, `ParseDates`, `RenameColumns`, `RemoveOutliers`
- [ ] `report.suggest_pipeline()` — pipeline auto-generata dal profiling
- [ ] Backend astratto + supporto **DuckDB**
- [ ] Logging strutturato configurabile
- [ ] Documentazione con MkDocs

---

## 📄 License

MIT