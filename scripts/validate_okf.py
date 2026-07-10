"""Validateur de conformité OKF (Open Knowledge Format v0.1).

Parcourt TOUTES les fiches JobPosting de content/ (quelle que soit leur organisation
en dossiers) et vérifie les champs requis par la spécification OKF :
  - type       = "JobPosting"
  - timestamp  = ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)
  - resource   = URI canonique du site
Recommandés : title, description.

Stdlib uniquement. Code retour non nul si des erreurs sont trouvées (utilisable en CI).
"""
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "content")
CANONICAL_PREFIX = "https://opt-nc.github.io/odata-avps/"


def validate_iso8601(ts):
    try:
        datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def field(frontmatter, name):
    m = re.search(rf"^{name}:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
    return m.group(1).strip() if m else None


print("🔍 Lancement du validateur de conformité OKF (Open Knowledge Format v0.1)...")
print("-" * 70)

total_files = 0
valid_files = 0
errors = []

for dirpath, _dirs, files in os.walk(CONTENT_DIR):
    for filename in sorted(files):
        if not filename.endswith(".md") or filename == "_index.md":
            continue

        file_path = os.path.join(dirpath, filename)
        relative_path = os.path.relpath(file_path, CONTENT_DIR)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        parts = content.split("---", 2)
        if len(parts) < 3:
            continue  # pas de front-matter → pas une fiche OKF
        frontmatter = parts[1]

        # On ne valide que les fiches-concepts (JobPosting) ; on ignore les autres pages.
        type_val = field(frontmatter, "type")
        if type_val != "JobPosting":
            continue

        total_files += 1

        # 1. timestamp requis, au format ISO 8601 UTC.
        ts_val = field(frontmatter, "timestamp")
        if not ts_val:
            errors.append(f"❌ {relative_path} : champ 'timestamp' requis manquant")
            continue
        if not validate_iso8601(ts_val):
            errors.append(f"❌ {relative_path} : 'timestamp' '{ts_val}' non conforme ISO 8601 UTC (YYYY-MM-DDTHH:MM:SSZ)")
            continue

        # 2. resource requis, pointant vers le domaine canonique.
        res_val = field(frontmatter, "resource")
        if not res_val:
            errors.append(f"❌ {relative_path} : champ 'resource' (URI canonique) manquant")
            continue
        if not res_val.startswith(CANONICAL_PREFIX):
            errors.append(f"❌ {relative_path} : 'resource' '{res_val}' doit commencer par {CANONICAL_PREFIX}")
            continue

        # 3. Recommandations : titre + description.
        warnings = []
        if not field(frontmatter, "title"):
            warnings.append("titre manquant")
        if not field(frontmatter, "description"):
            warnings.append("description manquante")
        if warnings:
            print(f"⚠️ {relative_path} : OKF valide mais recommandations manquantes ({', '.join(warnings)})")

        valid_files += 1

print("-" * 70)
if errors:
    print("\nDétails des erreurs rencontrées :")
    for err in errors:
        print(err)
    print("-" * 70)

print(f"\n📊 Résultat : {valid_files}/{total_files} fiches JobPosting conformes OKF.")
if total_files and valid_files == total_files:
    print("✅ Conformité OKF v0.1 : 100%.")
else:
    print("❌ Des corrections sont nécessaires pour une conformité totale.")
    sys.exit(1)
