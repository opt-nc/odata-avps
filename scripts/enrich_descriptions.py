import os
import re

content_dir = "content"
categories = [
    "commercial-et-clientele",
    "ressources-humaines",
    "poste-et-logistique",
    "telecommunications",
    "informatique-et-technologies",
    "administration-finance-et-juridique"
]

def extract_desc(body, summary):
    # Search for the context / description section in body
    match = re.search(r"## 📝 Description du poste & Contexte\s+(.*?)(?=\n##|$)", body, re.DOTALL)
    if match:
        desc = match.group(1).strip()
        # Remove markdown bold/italics or multiple line breaks
        desc = re.sub(r"\s+", " ", desc)
        if len(desc) > 30:
            return desc
    if summary:
        return summary
    return "Description non disponible."

print("✍️ Enrichissement des descriptions AVP...")

updated_count = 0

for category in categories:
    cat_dir = os.path.join(content_dir, category)
    if not os.path.exists(cat_dir):
        continue
    
    for filename in os.listdir(cat_dir):
        if not filename.endswith(".md") or filename == "_index.md":
            continue
            
        file_path = os.path.join(cat_dir, filename)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
            
        frontmatter = parts[1]
        body = parts[2]
        
        # Check if description field is already present
        desc_match = re.search(r"^description:\s*", frontmatter, re.MULTILINE)
        if desc_match:
            # Let's check if it has a non-empty value
            val_match = re.search(r"^description:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
            if val_match and len(val_match.group(1).strip()) > 10:
                # Description already exists and is valid
                continue
                
        # Get summary and extract a rich description
        summary_match = re.search(r"^summary:\s*\"?([^\n\"]+)\"?", frontmatter, re.MULTILINE)
        summary = summary_match.group(1).strip() if summary_match else None
        
        desc = extract_desc(body.strip(), summary)
        
        # Escape double quotes for YAML double-quoted string
        escaped_desc = desc.replace('"', '\\"')
        
        # Add description to frontmatter
        # We can clean up existing description line if it was empty/invalid
        if desc_match:
            # Remove existing description line
            frontmatter = re.sub(r"^description:.*?\n", "", frontmatter, flags=re.MULTILINE)
            
        # Append description before the end of frontmatter
        new_frontmatter = frontmatter.rstrip() + f'\ndescription: "{escaped_desc}"\n'
        
        new_content = f"---{new_frontmatter}---{body}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print(f"✅ {category}/{filename} : description ajoutée/enrichie")
        updated_count += 1

print(f"🎉 Terminé. {updated_count} fichiers AVP mis à jour avec une description riche.")
