import os
import re
from datetime import datetime

# Chemin du dossier `content` relatif à la racine du dépôt
# (robuste quel que soit le CWD / la machine / la CI)
content_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
categories = [
    "commercial-et-clientele",
    "ressources-humaines",
    "poste-et-logistique",
    "telecommunications",
    "informatique-et-technologies",
    "administration-finance-et-juridique"
]

def validate_iso8601(timestamp_str):
    try:
        # Standard OKF format: YYYY-MM-DDTHH:MM:SSZ
        datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False

print("🔍 Lancement du validateur de conformité OKF (Open Knowledge Format)...")
print("-" * 70)

total_files = 0
valid_files = 0
errors = []

for category in categories:
    cat_dir = os.path.join(content_dir, category)
    if not os.path.exists(cat_dir):
        continue
    
    for filename in os.listdir(cat_dir):
        if not filename.endswith(".md") or filename == "_index.md":
            continue
            
        total_files += 1
        file_path = os.path.join(cat_dir, filename)
        relative_path = os.path.relpath(file_path, content_dir)
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            errors.append(f"❌ {relative_path} : Structure de fichier invalide (délimiteurs '---' manquants ou mal formés)")
            continue
            
        frontmatter = parts[1]
        
        # 1. Validation du champ 'type'
        type_match = re.search(r"^type:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        if not type_match:
            errors.append(f"❌ {relative_path} : Champ 'type' requis manquant")
            continue
        type_val = type_match.group(1).strip()
        if type_val != "JobPosting":
            errors.append(f"⚠️ {relative_path} : Type '{type_val}' non standard (recommandé: 'JobPosting')")
            
        # 2. Validation du champ 'timestamp'
        ts_match = re.search(r"^timestamp:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        if not ts_match:
            errors.append(f"❌ {relative_path} : Champ 'timestamp' requis par la spécification OKF manquant")
            continue
        ts_val = ts_match.group(1).strip()
        if not validate_iso8601(ts_val):
            errors.append(f"❌ {relative_path} : 'timestamp' '{ts_val}' n'est pas au format ISO 8601 UTC (ex: YYYY-MM-DDTHH:MM:SSZ)")
            continue
            
        # 3. Validation du champ 'resource'
        res_match = re.search(r"^resource:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        if not res_match:
            errors.append(f"❌ {relative_path} : Champ 'resource' (URI canonique) manquant")
            continue
        res_val = res_match.group(1).strip()
        if not res_val.startswith("https://opt-nc.github.io/odata-avps/"):
            errors.append(f"❌ {relative_path} : 'resource' '{res_val}' doit pointer vers le domaine canonique du site")
            continue
            
        # 4. Validation des recommandations (titre et description)
        title_match = re.search(r"^title:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        desc_match = re.search(r"^description:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        
        warnings = []
        if not title_match:
            warnings.append("titre manquant")
        if not desc_match:
            warnings.append("description manquante")
            
        if warnings:
            print(f"⚠️ {relative_path} : OKF valide mais des recommandations manquent ({', '.join(warnings)})")
        
        valid_files += 1

print("-" * 70)
if errors:
    print("\nDétails des erreurs rencontrées :")
    for err in errors:
        print(err)
    print("-" * 70)

print(f"\n📊 Résultat : {valid_files}/{total_files} fichiers validés avec succès comme conformes OKF.")
if valid_files == total_files:
    print("✅ Félicitations ! Votre graphe de connaissances est 100% conforme à la spécification OKF v0.1.")
else:
    print("❌ Des corrections sont nécessaires pour obtenir une conformité totale.")
