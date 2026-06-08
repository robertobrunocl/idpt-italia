"""Recipe macrorefine specifiche del progetto idpt-italia.

Una Recipe per ciascuno dei 9 cubi del grafo (cubi 1-7 + cubo 8 IDPT computed
+ cubo 9 Plan B GDP). Ogni Recipe legge il CSV grezzo da `data/`, applica una
pipeline di step (built-in macrorefine + custom LOD-aware) e emette
``output/observations/cuboN_*.ttl`` con ``qb:Observation`` conformi alle DSD
in ``output/vocabularies/classes_and_properties.ttl``.

Le costanti URI usate dalle Recipe sono centralizzate in ``idpt_vocab.py``.
"""
