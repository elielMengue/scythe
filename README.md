#  Artifact-Scythe

> Un outil CLI intelligent pour nettoyer automatiquement les artefacts de build

##  Qu'est-ce que c'est ?

Artifact-Scythe scanne vos répertoires de projets et détecte automatiquement les artefacts de build inutiles (node_modules, .venv, __pycache__, target/, etc.) pour libérer des dizaines de Go d'espace disque.

##  Fonctionnalités

-  Scan récursif de répertoires
-  Détection automatique de types de projets (Node, Python, Rust, Java, etc.)
-  Calcul d'espace occupé par les artefacts
-  Nettoyage sélectif ou global
-  Mode interactif avec confirmation
-  Rapport détaillé de nettoyage

##  Installation

### Depuis les sources

```bash
git clone https://github.com/elielMengue/scythe.git
cd artifact-scythe
pip install -e .
```

### Depuis PyPI (à venir)

```bash
pip install scythe
```

##  Usage

### Scan d'un répertoire

```bash
scythe scan ~/projects
```

### Nettoyage interactif

```bash
scythe clean ~/projects --interactive
```

### Mode dry-run (simulation)

```bash
scythe clean ~/projects --dry-run
```

### Afficher l'aide

```bash
scythe --help
```

##  Développement

### Prérequis

- Python 3.10+
- pip

### Configuration de l'environnement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Lancer les tests

```bash
pytest -v
```

##  Roadmap

- [x] Phase 1: Configuration & Fondations
- [x] Phase 2: Scanner de Répertoires
- [ ] Phase 3: Détection d'Artefacts
- [ ] Phase 4: Interface Utilisateur
- [ ] Phase 5: Moteur de Nettoyage
- [ ] Phase 6: Fonctionnalités Avancées
- [ ] Phase 7: Tests & Validation
- [ ] Phase 8: Documentation & Déploiement

##  Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.


## ⚠️ Status du Projet
**Version 0.2.0**
Cette version contient le feature scan.



---
[@elielMengue](https://github.com/elielMengue)




