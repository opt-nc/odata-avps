#!/usr/bin/env python3
"""Pré-sélection de candidats ESCO (occupations + skills) pour chaque AVP.

Pour chaque fichier `data/avps/*.json`, produit un fichier de travail
`build/esco_candidates/<stem>.json` contenant :
  - un résumé compact de l'AVP (titre, description, responsabilités, compétences)
  - le top-N des occupations ESCO candidates (match lexical FR)
  - le top-N des skills ESCO candidates par libellé de compétence de l'AVP

Ces candidats servent d'ancrage anti-hallucination : l'annotation LLM ne peut
choisir des URIs QUE parmi ces candidats, validés ensuite contre la base.

Usage : python scripts/esco/candidates.py [stem ...]
"""
import json
import os
import sys
import unicodedata

import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from download_esco_db import ensure_db  # noqa: E402

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
AVPS_DIR = os.path.join(REPO_ROOT, "data", "avps")
OUT_DIR = os.path.join(REPO_ROOT, "build", "esco_candidates")

TOP_OCCUPATIONS = 15
TOP_SKILLS_PER_LABEL = 5


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def avp_summary(avp: dict) -> dict:
    er = avp.get("educationRequirements") or {}
    rel = avp.get("relevantOccupation") or {}
    return {
        "identifier": avp.get("identifier"),
        "title": avp.get("title") or avp.get("name"),
        "relevantOccupation": rel.get("name"),
        "occupationalCategory": avp.get("occupationalCategory"),
        "industry": avp.get("industry"),
        "description": avp.get("description"),
        "responsibilities": avp.get("responsibilities"),
        "skills": avp.get("skills"),
        "competencyRequired": er.get("competencyRequired"),
        "qualifications": avp.get("qualifications"),
    }


def occupation_queries(avp: dict) -> list:
    rel = avp.get("relevantOccupation") or {}
    queries = [avp.get("title") or avp.get("name"), rel.get("name")]
    queries += list(avp.get("occupationalCategory") or [])
    seen, out = set(), []
    for q in queries:
        if q and norm(q) not in seen:
            seen.add(norm(q))
            out.append(q)
    return out


def skill_labels(avp: dict) -> list:
    er = avp.get("educationRequirements") or {}
    labels = list(avp.get("skills") or []) + list(er.get("competencyRequired") or [])
    seen, out = set(), []
    for l in labels:
        if l and norm(l) not in seen:
            seen.add(norm(l))
            out.append(l)
    return out


STOPWORDS = {
    "de", "du", "des", "la", "le", "les", "l", "d", "un", "une", "et", "ou",
    "en", "a", "au", "aux", "pour", "par", "sur", "dans", "avec", "sans",
    "ses", "son", "sa", "leurs", "leur", "ce", "cette", "ces", "qui", "que",
    "est", "sont", "the", "of", "and",
}


def tokens(s: str) -> set:
    """Tokens normalisés, sans stopwords, avec stemming léger (pluriels)."""
    out = set()
    for t in "".join(c if c.isalnum() else " " for c in norm(s)).split():
        if t in STOPWORDS or len(t) < 2:
            continue
        if len(t) > 3 and t.endswith(("s", "x")):
            t = t[:-1]
        out.add(t)
    return out


class LexicalIndex:
    """Index lexical TF-IDF simplifié sur les labels ESCO (pref + alternatifs)."""

    def __init__(self, con, concept_type: str):
        import math
        from collections import defaultdict

        rows = con.execute(
            "SELECT label_normalized, concept_uri FROM concept_label WHERE concept_type = ?",
            [concept_type],
        ).fetchall()
        self.entries = []  # (token_set, label, uri)
        df = defaultdict(int)
        for label, uri in rows:
            tk = tokens(label)
            if not tk:
                continue
            self.entries.append((tk, label, uri))
            for t in tk:
                df[t] += 1
        n = len(self.entries)
        self.idf = {t: math.log(n / c) for t, c in df.items()}
        self.default_idf = math.log(n)

    def search(self, query: str, k: int) -> dict:
        """Top-k URIs : couverture IDF des tokens de la requête par le label."""
        qt = tokens(query)
        if not qt:
            return {}
        q_weight = sum(self.idf.get(t, self.default_idf) for t in qt)
        scored = {}
        for tk, label, uri in self.entries:
            inter = qt & tk
            if not inter:
                continue
            cov_q = sum(self.idf.get(t, self.default_idf) for t in inter) / q_weight
            cov_l = len(inter) / len(tk)
            score = 0.75 * cov_q + 0.25 * cov_l
            if score > scored.get(uri, 0.0):
                scored[uri] = score
        return dict(sorted(scored.items(), key=lambda x: -x[1])[:k])


def top_occupations(con, index: "LexicalIndex", queries: list, k: int) -> list:
    """Top-k occupations par similarité lexicale (labels + alt labels)."""
    scored = {}
    for q in queries:
        for uri, score in index.search(q, k).items():
            scored[uri] = max(scored.get(uri, 0.0), score)
    best = sorted(scored.items(), key=lambda x: -x[1])[:k]
    if not best:
        return []
    uris = [u for u, _ in best]
    details = con.execute(
        """
        SELECT uri, preferred_label, description, alt_labels,
               isco_group_code, isco_unit_group_label
        FROM v_occupation WHERE uri IN (SELECT unnest(?::VARCHAR[]))
        """,
        [uris],
    ).fetchall()
    by_uri = {d[0]: d for d in details}
    out = []
    for uri, score in best:
        d = by_uri.get(uri)
        if not d:
            continue
        out.append(
            {
                "escoUri": uri,
                "prefLabel_fr": d[1],
                "description": (d[2] or "")[:400],
                "altLabels": (d[3] or [])[:6],
                "iscoCode": d[4],
                "iscoLabel": d[5],
                "lexicalScore": round(score, 3),
            }
        )
    return out


def top_skills(con, index: "LexicalIndex", avp_labels: list, k: int) -> dict:
    """Pour chaque libellé de compétence AVP, top-k skills ESCO candidates."""
    out = {}
    for label in avp_labels:
        matches = index.search(label, k)
        if not matches:
            out[label] = []
            continue
        details = con.execute(
            """
            SELECT uri, preferred_label, skill_type FROM v_skill
            WHERE uri IN (SELECT unnest(?::VARCHAR[]))
            """,
            [list(matches)],
        ).fetchall()
        by_uri = {d[0]: d for d in details}
        out[label] = [
            {
                "escoUri": uri,
                "prefLabel_fr": by_uri[uri][1],
                "skillType": by_uri[uri][2],
                "lexicalScore": round(score, 3),
            }
            for uri, score in matches.items()
            if uri in by_uri
        ]
    return out


def occupation_skills(con, occupation_uris: list, limit: int = 60) -> list:
    """Skills essentielles/optionnelles des occupations retenues (pour la phase 2)."""
    if not occupation_uris:
        return []
    rows = con.execute(
        """
        SELECT DISTINCT skill_uri, skill_label, skill_type, relation_type
        FROM v_occupation_skill
        WHERE occupation_uri IN (SELECT unnest(?::VARCHAR[]))
        ORDER BY relation_type, skill_label
        LIMIT ?
        """,
        [occupation_uris, limit],
    ).fetchall()
    return [
        {
            "escoUri": r[0],
            "prefLabel_fr": r[1],
            "skillType": r[2],
            "relationType": r[3],
        }
        for r in rows
    ]


def main(stems: list):
    db = ensure_db()
    con = duckdb.connect(db, read_only=True)
    occ_index = LexicalIndex(con, "occupation")
    skill_index = LexicalIndex(con, "skill")
    os.makedirs(OUT_DIR, exist_ok=True)
    files = sorted(os.listdir(AVPS_DIR))
    for fn in files:
        if not fn.endswith(".json"):
            continue
        stem = fn[:-5]
        if stems and stem not in stems:
            continue
        with open(os.path.join(AVPS_DIR, fn), encoding="utf-8") as f:
            avp = json.load(f)
        result = {
            "stem": stem,
            "avp": avp_summary(avp),
            "candidate_occupations": top_occupations(
                con, occ_index, occupation_queries(avp), TOP_OCCUPATIONS
            ),
            "candidate_skills_by_label": top_skills(
                con, skill_index, skill_labels(avp), TOP_SKILLS_PER_LABEL
            ),
        }
        out_path = os.path.join(OUT_DIR, f"{stem}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ {stem} : {len(result['candidate_occupations'])} occupations candidates")
    con.close()


if __name__ == "__main__":
    main(sys.argv[1:])
