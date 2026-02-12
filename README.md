# Card Game TCG

Application de jeu de cartes à collectionner (Trading Card Game) construite avec Python, SQLite et Kivy.

## Stack technique

- **Python** >= 3.12
- **SQLite** via [SQLAlchemy](https://www.sqlalchemy.org/) (ORM)
- **Alembic** pour les migrations de base de données
- **Pydantic** pour la validation des données
- **Kivy** pour l'interface graphique (desktop + Android via Buildozer)
- **EasyOCR** / **Google ML Kit** pour la reconnaissance de cartes (scan OCR)
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

## Scanner de cartes (OCR)

L'application intègre un scanner qui utilise la caméra pour identifier les cartes Pokémon :

- **Desktop** : [EasyOCR](https://github.com/JaidedAI/EasyOCR) (reconnaissance FR/EN), pytesseract en fallback
- **Android** : Google ML Kit (via pyjnius)

Le scanner capture une photo, extrait le texte par OCR, puis identifie le nom du Pokémon en filtrant les suffixes (EX, GX, VMAX, VSTAR, V, ex).

## Tests

```bash
uv run pytest
```

Pour exclure les tests lents (OCR sur image réelle) :

```bash
uv run pytest -m "not slow"
```

## Build Android (APK)

Le projet utilise [Buildozer](https://github.com/kivy/buildozer) pour compiler l'APK Android.

**En local :**

```bash
pip install buildozer cython
buildozer android debug
```

L'APK est généré dans `bin/`.

**Via GitHub Actions :**

Le workflow CD se lance manuellement depuis l'onglet Actions > CD > "Run workflow". Il build l'APK et l'uploade en artifact téléchargeable.

## Structure du projet

```
src/card_game_tcg/
├── main.py              # Point d'entrée applicatif
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
│   ├── card_service.py  # CRUD cartes
│   └── ocr_service.py   # Reconnaissance de texte (OCR multiplateforme)
└── ui/                  # Interface Kivy
    ├── app.py           # CardGameApp
    ├── screens/         # Écrans (Screen) : collection, recherche, scanner
    └── kv/              # Fichiers .kv (layout déclaratif)
main.py                  # Entry point Buildozer (racine)
buildozer.spec           # Configuration Buildozer (Android)
```
