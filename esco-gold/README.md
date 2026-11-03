# Jeu de référence AVP ↔ ESCO

Annotations faites à la main pour **mesurer** la qualité du rapprochement automatique des AVP de l'OPT-NC
avec le référentiel européen [ESCO v1.2.1](https://esco.ec.europa.eu/fr) (professions et compétences),
et comparer des pipelines ou des LLM entre eux sur les mêmes données.

> Version 1 : annotation terminée (100 exigences, 70 AVP).

## Fichiers

| Fichier | Contenu |
|---|---|
| `skills.jsonl` | 100 exigences (`skills`, `competencyRequired`) → compétences ESCO |
| `occupations.jsonl` | 70 AVP → professions ESCO (la totalité du run) |
| `annotator2.jsonl` | passe indépendante d'un second annotateur sur 20 lignes du test (accord inter-annotateurs) |

Champs communs :

- `id` : identifiant stable de la ligne (`s001`…, `o001`…)
- `split` : `dev` (30 %) ou `test` (70 %), voir plus bas
- `gold` : `null` = pas encore annotée, `[]` = aucun concept ESCO n'a le même sens, sinon la liste des URI ESCO
  de même sens (`http://data.europa.eu/esco/skill/…` ou `…/occupation/…`), la plus pertinente en premier
- `acceptable` : alternatives défendables (quasi-synonyme ESCO, concept partiel ou le plus proche quand `gold`
  vaut `[]`) ; un pipeline qui les choisit ne commet pas d'erreur au score tolérant
- `gap` : ce qu'ESCO ne couvre pas, que `gold` soit vide ou ne couvre qu'une partie de l'exigence ; `null` si
  l'exigence est entièrement couverte
  - `opt` : connaissance ou valeur propre à l'OPT-NC ou à la Nouvelle-Calédonie
  - `outil` : outil ou technologie absent d'ESCO
  - `esco` : compétence générale qu'ESCO ne couvre pas
  - `vague` : exigence trop floue pour être reliée à un concept
- `note` : remarque libre de l'annotateur (cas limite, hésitation…)

## Échantillon

Tiré au hasard (graine fixe) parmi les 70 AVP du run du 2026-10-09 :

- **exigences** : 20 restées sans compétence ESCO lors de ce run (là où un meilleur rappel peut aider),
  80 autres réparties au prorata des champs `skills` et `competencyRequired`. Les variantes d'écriture
  (« Être rigoureux » / « Etre rigoureux ») sont fusionnées ;
- **AVP** : d'abord 30 (au moins un par direction, le reste au hasard), puis extension aux 40 restants
  (o031-o070, mêmes règles, découpage dev/test au même ratio) : les 70 AVP du run sont couverts.

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
   pas : « écouter les besoins du client » est une seule idée (écouter activement). Exception : une
   énumération explicite d'outils ou de langages reçoit un concept par élément présent dans ESCO, sans limite.
5. **Connaissance ou savoir-faire** : on suit la formulation, pas le champ d'origine. « Techniques de… »,
   « Connaissance de… » → connaissance ESCO ; un verbe d'action → savoir-faire. L'autre forme va dans `acceptable`.
6. Entre quasi-doublons ESCO (« garantir la satisfaction des clients » / « satisfaire les clients »), le plus
   complet va dans `gold`, l'autre dans `acceptable`.
7. Les qualités personnelles (rigueur, autonomie, esprit d'équipe…) se relient aux compétences transversales
   ESCO, en distinguant la qualité personnelle (« travailler en équipe ») du rôle managérial
   (« construire un esprit d'équipe »).
8. Une partie de l'exigence sans équivalent ESCO est signalée dans `note`.
9. « Maîtrise de… » est ambigu (connaissance ou savoir-faire) : on tranche selon la description ESCO, l'autre
   forme va dans `acceptable`.
10. **Relationnel** : ESCO n'a pas de concept général. Si l'exigence précise le public (« avec le public et le
    personnel »), un concept de communication par public ; sinon `gold` vaut `[]`, les concepts proches vont
    dans `acceptable`.
11. **Professions** : `gold` contient la profession ESCO qui correspond au poste, la plus précise possible (2 au plus
    si le poste combine réellement deux métiers) ; une profession voisine (niveau hiérarchique au-dessus ou en
    dessous, domaine proche) va dans `acceptable`, y compris pour un poste junior de la même fonction.

## Méthode et limites

Les annotations sont **proposées par un LLM (Claude) puis validées ou corrigées par un humain** connaissant
les métiers de l'OPT-NC. Un second annotateur, sans voir les réponses, reprendra une vingtaine de lignes du test
pour mesurer l'accord entre annotateurs, qui donne le plafond réaliste des scores. Les lots o031-o070 ont été
annotés par un second LLM (Claude Fable) avec relecture humaine.

**Accord inter-annotateurs** : un second annotateur (Claude Fable, sans voir les réponses du premier) a repris
20 lignes du test (15 exigences + 5 AVP, graine 42, fichier `annotator2.jsonl`) : accord strict (mêmes `gold`)
14/20, accord tolérant (via `acceptable`) 19/20. Le seul désaccord (s088) est un rappel manqué du second
annotateur. Les scores strict d'un pipeline au-delà de ~70 % ne sont donc pas interprétables.

Le jeu est petit (100 exigences, 70 AVP) :
les écarts de quelques points entre deux pipelines ne sont pas significatifs.
