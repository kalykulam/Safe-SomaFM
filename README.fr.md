# Safe SomaFM pour Home Assistant

Safe SomaFM est une intégration personnalisée Home Assistant pensée pour écouter les radios [SomaFM](https://somafm.com/) depuis Home Assistant avec une approche prudente et défensive.

Elle fournit :

- un lecteur local dans Home Assistant ;
- une carte Lovelace compacte pour le dashboard ;
- un lanceur dans la barre latérale qui ouvre le lecteur complet dans un nouvel onglet ;
- les images des stations, descriptions, genres, auditeurs, DJ et informations “now playing” quand SomaFM les fournit ;
- le choix de qualité / débit ;
- une logique de reconnexion automatique pour les longues écoutes.

Version actuelle : **v0.8.4**

Documentation anglaise : [README.md](README.md)

---

## Pourquoi cette intégration existe

Le Media Browser standard de Home Assistant peut transmettre le flux directement au navigateur. Pendant les tests, certains navigateurs coupaient les flux SomaFM après plusieurs minutes.

Safe SomaFM utilise donc une page de lecture locale dans Home Assistant avec une logique de reconnexion automatique. Le lecteur complet a été testé avec succès sur de longues durées d’écoute.

---

## Fonctionnalités

### Lecteur local complet

Le lecteur complet est accessible ici :

```text
/safe_somafm/player
```

Il affiche :

- les images des stations ;
- une grille de stations avec recherche ;
- les métadonnées des stations ;
- le choix de qualité / débit ;
- les boutons lecture et arrêt ;
- l’état de reconnexion automatique.

### Mode dashboard compact

La carte Lovelace utilise le mode compact :

```text
/safe_somafm/player?compact=1
```

Ce mode est adapté aux colonnes de dashboard et utilise des images de stations plus petites.

### Lanceur dans la barre latérale

L’intégration ajoute une entrée **Safe SomaFM** dans la barre latérale gauche de Home Assistant.

Quand tu cliques dessus, Home Assistant tente d’ouvrir le lecteur complet dans un **nouvel onglet**.

Si le navigateur bloque l’ouverture automatique, une petite page de secours s’affiche avec un bouton **Open Safe SomaFM**.

### Carte Lovelace

L’intégration fournit une ressource locale :

```text
/safe_somafm/card.js
```

Ajoute-la comme ressource de dashboard Home Assistant :

```text
Module JavaScript
```

Puis ajoute une carte :

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 320px
```

Version un peu plus grande :

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 420px
show_header: true
```

---

## Installation

### Installation manuelle

1. Copie ce dossier :

```text
custom_components/safe_somafm/
```

dans le dossier de configuration Home Assistant :

```text
/config/custom_components/safe_somafm/
```

2. Redémarre complètement Home Assistant.
3. Va dans **Paramètres → Appareils et services → Ajouter une intégration**.
4. Cherche **Safe SomaFM**.
5. Ajoute l’intégration.

### Mise à jour

Pour une mise à jour manuelle :

1. Arrête ou redémarre Home Assistant.
2. Supprime l’ancien dossier :

```text
/config/custom_components/safe_somafm/
```

3. Copie le nouveau dossier `safe_somafm`.
4. Redémarre Home Assistant.
5. Recharge le navigateur avec `Ctrl + F5`.

---

## Configuration du dashboard

### Ajouter la ressource de carte

Dans Home Assistant :

1. Ouvre un dashboard.
2. Clique sur **Modifier le tableau de bord**.
3. Ouvre le menu en haut à droite.
4. Va dans **Ressources**.
5. Ajoute :

```text
/safe_somafm/card.js
```

Type de ressource :

```text
Module JavaScript
```

### Ajouter la carte

```yaml
type: custom:safe-somafm-card
title: Safe SomaFM
height: 320px
```

---

## Sécurité

Safe SomaFM est volontairement limitée :

- pas d’identifiants utilisateur ;
- pas de secrets ;
- pas de dépendances Python externes ;
- pas d’exécution shell ;
- pas d’import dynamique ;
- pas de proxy arbitraire ;
- pas d’entrée utilisateur pour une URL de flux arbitraire ;
- les identifiants de stations sont validés ;
- les URL de playlists et d’images sont validées comme URL SomaFM ;
- les endpoints de lecture sont des endpoints locaux Home Assistant.

Le lanceur de la barre latérale ouvre uniquement :

```text
/safe_somafm/player
```

Il n’accepte pas d’URL externe.

Plus de détails sont disponibles dans [SECURITY_REVIEW.md](SECURITY_REVIEW.md).

---

## Fichiers

```text
custom_components/safe_somafm/
├── __init__.py
├── card.py
├── config_flow.py
├── const.py
├── manifest.json
├── media_source.py
├── panel.py
├── player.py
├── somafm.py
├── strings.json
└── brand/
```

---

## Notes

Safe SomaFM n’est pas affiliée à SomaFM ni à Home Assistant.

Les noms SomaFM, les noms des stations et les images des stations appartiennent à SomaFM. L’icône de l’intégration Safe SomaFM est originale et n’utilise pas les logos officiels SomaFM ou Home Assistant.


## v0.8.4 correction de l’index des stations

Cette version rétablit l’affichage de l’index/la grille des stations sur la page complète, tout en gardant la carte Lovelace compacte.

- `/safe_somafm/player` conserve la grille complète des stations.
- `/safe_somafm/player?compact=1` conserve l’affichage compact pour le dashboard.
- La logique de lecture et de reconnexion n’est pas modifiée.


## Page index GitHub Pages

Ce dépôt contient une page `index.html` simple pour GitHub Pages.

Elle renvoie vers :

- le README anglais ;
- le README français ;
- la revue de sécurité.

L’intégration Home Assistant ne dépend pas de ce fichier. Il sert uniquement pour la page du projet GitHub.
