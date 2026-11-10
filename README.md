# Cours IAM : gestion des identités et des accès

Site du cours IAM de Grégory Ruch : le cours, les exercices et le labo Keycloak.
Le site est écrit en Markdown et généré par [Quarto](https://quarto.org).

## Organisation

```
_quarto.yml        menus, barres latérales, thème : le seul fichier de configuration
_variables.yml     édition, adresse du dépôt, version de Keycloak
index.qmd          page d'accueil
cours/             un fichier par chapitre (01 à 10)
exercices/         les deux études de cas et les questions de révision
labo/              le guide du labo (pages du site)
labo/kit/          le kit du labo : docker compose, application, corrigé (pas publié sur le site)
glossaire.qmd      les sigles
sources.qmd        les références
images/            les schémas (SVG, modifiables avec Inkscape)
styles/            couleurs et mise en forme (theme.scss, theme-dark.scss)
```

## Travailler en local

1. Installer Quarto : <https://quarto.org/docs/get-started/>
2. Dans ce dossier : `quarto preview`

Le site s'ouvre dans le navigateur et se recharge à chaque enregistrement.

## Modifier le contenu

- **Corriger un texte** : ouvrir le `.qmd` concerné, c'est du Markdown.
- **Ajouter un chapitre** : créer le fichier dans `cours/`, puis l'ajouter à la liste `sidebar` de
  `_quarto.yml`.
- **Nouvelle édition** : changer `edition` dans `_variables.yml`.

Les blocs de mise en forme utilisés dans les pages :

| Bloc | Rendu |
|---|---|
| `::: {.callout-important title="À retenir"}` | Encadré du message clé |
| `::: {.callout-tip title="Exemple"}` | Encadré d'exemple |
| `::: {.cartes}` contenant des `::: {.carte}` | Grille de cartes (`.cartes .deux` pour deux colonnes) |
| `::: {.etapes}` autour d'une liste numérotée | Étapes avec pastilles |
| `::: {.question}` | Question d'exercice ou de labo |
| `::: {.question-du-chapitre}` | Accroche en tête de chapitre |
| `[Faible]{.niveau .faible}` | Pastille de niveau (`.faible`, `.moyen`, `.resistant`) |

## Branches et publication

- `dev` : la branche de travail. Rien n'est publié.
- `main` : la version en ligne. Chaque fusion dans `main` republie le site.
- `gh-pages` : le site généré. Ne jamais la modifier à la main.

Une demande de fusion (pull request) de `dev` vers `main` déclenche une compilation de contrôle.
La fusion déclenche la publication. Tout est dans `.github/workflows/publier.yml`.

```bash
git checkout dev
# ... modifications ...
git add -A && git commit -m "Corrige le chapitre 5"
git push
# puis, sur GitHub : pull request de dev vers main, et fusion
```
