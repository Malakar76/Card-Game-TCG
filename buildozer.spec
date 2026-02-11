[app]

title = Card Game TCG
package.name = cardgametcg
package.domain = org.cardgametcg

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,json
source.include_patterns = main.py,src/**/*.py,src/**/*.kv
source.exclude_dirs = tests,.venv,.git,.github,.ruff_cache,.pytest_cache,db/migrations,build,dist
source.exclude_patterns = buildozer.spec,pyproject.toml,alembic.ini,*.egg-info

version = 0.1.0

requirements = python3,kivy==2.3.0,sqlalchemy==2.0.36,pydantic==2.10.6,pydantic-settings,pydantic-core,annotated-types,typing-extensions,dotenv

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.archs = arm64-v8a
android.allow_backup = True
android.accept_sdk_license = True

# Blacklist the built-in sqlalchemy recipe (broken URL for 2.x) so pip installs it
p4a.extra_args = --recipe-blacklist=sqlalchemy

android.permissions = INTERNET

[buildozer]

log_level = 2
warn_on_root = 1
