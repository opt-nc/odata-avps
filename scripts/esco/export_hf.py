#!/usr/bin/env python3
"""Agrège les annotations ESCO unitaires en un fichier JSONL pour HuggingFace.

Produit `build/all_esco.jsonl` (une ligne par AVP annoté), à publier dans le
dataset HuggingFace `opt-nc/odata-avps` sous `data/all_esco.jsonl`.

Usage : python scripts/esco/export_hf.py [chemin_sortie]
"""
import json
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
ESCO_DIR = os.path.join(REPO_ROOT, "data", "esco")
DEFAULT_OUT = os.path.join(REPO_ROOT, "build", "all_esco.jsonl")


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    rows = []
    for fn in sorted(os.listdir(ESCO_DIR)):
        if not fn.endswith(".json") or fn.endswith(".schema.json"):
            continue
        with open(os.path.join(ESCO_DIR, fn), encoding="utf-8") as f:
            rows.append(json.load(f))
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"✅ {len(rows)} annotations exportées vers {out_path}")


if __name__ == "__main__":
    main()
