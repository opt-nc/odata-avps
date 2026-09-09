---
title: "Les AVPs pour les développeurs"
description: "Intégrez les Avis de Vacance de Poste OPT-NC dans vos applications : API REST, serveur MCP pour agents IA, et open data."
archetype: "page"
disableNextPrev: true
hidden: true
---

### 🚀 Une API publique, trois façons de l'utiliser {#trois-usages}

Les données de cette plateforme sont **intégrables** dans vos applications, scripts,
tableaux de bord ou agents IA. Tout passe par le
[portail d'APIs de l'OPT-NC](https://apigee-optnc-prd-api.apigee.io/).

{{% notice style="primary" title="Obtenir votre clé, en trois étapes" icon="key" %}}
1. Créez un compte sur le portail, puis une *app* ;
2. Abonnez-la au produit **`avps`** — l'approbation est automatique ;
3. Récupérez votre clé API : champ « Key » dans les détails de votre app.
{{% /notice %}}

#### Pour vous aider {#demarrer}

{{< button href="https://dev.to/optnc/apigee-101-onboarding-authentication-1ghl" icon="fas fa-book-open" >}}Lire le guide complet{{< /button >}}
{{< button href="https://youtu.be/L56z2Vkht5E" icon="fab fa-youtube" >}}Voir la vidéo sur YouTube{{< /button >}}

L'onboarding APIGEE pas à pas, de la création du compte au premier appel authentifié :

{{< avp-video L56z2Vkht5E >}}

---

### 🔎 L'API REST de recherche {#api-rest}

Exemples avec [httpie](https://httpie.io/) (`brew install httpie` / `apt install httpie`) :

**Recherche sémantique** — décrivez le poste en langage naturel :

```bash
http POST https://api.opt.nc/avps/search \
  x-apikey:$API_KEY \
  prompt="Je suis spécialiste data. Trouve moi un poste adapté"
```

ou avec curl

```
curl --request POST \
  'https://api.opt.nc/avps/search' \
  --header 'x-apikey: [YOUR_API_KEY]' \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json' \
  --data '{"prompt":"Je suis spécialiste data. Trouve moi un poste adapté"}' \
  --compressed
```

**Filtres structurés** — commune, province et direction utilisent les référentiels
officiels (voir les valeurs admises dans la
[spécification OpenAPI](https://apigee-optnc-prd-api.apigee.io/)) :

```bash
http POST https://api.opt.nc/avps/search \
  x-apikey:$API_KEY \
  filters:='{"ville": "Nouméa", "province": "province Sud"}'
```

```bash
http POST https://api.opt.nc/avps/search \
  x-apikey:$API_KEY \
  filters:='{"direction": "DIRECTION DES SYSTEMES D'\''INFORMATION"}' \
  options:='{"top_k": 10}'
```

**Combinez les deux** — le prompt affine, les filtres bornent :

```bash
http POST https://api.opt.nc/avps/search \
  x-apikey:$API_KEY \
  prompt="management d'équipe" \
  filters:='{"province": "province Nord"}'
```

Chaque résultat contient la fiche complète au format
[Schema.org/JobPosting](https://schema.org/JobPosting) (`json_data`), plus les champs
de synthèse (`titre`, `ville`, `province`, `familles`, `direction`, `distance`).

---

### 🤖 Le serveur MCP pour les agents IA {#serveur-mcp}

Vos assistants (Claude, Gemini, agents maison…) peuvent interroger les AVPs
nativement via le protocole **MCP** (Model Context Protocol) :

- **Endpoint** : `https://api.opt.nc/mcp` (transport HTTP streamable)
- **Authentification** : header `x-apikey` (produit `mcp-emploi` sur le portail),
  ou OAuth 2.0 `client_credentials` via `POST /oauth/token`

Exemple de configuration pour Claude Code :

```bash
claude mcp add --transport http avp-opt https://api.opt.nc/mcp \
  --header "x-apikey: $API_KEY"
```

L'agent découvre alors les outils de recherche (`searchAvp`, référentiel métiers,
open data) et peut répondre à des questions comme *« quels postes sont ouverts en
province Nord ? »* en croisant plusieurs sources.

---

### 📊 La donnée brute (open data) {#open-data}

- **Dataset Hugging Face** : [opt-nc/odata-avps](https://huggingface.co/datasets/opt-nc/odata-avps)
  — le corpus consolidé (JSONL) et les embeddings (Parquet) des AVP actifs ;
- **Flux d'intégration emploi** : [sitemap dédié](../jobs-sitemap.xml) et JSON-LD
  `JobPosting` embarqué dans chaque page.

---

### 📬 Support {#support}

Une idée d'intégration, un besoin de quota supérieur, un bug ? Ouvrez une issue sur
[le dépôt du projet](https://github.com/opt-nc/odata-avps) ou contactez le support
via le portail d'APIs.
