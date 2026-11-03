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
- `gold` : `null` = pas encore annotée, `[]` = aucun concept ESCO n'a le même sens, sinon la liste des URI ESCO
  de même sens (`http://data.europa.eu/esco/skill/…` ou `…/occupation/…`), la plus pertinente en premier
- `acceptable` : alternatives défendables (quasi-synonyme ESCO, concept partiel ou le plus proche quand `gold`
  vaut `[]`) ; un pipeline qui les choisit ne commet pas d'erreur au score tolérant
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
Deux scores :

- **strict** : seul `gold` compte ;
- **tolérant** : un choix présent dans `acceptable` n'est pas compté comme une erreur (ni juste, ni faux).

## Guide d'annotation

1. On cherche dans **tout** ESCO, pas seulement parmi les candidates d'un pipeline.
2. On valide chaque concept sur sa **description** ESCO, pas seulement sur son libellé, et on écarte ceux
   propres à un autre domaine (ex. « répondre aux demandes des clients » est décrit pour le tourisme).
3. `gold` ne contient que des concepts de **même sens**. Un concept approximatif va dans `acceptable` ; si
   rien n'a le même sens, `gold` vaut `[]`, le plus proche va dans `acceptable` et `note` dit pourquoi.
4. **Un concept par savoir-faire distinct** (3 au plus). Un complément qui ne précise que le moyen ne compte
   pas : « écouter les besoins du client » est une seule idée (écouter activement).
5. **Connaissance ou savoir-faire** : on suit la formulation, pas le champ d'origine. « Techniques de… »,
   « Connaissance de… » → connaissance ESCO ; un verbe d'action → savoir-faire. L'autre forme va dans `acceptable`.
6. Entre quasi-doublons ESCO (« garantir la satisfaction des clients » / « satisfaire les clients »), le plus
   complet va dans `gold`, l'autre dans `acceptable`.
7. Les qualités personnelles (rigueur, autonomie, esprit d'équipe…) se relient aux compétences transversales
   ESCO, en distinguant la qualité personnelle (« travailler en équipe ») du rôle managérial
   (« construire un esprit d'équipe »).
8. Une partie de l'exigence sans équivalent ESCO est signalée dans `note`.

## Méthode et limites

Les annotations sont **proposées par un LLM (Claude) puis validées ou corrigées par un humain** connaissant
les métiers de l'OPT-NC. Un second annotateur, sans voir les réponses, reprendra une vingtaine de lignes du test
pour mesurer l'accord entre humains, qui donne le plafond réaliste des scores. Le jeu est petit (100 exigences, 30 AVP) : les écarts de quelques points entre deux
pipelines ne sont pas significatifs.
