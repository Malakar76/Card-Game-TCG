# Card Game TCG

Application de jeu de cartes à collectionner (Trading Card Game) construite avec Python, MongoDB et Qt.

## Stack technique

- **Python** >= 3.12
- **MongoDB** via [Motor](https://motor.readthedocs.io/) (driver async)
- **Beanie** + **Pydantic** pour l'ODM (Object-Document Mapper)
- **PySide6** (Qt 6) pour l'interface graphique
- **uv** pour la gestion des dépendances

## Prérequis

- Python 3.12+
- MongoDB en cours d'exécution sur `localhost:27017` (ou configurer `TCG_MONGO_URI`)
- [uv](https://docs.astral.sh/uv/) installé

## Installation

```bash
# Installer les dépendances
uv sync

# Installer aussi les dépendances de développement
uv sync --group dev
```

## Lancement

```bash
uv run card-game-tcg
```

## Configuration

L'application se configure via des variables d'environnement préfixées par `TCG_` :

| Variable            | Défaut                        | Description              |
|---------------------|-------------------------------|--------------------------|
| `TCG_MONGO_URI`     | `mongodb://localhost:27017`   | URI de connexion MongoDB |
| `TCG_MONGO_DB_NAME` | `card_game_tcg`               | Nom de la base de données|
| `TCG_DEBUG`         | `false`                       | Mode debug               |

Vous pouvez aussi créer un fichier `.env` à la racine du projet.

## Tests

```bash
uv run pytest
```

## Structure du projet

```
src/card_game_tcg/
├── main.py              # Point d'entrée
├── config.py            # Configuration (pydantic-settings)
├── db/
│   └── connection.py    # Connexion MongoDB / init Beanie
├── models/              # Documents Beanie (modèles de données)
│   └── card.py
├── services/            # Logique métier
│   └── card_service.py
└── ui/                  # Interface Qt
    ├── app.py           # Setup QApplication
    └── windows/
        └── main_window.py
```
