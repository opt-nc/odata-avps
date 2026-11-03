# Jeu de référence AVP ↔ ESCO

Annotations faites à la main pour **mesurer** la qualité du rapprochement automatique des AVP de l'OPT-NC
avec le référentiel européen [ESCO v1.2.1](https://esco.ec.europa.eu/fr) (professions et compétences),
et comparer des pipelines ou des LLM entre eux sur les mêmes données.

> 🚧 Annotation en cours : `"gold": null` signale une ligne pas encore annotée.

## Fichiers

| Fichier | Contenu |
|---|---|
| `skills.jsonl` | 100 exigences (`skills`, `competencyRequired`) → compétences ESCO |
| `occupations.jsonl` | 30 AVP → professions ESCO |

Champs communs :

- `id` : identifiant stable de la ligne (`s001`…, `o001`…)
- `split` : `dev` (30 %) ou `test` (70 %), voir plus bas
- `gold` : `null` = pas encore annotée, `[]` = aucun concept ESCO ne convient, sinon la liste des URI ESCO
  retenues (`http://data.europa.eu/esco/skill/…` ou `…/occupation/…`), la plus pertinente en premier
- `note` : remarque libre de l'annotateur (cas limite, hésitation…)

## Échantillon

Tiré au hasard (graine fixe) parmi les 70 AVP du run du 2026-10-09 :

- **exigences** : 20 restées sans compétence ESCO lors de ce run (là où un meilleur rappel peut aider),
  80 autres réparties au prorata des champs `skills` et `competencyRequired`. Les variantes d'écriture
  (« Être rigoureux » / « Etre rigoureux ») sont fusionnées ;
- **AVP** : au moins un par direction, le reste au hasard.

Les choix du modèle ne figurent pas dans les fichiers, pour ne pas orienter l'annotation.

## Utilisation : dev et test

- **dev** : on peut regarder les erreurs d'un pipeline et ajuster ses réglages.
- **test** : réservé aux comparaisons finales. On n'ajuste jamais un prompt, un seuil ou un paramètre en
  regardant les erreurs sur ces lignes, sinon les scores ne veulent plus rien dire.
- Aucune ligne de ce jeu ne doit servir d'exemple dans un prompt.

Mesures prévues : précision, rappel et F1 sur les URI ESCO, taux de réponses valides, et rappel@k de
l'étape de présélection (la bonne compétence figure-t-elle parmi les candidates soumises au LLM ?).

## Guide d'annotation

À compléter au fil des premiers lots, à partir des cas difficiles.

1. On cherche dans **tout** ESCO, pas seulement parmi les candidates d'un pipeline.
2. Un lien n'est valable que si le **sens** est le même, pas seulement les mots.
3. Une exigence qui énumère plusieurs savoir-faire distincts reçoit une compétence par élément (3 au plus).
4. Les qualités personnelles (rigueur, autonomie…) se relient aux compétences transversales ESCO.
5. Si rien ne convient (outil interne, connaissance propre à l'OPT-NC…), `gold` vaut `[]` et `note` dit pourquoi.

## Méthode et limites

Les annotations sont **proposées par un LLM (Claude) puis validées ou corrigées par un humain** connaissant
les métiers de l'OPT-NC. Le jeu est petit (100 exigences, 30 AVP) : les écarts de quelques points entre deux
pipelines ne sont pas significatifs.
