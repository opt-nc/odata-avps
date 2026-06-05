---
title: "À propos de la plateforme"
description: "Démarche de production automatisée des fiches d'offres OPT-NC."
archetype: "page"
disableNextPrev: true # Evite que les flèches de navigation cyclent sur cette page
---

### 🏛️ La démarche de production

Cette plateforme a été conçue pour moderniser et fluidifier l'accès aux Avis de Vacances de Postes (AVP) de l'**Office des Postes et Télécommunications de Nouvelle-Calédonie**. 

Le processus de publication est entièrement automatisé et s'articule autour de trois piliers technologiques :

1. **Extraction de la Donnée (IA Générative) :** Les documents administratifs bruts au format PDF sont analysés par un agent d'intelligence artificielle (propulsé par Gemini). Il structure les données essentielles (références, dates de clôture, critères requis) au format JSON/Markdown sans aucune intervention humaine.
2. **Identité Visuelle Synchrone :** Les illustrations bannières thématiques intégrées à chaque offre sont générées à la volée par les algorithmes de **Nanobanana**, garantissant une charte graphique unique et moderne pour chaque métier.
3. **Performance Statique :** Le site est compilé via **Hugo**, offrant une rapidité de chargement instantanée, une sécurité maximale et une empreinte carbone minimale. Les images sont automatiquement converties au format nouvelle génération `WebP`.

---

### 🛠️ Informations de build (Suivi technique)

Pour garantir la traçabilité de l'application, les indicateurs de révision système sont injectés à chaque déploiement :

* **Révision du code source (Git) :** `r-{{ readFile "data/git_commit.txt" | default "version-dev" | strings.TrimSpace }}`
* **Moteur de rendu :** Hugo `v{{ hugo.Version }}`
* **Dernière synchronisation :** En production le {{ hugo.BuildDate.Format "02/01/2006 à 15:04:05" }}