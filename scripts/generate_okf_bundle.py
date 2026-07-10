"""Génère le bundle OKF (Open Knowledge Format v0.1) sous static/okf/.

Format canonique = les fiches Markdown + front-matter (déjà conformes OKF : type /
timestamp / resource). Ce script produit, à partir de TOUTES les fiches JobPosting de
content/ (quelle que soit leur organisation en dossiers) :

  - static/okf/index.md    : index humain À PLAT, chaque entrée portant ses facettes
                             (famille, direction, ville, ROME, métier) + lien canonique.
  - static/okf/index.jsonl : export MACHINE (1 ligne = 1 AVP, toutes les facettes) →
                             tri / filtre / regroupement laissés au consommateur.

Stdlib uniquement (pas de dépendance externe en CI).
"""
import os
import re
import json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
OKF_DIR = os.path.join(ROOT, "static", "okf")


def parse_frontmatter(text):
    """Parse le front-matter (entre les deux premiers '---') en dict.
    Le pipeline émet des valeurs JSON-compatibles (via json.dumps), donc json.loads
    dé-quote proprement chaînes, listes et nombres ; repli en texte brut sinon."""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = {}
    for line in parts[1].splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw == "":
            fm[key] = None
            continue
        try:
            fm[key] = json.loads(raw)
        except Exception:
            fm[key] = raw.strip('"')
    return fm


def collect_jobpostings():
    records = []
    for dirpath, _dirs, files in os.walk(CONTENT_DIR):
        for fn in sorted(files):
            if not fn.endswith(".md") or fn == "_index.md":
                continue
            with open(os.path.join(dirpath, fn), "r", encoding="utf-8") as f:
                fm = parse_frontmatter(f.read())
            if not fm or fm.get("type") != "JobPosting":
                continue
            fams = fm.get("families_metier") or []
            if isinstance(fams, str):
                fams = [fams]
            records.append({
                "identifier": fm.get("ref"),
                "title": fm.get("title"),
                "description": fm.get("description"),
                "resource": fm.get("resource"),
                "timestamp": fm.get("timestamp"),
                "datePosted": fm.get("date"),
                "validThrough": fm.get("date_cloture"),
                "familles_metier": fams,
                "direction": fm.get("direction"),
                "ville": fm.get("ville"),
                "code_rome": fm.get("code_rome"),
                "libelle_rome": fm.get("libelle_rome"),
                "metier_reference": fm.get("metier_ref_nom"),
                "code_metier": fm.get("code_metier_ref"),
                "fiche_metier_url": fm.get("url_fiche_metier"),
            })
    # Tri : date de publication décroissante, puis référence.
    records.sort(key=lambda r: (r.get("datePosted") or "", r.get("identifier") or ""), reverse=True)
    return records


def _clean(v):
    return v not in (None, "", [], "Non spécifié")


def main():
    os.makedirs(OKF_DIR, exist_ok=True)
    print("📁 Génération du bundle OKF sous static/okf...")
    records = collect_jobpostings()

    # 1. Manifeste MACHINE (JSONL) — 1 ligne = 1 AVP, toutes les facettes.
    jsonl_path = os.path.join(OKF_DIR, "index.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"📝 Manifeste machine : {jsonl_path} ({len(records)} fiches)")

    # 2. Index HUMAIN (Markdown) — à plat, facettes en ligne, lien canonique.
    lines = [
        "---",
        'type: "index"',
        'title: "Index des Offres d\'Emploi de l\'OPT-NC (Open Knowledge Format)"',
        'description: "Index à plat des Avis de Vacances de Poste (AVP) de l\'OPT-NC au format OKF v0.1. Chaque entrée porte ses facettes (famille, direction, ville, ROME, métier) ; le flux machine est disponible dans index.jsonl."',
        "---",
        "",
        "# Index des Offres d'Emploi de l'OPT-NC (Open Knowledge Format)",
        "",
        f"{len(records)} offre(s). Flux machine : [`index.jsonl`](./index.jsonl).",
        "",
    ]
    for r in records:
        title = r.get("title") or r.get("identifier") or "Offre"
        url = r.get("resource") or ""
        entry = f"- [{title}]({url})" if url else f"- {title}"
        facets = []
        if _clean(r.get("familles_metier")):
            facets.append("Famille(s) : " + ", ".join(r["familles_metier"]))
        if _clean(r.get("direction")):
            facets.append("Direction : " + r["direction"])
        if _clean(r.get("ville")):
            facets.append("Ville : " + r["ville"])
        if _clean(r.get("code_rome")):
            facets.append("ROME : " + r["code_rome"])
        if _clean(r.get("code_metier")):
            facets.append("Métier : " + r["code_metier"])
        if facets:
            entry += "  \n  " + " · ".join(facets)
        if _clean(r.get("description")):
            entry += "  \n  *" + r["description"] + "*"
        lines.append(entry)

    with open(os.path.join(OKF_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"🎉 Bundle OKF généré : index.md + index.jsonl ({len(records)} fiches).")


if __name__ == "__main__":
    main()
