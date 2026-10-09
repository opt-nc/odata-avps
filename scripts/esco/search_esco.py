#!/usr/bin/env python3
"""Recherche lexicale libre dans le référentiel ESCO (esco.duckdb).

Permet de compléter la pré-sélection automatique lors de l'annotation :
toutes les URIs retournées proviennent de la base (ancrage anti-hallucination).

Usage :
  python scripts/esco/search_esco.py occupation "guichetier" [k]
  python scripts/esco/search_esco.py skill "relation client" [k]
"""
import json
import sys

import duckdb

from candidates import LexicalIndex
from download_esco_db import ensure_db


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("occupation", "skill"):
        print(__doc__)
        sys.exit(2)
    concept_type, query = sys.argv[1], sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    con = duckdb.connect(ensure_db(), read_only=True)
    index = LexicalIndex(con, concept_type)
    matches = index.search(query, k)
    out = []
    if concept_type == "occupation":
        for uri, score in matches.items():
            r = con.execute(
                "SELECT preferred_label, isco_group_code, description FROM v_occupation WHERE uri = ?",
                [uri],
            ).fetchone()
            out.append(
                {
                    "escoUri": uri,
                    "prefLabel_fr": r[0],
                    "iscoCode": r[1],
                    "description": (r[2] or "")[:300],
                    "lexicalScore": round(score, 3),
                }
            )
    else:
        for uri, score in matches.items():
            r = con.execute(
                "SELECT preferred_label, skill_type, description FROM v_skill WHERE uri = ?",
                [uri],
            ).fetchone()
            out.append(
                {
                    "escoUri": uri,
                    "prefLabel_fr": r[0],
                    "skillType": r[1],
                    "description": (r[2] or "")[:300],
                    "lexicalScore": round(score, 3),
                }
            )
    con.close()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
