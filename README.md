[![Dataset](https://img.shields.io/badge/🤗%20HuggingFace-odata--avps-FFD21E?logo=huggingface&logoColor=000&style=for-the-badge)](https://huggingface.co/datasets/opt-nc/odata-avps)
[![Open Data](https://img.shields.io/badge/🌏%20data.gouv.nc-AVP%20DRHFPNC-0072BC?style=for-the-badge)](https://data.gouv.nc/explore/dataset/avis-de-vacances-de-poste-avp-drhfpnc)


# odata-avps — Bourse d'emploi OPT-NC (site)

Site **statique** publiant les Avis de Vacance de Poste (AVP) de l'**OPT-NC**, à partir du jeu
Open Data [`avis-de-vacances-de-poste-avp-drhfpnc`](https://data.gouv.nc/explore/dataset/avis-de-vacances-de-poste-avp-drhfpnc).

Le contenu (`content/`, `data/avps/`, bannières) est **généré et poussé automatiquement** par le pipeline
GCP [`gcp-avp-cloudfunctions`](../gcp-avp-cloudfunctions). Ce dépôt ne contient que la couche de **présentation**.

## 🧱 Stack

- **[Hugo](https://gohugo.io/)** (extended) + thème **[relearn](https://github.com/McShelby/hugo-theme-relearn)** (sous-module Git).
- Déploiement **GitHub Pages** via [`.github/workflows/deploy_site.yaml`](.github/workflows/deploy_site.yaml).
- Sorties additionnelles : **JSON-LD JobPosting** (Google for Jobs), **flux ATS** (`flux_ats.xml`),
  **jobs-sitemap** (`jobs-sitemap.xml`) et bundle **OKF** (`static/okf/`).

## 📂 Structure

| Dossier | Rôle |
|---|---|
| `content/<famille>/` | Fiches AVP en Markdown (générées) + `_index.md` par famille de métiers |
| `content/mot-drh/` | « Le mot de la DRH » (généré par le consolidateur) |
| `data/avps/*.json` | Schéma JSON-LD par AVP (source du JSON-LD + des flux) |
| `layouts/` | Shortcodes (`avp-header`, `avp-map`, `list-avps`), partials SEO, sorties XML |
| `assets/css/` | Thèmes `opt-light` / `opt-dark` + `avp-components.css` |
| `static/vendor/` | Leaflet & easyqrcode **auto-hébergés** (aucune dépendance CDN) |
| `scripts/` | Outils de build : enrichissement descriptions, bundle OKF, validateur OKF |

## 🚀 Développement local

```bash
# 1. Cloner avec le sous-module du thème
git clone --recurse-submodules <repo>
# (ou, si déjà cloné) : git submodule update --init --recursive

# 2. Scripts de pré-build (comme en CI)
mkdir -p data && echo "hash: dev" > data/git_commit.yaml
python3 scripts/enrich_descriptions.py
python3 scripts/generate_okf_bundle.py

# 3. Servir le site
hugo server -D

# 4. (optionnel) Vérifier la conformité OKF des fiches
python3 scripts/validate_okf.py
```

> ℹ️ Les libs JS (Leaflet, easyqrcode) sont versionnées dans `static/vendor/`.
> Pour les mettre à jour, remplacer les fichiers correspondants (voir leurs versions dans les commentaires des shortcodes).
