# Card Game TCG

Application de jeu de cartes à collectionner (Trading Card Game) construite avec Python, SQLite et Kivy.

## Stack technique

- **Python** >= 3.12
- **SQLite** via [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
- **Alembic** pour les migrations de base de données
- **Pydantic** pour la validation des données
- **Kivy** pour l'interface graphique (desktop + Android via Buildozer)
- **uv** pour la gestion des dépendances

## Prérequis

- Python 3.12+
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

| Variable       | Défaut                              | Description                  |
|----------------|-------------------------------------|------------------------------|
| `TCG_DB_PATH`  | `~/.card_game_tcg/card_game_tcg.db` | Chemin du fichier SQLite     |
| `TCG_DEBUG`    | `false`                             | Mode debug                   |

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
│   ├── session.py       # Engine SQLite, SessionLocal, init_db()
│   └── migrations/      # Alembic (migrations de schéma)
├── models/              # Modèles SQLAlchemy
│   ├── base.py          # BaseModel (soft delete, timestamps)
│   └── card.py          # Modèle Card
├── schemas/             # Schémas Pydantic (validation)
│   └── card.py          # CardCreate, CardRead
├── services/            # Logique métier
│   └── card_service.py
└── ui/                  # Interface Kivy
    ├── app.py           # CardGameApp
    ├── screens/         # Écrans (Screen)
    └── kv/              # Fichiers .kv (layout déclaratif)
```
