import os
import re
import shutil

static_okf_dir = "static/okf"
content_dir = "content"
categories = [
    "commercial-et-clientele",
    "ressources-humaines",
    "poste-et-logistique",
    "telecommunications",
    "informatique-et-technologies",
    "administration-finance-et-juridique"
]

print("📁 Génération du bundle OKF sous static/okf...")

# Ensure static/okf folder exists
os.makedirs(static_okf_dir, exist_ok=True)

# Generate static/okf/index.md (without YAML frontmatter)
index_path = os.path.join(static_okf_dir, "index.md")
print(f"📝 Génération de l'index OKF : {index_path}...")

markdown_lines = [
    "---",
    'type: "index"',
    'title: "Index des Offres d\'Emploi de l\'OPT-NC (Open Knowledge Format)"',
    'description: "Ce dossier contient l\'index et les fiches de concepts des Avis de Vacances de Poste (AVP) de l\'OPT Nouvelle-Calédonie au format standardisé OKF (Open Knowledge Format v0.1)."',
    "---",
    "",
    "# Index des Offres d'Emploi de l'OPT-NC (Open Knowledge Format)",
    "",
    "Ce dossier contient l'index et les fiches de concepts des Avis de Vacances de Poste (AVP) de l'OPT Nouvelle-Calédonie au format standardisé OKF (Open Knowledge Format v0.1).",
    "",
    "## Catégories d'emplois",
    ""
]

category_labels = {
    "commercial-et-clientele": "Commercial et clientèle",
    "ressources-humaines": "Ressources humaines",
    "poste-et-logistique": "Poste et logistique",
    "telecommunications": "Télécommunications",
    "informatique-et-technologies": "Informatique et technologies",
    "administration-finance-et-juridique": "Administration, finance et juridique"
}

for category in categories:
    cat_dir = os.path.join(content_dir, category)
    if not os.path.exists(cat_dir):
        continue
    
    label = category_labels.get(category, category.replace("-", " ").capitalize())
    
    # Gather and sort all job postings in this category
    postings = []
    for filename in sorted(os.listdir(cat_dir)):
        if not filename.endswith(".md") or filename == "_index.md":
            continue
            
        file_path = os.path.join(cat_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
            
        frontmatter = parts[1]
        
        # Check if type: "JobPosting" is present
        type_match = re.search(r"^type:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        if not type_match or type_match.group(1).strip() != "JobPosting":
            continue
            
        title_match = re.search(r"^title:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else filename
        
        desc_match = re.search(r"^description:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        desc = desc_match.group(1).strip() if desc_match else ""
        
        postings.append({
            "title": title,
            "filename": filename,
            "description": desc
        })
        
    if postings:
        markdown_lines.append(f"### {label}")
        markdown_lines.append("")
        for post in postings:
            desc_part = f" - *{post['description']}*" if post['description'] else ""
            markdown_lines.append(f"- [{post['title']}](./{category}/{post['filename']}){desc_part}")
        markdown_lines.append("")

with open(index_path, "w", encoding="utf-8") as f:
    f.write("\n".join(markdown_lines))

print("🎉 Bundle OKF généré avec succès !")
