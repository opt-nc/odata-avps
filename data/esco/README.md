# Annotations ESCO des AVPs

Ce dossier contient les annotations [ESCO](https://esco.ec.europa.eu/fr)
(European Skills, Competences, Qualifications and Occupations) des AVPs
publiées dans [`data/avps/`](../avps/) : **un fichier JSON par AVP**, même nom
de fichier que l'AVP source.

Les fichiers AVP source ne sont **pas modifiés** : les annotations vivent à part.

## Objectifs

1. **Mieux rédiger les AVPs** : vocabulaire métiers/compétences normalisé,
   suggestions de compétences typiques du métier (relations
   professions ↔ compétences d'ESCO)
2. **Automatiser la labellisation** des nouveaux AVPs (code ISCO-08 inclus)

## Référentiel

Les annotations pointent vers ESCO **v1.2.1 (français)** via la base DuckDB
[`adriens/odata-esco` v1.0.1](https://github.com/adriens/odata-esco/releases/tag/v1.0.1)
(3 039 professions, 13 939 compétences). La base (~108 Mo) est téléchargée et
cachée automatiquement par les scripts — elle n'est jamais commitée.

> ESCO © Union européenne, réutilisation autorisée avec mention de la source.

## Format d'un fichier d'annotation

Conforme à [`esco_annotation.schema.json`](esco_annotation.schema.json) :

```json
{
  "identifier": "3134-26-1049/SR",
  "source_file": "data/avps/3134-26-1049_SR.json",
  "source_sha256": "…",
  "esco_version": "v1.2.1",
  "esco_db": "adriens/odata-esco v1.0.1",
  "annotated_at": "2026-10-10",
  "annotation_method": "llm/claude-fable-5 + candidats lexicaux esco.duckdb",
  "occupations": [
    { "escoUri": "http://data.europa.eu/esco/occupation/…", "prefLabel_fr": "…",
      "iscoCode": "4211", "matchType": "close", "confidence": 0.85, "evidence": "…" }
  ],
  "skills": [
    { "escoUri": "http://data.europa.eu/esco/skill/…", "prefLabel_fr": "…",
      "skillType": "skill/competence", "matchType": "exact", "confidence": 0.95,
      "evidence": "…", "source_field": "skills" }
  ]
}
```

- `matchType` (esprit SKOS) : `exact` (même concept), `close` (même idée,
  granularité/formulation proche), `broad` (plus générique/partiel)
- `source_sha256` : SHA-256 du fichier AVP au moment de l'annotation —
  si l'AVP change, l'annotation est détectée **obsolète**
- `occupations: []` + `comment` est permis quand aucun métier ESCO ne convient

## Pipeline d'annotation (anti-hallucination)

```
data/avps/*.json
   │  scripts/esco/candidates.py        (pré-sélection lexicale dans esco.duckdb)
   ▼
build/esco_candidates/*.json
   │  annotation LLM                    (choix UNIQUEMENT parmi les candidats,
   │                                     recherches complémentaires via search_esco.py)
   ▼
build/esco_raw/*.json
   │  scripts/esco/finalize_annotations.py  (métadonnées + labels officiels depuis la base,
   │                                         rejet des URIs inconnues)
   ▼
data/esco/*.json
   │  scripts/esco/validate_annotations.py  (schéma + URIs + fraîcheur + couverture)
   ▼
   PR + revue humaine
```

Les URIs proposées par le LLM proviennent exclusivement des candidats extraits
de la base ; `finalize` réécrit les labels officiels et `validate` rejette toute
URI inconnue — une URI inventée ne peut pas atteindre `data/esco/`.

## Utilisation

```bash
# environnement
uv venv .venv && uv pip install -p .venv/bin/python duckdb jsonschema

# pré-sélection des candidats (tous les AVPs, ou une liste de stems)
.venv/bin/python scripts/esco/candidates.py [stem …]

# recherche libre dans le référentiel
cd scripts/esco && ../../.venv/bin/python search_esco.py occupation "guichetier" 8

# finalisation des annotations brutes (build/esco_raw → data/esco)
.venv/bin/python scripts/esco/finalize_annotations.py [stem …]

# validation complète
.venv/bin/python scripts/esco/validate_annotations.py --coverage

# export HuggingFace (build/all_esco.jsonl)
.venv/bin/python scripts/esco/export_hf.py
```

La CI ([`esco-annotations.yml`](../../.github/workflows/esco-annotations.yml))
valide les annotations à chaque PR et ouvre une issue quand des AVPs
nouveaux/modifiés n'ont pas d'annotation à jour.
