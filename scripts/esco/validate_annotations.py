#!/usr/bin/env python3
"""Validation des annotations ESCO (`data/esco/*.json`).

Contrôles effectués :
  1. Conformité au JSON Schema (`data/esco/esco_annotation.schema.json`)
  2. Chaque escoUri d'occupation existe dans esco.duckdb et le prefLabel_fr correspond
  3. Chaque escoUri de skill existe dans esco.duckdb et le prefLabel_fr correspond
  4. Le fichier AVP source existe et son SHA-256 correspond (sinon → obsolète)
  5. Chaque AVP de data/avps/ possède une annotation (mode --coverage)

Sortie non-nulle si au moins une erreur. Les annotations obsolètes sont
signalées en avertissement (erreur avec --strict).

Usage : python scripts/esco/validate_annotations.py [--coverage] [--strict]
"""
import hashlib
import json
import os
import re
import sys

import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from download_esco_db import ensure_db  # noqa: E402

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
AVPS_DIR = os.path.join(REPO_ROOT, "data", "avps")
ESCO_DIR = os.path.join(REPO_ROOT, "data", "esco")
SCHEMA_PATH = os.path.join(ESCO_DIR, "esco_annotation.schema.json")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_schema(ann: dict, schema: dict, errors: list, name: str):
    try:
        import jsonschema

        validator = jsonschema.Draft202012Validator(schema)
        for err in validator.iter_errors(ann):
            errors.append(f"{name}: schéma invalide — {err.message}")
        return
    except ImportError:
        pass
    # Fallback minimal sans jsonschema
    for key in schema["required"]:
        if key not in ann:
            errors.append(f"{name}: champ requis manquant '{key}'")
    for occ in ann.get("occupations", []):
        if not re.match(r"^http://data\.europa\.eu/esco/occupation/[0-9a-f-]{36}$", occ.get("escoUri", "")):
            errors.append(f"{name}: URI occupation invalide {occ.get('escoUri')}")
        if occ.get("matchType") not in ("exact", "close", "broad"):
            errors.append(f"{name}: matchType occupation invalide")
    for sk in ann.get("skills", []):
        if not re.match(r"^http://data\.europa\.eu/esco/skill/[0-9a-f-]{36}$", sk.get("escoUri", "")):
            errors.append(f"{name}: URI skill invalide {sk.get('escoUri')}")
        if sk.get("matchType") not in ("exact", "close", "broad"):
            errors.append(f"{name}: matchType skill invalide")
    if not DATE_RE.match(ann.get("annotated_at", "")):
        errors.append(f"{name}: annotated_at invalide")


def main():
    strict = "--strict" in sys.argv
    coverage = "--coverage" in sys.argv
    errors, warnings = [], []

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)

    con = duckdb.connect(ensure_db(), read_only=True)
    occ_labels = dict(con.execute("SELECT uri, preferred_label FROM v_occupation").fetchall())
    skill_labels = dict(con.execute("SELECT uri, preferred_label FROM v_skill").fetchall())
    con.close()

    ann_files = sorted(
        f for f in os.listdir(ESCO_DIR) if f.endswith(".json") and not f.endswith(".schema.json")
    )
    annotated_stems = set()

    for fn in ann_files:
        name = f"data/esco/{fn}"
        with open(os.path.join(ESCO_DIR, fn), encoding="utf-8") as f:
            try:
                ann = json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"{name}: JSON invalide — {e}")
                continue

        validate_schema(ann, schema, errors, name)

        for occ in ann.get("occupations", []):
            uri = occ.get("escoUri")
            if uri not in occ_labels:
                errors.append(f"{name}: occupation inconnue dans ESCO — {uri}")
            elif occ.get("prefLabel_fr") != occ_labels[uri]:
                errors.append(
                    f"{name}: prefLabel_fr occupation incohérent — "
                    f"'{occ.get('prefLabel_fr')}' != '{occ_labels[uri]}' ({uri})"
                )
        for sk in ann.get("skills", []):
            uri = sk.get("escoUri")
            if uri not in skill_labels:
                errors.append(f"{name}: skill inconnue dans ESCO — {uri}")
            elif sk.get("prefLabel_fr") != skill_labels[uri]:
                errors.append(
                    f"{name}: prefLabel_fr skill incohérent — "
                    f"'{sk.get('prefLabel_fr')}' != '{skill_labels[uri]}' ({uri})"
                )

        src = ann.get("source_file", "")
        src_path = os.path.join(REPO_ROOT, src)
        if not os.path.exists(src_path):
            errors.append(f"{name}: fichier source introuvable — {src}")
        else:
            annotated_stems.add(os.path.splitext(os.path.basename(src))[0])
            actual = sha256_file(src_path)
            if actual != ann.get("source_sha256"):
                msg = f"{name}: annotation OBSOLÈTE (sha256 source modifié)"
                (errors if strict else warnings).append(msg)

    if coverage:
        for fn in sorted(os.listdir(AVPS_DIR)):
            if fn.endswith(".json") and os.path.splitext(fn)[0] not in annotated_stems:
                msg = f"data/avps/{fn}: aucune annotation ESCO"
                (errors if strict else warnings).append(msg)

    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    n_ann = len(ann_files)
    print(f"\n📊 {n_ann} annotations vérifiées — {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
