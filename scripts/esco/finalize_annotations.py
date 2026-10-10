#!/usr/bin/env python3
"""Finalise les annotations ESCO brutes produites par le LLM.

Lit `build/esco_raw/<stem>.json` (sortie LLM minimale) et produit
`data/esco/<stem>.json` conforme au schéma :
  - remplit source_file / source_sha256 / esco_version / esco_db / annotated_at
  - remplace prefLabel_fr, iscoCode et skillType par les valeurs officielles
    de la base ESCO (anti-hallucination : seule l'URI vient du LLM)
  - rejette toute URI absente de la base

Format d'entrée attendu (par le LLM) :
{
  "stem": "...",
  "comment": "..." (optionnel),
  "occupations": [{"escoUri", "matchType", "confidence", "evidence"}],
  "skills": [{"escoUri", "matchType", "confidence", "evidence", "source_field"}]
}

Usage : python scripts/esco/finalize_annotations.py [stem ...]
"""
import datetime
import hashlib
import json
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from download_esco_db import ensure_db, ESCO_RELEASE  # noqa: E402

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
AVPS_DIR = os.path.join(REPO_ROOT, "data", "avps")
RAW_DIR = os.path.join(REPO_ROOT, "build", "esco_raw")
OUT_DIR = os.path.join(REPO_ROOT, "data", "esco")

ANNOTATION_METHOD = "llm/claude-fable-5 + candidats lexicaux esco.duckdb"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(stems: list):
    con = duckdb.connect(ensure_db(), read_only=True)
    esco_version = con.execute("SELECT esco_version FROM build_info").fetchone()[0]
    occ = {
        r[0]: {"prefLabel_fr": r[1], "iscoCode": r[2]}
        for r in con.execute(
            "SELECT uri, preferred_label, isco_group_code FROM v_occupation"
        ).fetchall()
    }
    sk = {
        r[0]: {"prefLabel_fr": r[1], "skillType": r[2] or "skill/competence"}
        for r in con.execute("SELECT uri, preferred_label, skill_type FROM v_skill").fetchall()
    }
    con.close()

    os.makedirs(OUT_DIR, exist_ok=True)
    errors = 0
    for fn in sorted(os.listdir(RAW_DIR)):
        if not fn.endswith(".json"):
            continue
        stem = fn[:-5]
        if stems and stem not in stems:
            continue
        with open(os.path.join(RAW_DIR, fn), encoding="utf-8") as f:
            raw = json.load(f)
        src_rel = f"data/avps/{stem}.json"
        src_path = os.path.join(AVPS_DIR, f"{stem}.json")
        if not os.path.exists(src_path):
            print(f"❌ {stem}: AVP source introuvable")
            errors += 1
            continue
        with open(src_path, encoding="utf-8") as f:
            identifier = json.load(f).get("identifier")

        occupations, skills = [], []
        ok = True
        for o in raw.get("occupations", []):
            uri = o.get("escoUri")
            if uri not in occ:
                print(f"❌ {stem}: occupation inconnue dans ESCO — {uri}")
                ok = False
                continue
            occupations.append(
                {
                    "escoUri": uri,
                    "prefLabel_fr": occ[uri]["prefLabel_fr"],
                    "iscoCode": occ[uri]["iscoCode"],
                    "matchType": o["matchType"],
                    "confidence": o["confidence"],
                    "evidence": o["evidence"],
                }
            )
        for s in raw.get("skills", []):
            uri = s.get("escoUri")
            if uri not in sk:
                print(f"❌ {stem}: skill inconnue dans ESCO — {uri}")
                ok = False
                continue
            skills.append(
                {
                    "escoUri": uri,
                    "prefLabel_fr": sk[uri]["prefLabel_fr"],
                    "skillType": sk[uri]["skillType"],
                    "matchType": s["matchType"],
                    "confidence": s["confidence"],
                    "evidence": s["evidence"],
                    "source_field": s["source_field"],
                }
            )
        # dédoublonnage par URI (garde la meilleure confiance)
        skills_by_uri = {}
        for s in skills:
            prev = skills_by_uri.get(s["escoUri"])
            if prev is None or s["confidence"] > prev["confidence"]:
                skills_by_uri[s["escoUri"]] = s
        skills = sorted(skills_by_uri.values(), key=lambda s: -s["confidence"])

        ann = {
            "identifier": identifier,
            "source_file": src_rel,
            "source_sha256": sha256_file(src_path),
            "esco_version": esco_version,
            "esco_db": f"adriens/odata-esco {ESCO_RELEASE}",
            "annotated_at": datetime.date.today().isoformat(),
            "annotation_method": ANNOTATION_METHOD,
            "occupations": occupations,
            "skills": skills,
        }
        if raw.get("comment"):
            ann["comment"] = raw["comment"]
        out_path = os.path.join(OUT_DIR, fn)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(ann, f, ensure_ascii=False, indent=2)
            f.write("\n")
        status = "✅" if ok else "⚠️ "
        print(f"{status} {stem}: {len(occupations)} occupation(s), {len(skills)} skill(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
