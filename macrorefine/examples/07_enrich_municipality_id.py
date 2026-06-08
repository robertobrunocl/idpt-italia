"""
Esempio 07: arricchimento del dataset rifiuti con ID_COMUNE, sigla automobilistica 
e normalizzazione dei numeri italiani.

Tre dataset:
    - rifiuti     (COMUNE, PROVINCIA estesa, valori numerici in formato IT, ...)
    - province    (Provincia/Uts estesa, Codice Provincia, Sigla automobilistica)
    - cities      (LABEL_COMUNE_IT, CODICE_PROVINCIA, ID_COMUNE, validità)

Obiettivo: portare ID_COMUNE e SIGLA AUTOMOBILISTICA nel dataset rifiuti, gestendo:
    1. Parsing universale dei numeri italiani (es. 9.999,9) e percentuali (es. 45,5%)
    2. Omonimie tra comuni → join su (comune, codice_provincia)
    3. Provincia estesa vs codice_provincia → primo join via dataset province
    4. Storico e univocità dei comuni → tieni le righe valide e rimuovi i duplicati
"""
import re
from pathlib import Path

import pandas as pd

from macrorefine import Dataset, Pipeline, PipelineStep, Recipe
from macrorefine.history import StepRecord
from macrorefine.steps import (
    AddNormalizedKey,
    DropColumns,
    FilterRows,
    LeftJoinEnrich,
    NormalizeColumnNames,
    ParseDates,
    RenameColumns,
)


# --- Step Custom 1: Parsing universale numeri italiani ---
class ParseItalianNumbers(PipelineStep):
    """
    Scansiona le colonne testuali per convertire i numeri in formato italiano
    (es. '9.999,9') e percentuali (es. '45,5%') in float nativi.
    Se la colonna contiene solo numeri interi, rimuove i decimali convertendola in Int64.
    """

    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        
        # Regex per intercettare: opzionale meno, migliaia col punto, decimali con virgola, opzionale %
        pattern = re.compile(r'^\s*(-?(?:\d{1,3}(?:\.\d{3})*|\d+)(?:,\d+)?)\s*(%?)\s*$')

        def parse_val(val):
            if pd.isna(val):
                return val
            val_str = str(val).strip()
            match = pattern.match(val_str)
            if not match:
                return val  # Non è un numero riconoscibile

            num_str = match.group(1)
            # Rimuove il punto delle migliaia e sostituisce la virgola decimale col punto
            clean_num = num_str.replace('.', '').replace(',', '.')
            
            try:
                return float(clean_num)
            except ValueError:
                return val

        changed_cols = []
        for col in df.columns:
            original = df[col].copy()
            df[col] = df[col].apply(parse_val)
            
            if not original.equals(df[col]):
                changed_cols.append(col)
                
                # Equivalente sicuro di errors='ignore' compatibile con le nuove versioni di pandas
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass  # Se ci sono stringhe che non sono numeri, le lasciamo stare
                
                # Se è un float ma tutti i valori sono interi (es. Popolazione),
                # lo castiamo a Int64 per rimuovere il .0 ed esportarlo in modo pulito
                if pd.api.types.is_float_dtype(df[col]):
                    if df[col].dropna().apply(lambda x: x.is_integer()).all():
                        df[col] = df[col].astype("Int64")

        record = StepRecord(
            name=self.name,
            metrics={"parsed_columns": changed_cols}
        )
        return dataset.with_data(df, step_record=record)


# --- Step Custom 2: Garantisce l'univocità della chiave di join ---
class KeepUniqueCity(PipelineStep):
    """
    Rimuove i duplicati basandosi sulla chiave di join (_comune_key e codice_provincia)
    evitando l'esplosione delle righe durante il Left Join.
    """
    def apply(self, dataset: Dataset) -> Dataset:
        df = dataset.to_pandas()
        before = len(df)
        df = df.drop_duplicates(subset=["_comune_key", "codice_provincia"]).reset_index(drop=True)
        after = len(df)
        
        record = StepRecord(
            name=self.name,
            metrics={"removed_duplicates": before - after}
        )
        return dataset.with_data(df, step_record=record)


# --- Recipe: prepara il vocabolario delle città ---
class CitiesPreparationRecipe(Recipe):
    def build(self) -> Pipeline:
        return (
            Pipeline(on_error="raise")
            .add(NormalizeColumnNames())
            .add(ParseDates(columns="data_fine_validita", errors="coerce"))
            # 1. Filtro temporale (solo quelli attivi)
            .add(FilterRows(predicate=lambda df: (
                df["data_fine_validita"].isna()
                | (df["data_fine_validita"] == pd.Timestamp("9999-12-31"))
            )))
            .add(AddNormalizedKey(source="label_comune_it", target="_comune_key"))
            # 2. Rimuove eventuali chiavi duplicate rimaste per variazioni storiche
            .add(KeepUniqueCity())
        )


# --- Recipe: prepara il vocabolario delle province ---
class ProvincePreparationRecipe(Recipe):
    def build(self) -> Pipeline:
        return (
            Pipeline(on_error="raise")
            .add(NormalizeColumnNames())
            .add(RenameColumns(mapping={
                "provincia_uts": "provincia",
                "codice_provincia_storico": "codice_provincia",
            }))
            .add(AddNormalizedKey(source="provincia", target="_provincia_key"))
        )


# --- Recipe: pulizia iniziale e arricchimento del dataset rifiuti ---
class WasteEnrichmentRecipe(Recipe):
    def __init__(self, provinces: Dataset, cities: Dataset) -> None:
        self.provinces = provinces
        self.cities = cities

    def build(self) -> Pipeline:
        return (
            Pipeline(on_error="raise")
            .add(NormalizeColumnNames())
            # 1. Parsing globale dei numeri sporchi italiani
            .add(ParseItalianNumbers())
            # 2. Setup chiavi per i join
            .add(AddNormalizedKey(source="provincia", target="_provincia_key"))
            .add(AddNormalizedKey(source="comune", target="_comune_key"))
            # 3. Primo join: portiamo codice_provincia e sigla_automobilistica
            .add(LeftJoinEnrich(
                other=self.provinces,
                left_on="_provincia_key",
                right_on="_provincia_key",
                columns=["codice_provincia", "sigla_automobilistica"],
            ))
            # 4. Secondo join: (comune, codice_provincia) → id_comune
            .add(LeftJoinEnrich(
                other=self.cities,
                left_on=["_comune_key", "codice_provincia"],
                right_on=["_comune_key", "codice_provincia"],
                columns=["id_comune"],
            ))
            # 5. Pulizia colonne ausiliarie usate per i join
            .add(DropColumns(columns=[
                "_comune_key",
                "_provincia_key",
                "codice_provincia",
            ]))
        )


def main() -> None:
    DATA_DIR = Path(__file__).parent / "data"

    # ============================================================
    # 1. Caricamento dei tre CSV
    # IMPORTANTE: `dtype=str` impedisce a pandas di corrompere i
    # numeri col punto delle migliaia durante la lettura iniziale!
    # ============================================================
    province_raw = Dataset.from_csv(DATA_DIR / "province.csv", sep=";", encoding="utf-8", dtype=str)
    cities_raw = Dataset.from_csv(DATA_DIR / "cities.csv", sep=",", encoding="utf-8", dtype=str)
    waste_raw = Dataset.from_csv(DATA_DIR / "rifiuti.csv", sep=",", encoding="utf-8", dtype=str)

    # ============================================================
    # 2. Preparazione dei due dataset di lookup
    # ============================================================
    provinces = ProvincePreparationRecipe().apply(province_raw)
    cities = CitiesPreparationRecipe().apply(cities_raw)

    # ============================================================
    # 3. Pulizia e Arricchimento del dataset rifiuti
    # ============================================================
    enriched = WasteEnrichmentRecipe(
        provinces=provinces,
        cities=cities,
    ).apply(waste_raw)

    print("\n=== RIFIUTI (pulito e arricchito) ===")
    print(enriched.to_pandas().head(10))

    # ============================================================
    # 4. Report match / mismatch
    # ============================================================
    out = enriched.to_pandas()
    matched = int(out["id_comune"].notna().sum())
    total = len(out)
    
    print(f"\n=== REPORT ===")
    print(f"Match riusciti: {matched}/{total}")
    if matched < total:
        unmatched = out[out["id_comune"].isna()][["comune", "provincia"]]
        print("Comuni senza match:")
        print(unmatched.to_string(index=False))
    
    # ============================================================
    # 5. Salvataggio
    # ============================================================
    from macrorefine import save_dataset
    OUT_DIR = Path(__file__).parent / "output"
    
    out_path = save_dataset(
        enriched,
        OUT_DIR / "rifiuti_arricchito.csv",
        save_history=True,
        sep=";",
        decimal=",",  # <-- IMPEDISCE A EXCEL DI INTERPRETARE I NUMERI COME ORARI
    )
    
    print(f"\n✅ Dataset salvato in: {out_path}")

if __name__ == "__main__":
    main()